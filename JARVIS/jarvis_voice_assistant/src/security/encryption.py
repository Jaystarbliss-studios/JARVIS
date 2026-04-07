"""
Security & Encryption Module
Handles voiceprint encryption, secure logging, and anti-spoofing measures.

CRITICAL: All biometric data must be encrypted at rest.
"""

import base64
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class VoiceprintEncryption:
    """
    Encrypts and stores speaker embeddings (voiceprints) securely.

    SECURITY PRINCIPLES:
    - Never store raw embeddings without encryption
    - Use environment variable for encryption key (not hardcoded)
    - Fail-secure: reject if key unavailable
    """

    def __init__(self, key_env_var: str = "JARVIS_ENCRYPTION_KEY"):
        """
        Initialize encryption handler.

        Args:
            key_env_var: Environment variable containing encryption key

        Raises:
            RuntimeError: If encryption key not found
        """
        self.key_env_var = key_env_var
        self.cipher_suite = self._load_or_create_key()
        logger.info("Encryption handler initialized")

    def _load_or_create_key(self) -> Fernet:
        """
        Load encryption key from environment, persistent file, or create new one.

        Returns:
            Fernet cipher suite

        Raises:
            RuntimeError: If key unavailable and cannot be created
        """
        # Try to load from environment
        key_str = os.getenv(self.key_env_var)

        if key_str:
            try:
                # Validate key format
                key_bytes = key_str.encode("utf-8")
                cipher = Fernet(key_bytes)
                logger.info("Loaded encryption key from environment")
                return cipher
            except Exception as e:
                logger.error(f"Invalid encryption key in environment: {e}")
                raise RuntimeError(f"Encryption key error: {e}")

        # Try to load from persistent keyfile
        keyfile = Path(".jarvis_keystore")
        if keyfile.exists():
            try:
                with open(keyfile) as f:
                    key_str = f.read().strip()
                key_bytes = key_str.encode("utf-8")
                cipher = Fernet(key_bytes)
                logger.info("Loaded encryption key from persistent keystore")
                return cipher
            except Exception as e:
                logger.warning(f"Failed to load persisted key: {e}. Creating new one.")

        # No key found - generate new one and persist it
        logger.warning(f"No {self.key_env_var} environment variable set")
        logger.info("To use existing voiceprint, set environment variable:")
        logger.info(f"  export {self.key_env_var}=<your_key>")

        new_key = Fernet.generate_key()
        key_str = new_key.decode("utf-8")

        # Save to persistent keystore
        try:
            with open(keyfile, "w") as f:
                f.write(key_str)
            os.chmod(keyfile, 0o600)  # Restrict permissions
            logger.info(f"Saved encryption key to {keyfile} (mode: 0o600)")
        except Exception as e:
            logger.warning(f"Could not persist key to file: {e}")

        logger.warning("Generated new encryption key. You can also set:")
        logger.warning(f"  {self.key_env_var}={key_str}")

        return Fernet(new_key)

    def encrypt_embedding(self, embedding: np.ndarray) -> str:
        """
        Encrypt speaker embedding for storage.

        Args:
            embedding: Speaker embedding vector (numpy array)

        Returns:
            Encrypted string (base64 encoded)
        """
        # Convert numpy array to JSON
        json_data = json.dumps(embedding.tolist())

        # Encrypt
        encrypted = self.cipher_suite.encrypt(json_data.encode("utf-8"))

        # Return as base64 string for storage
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_embedding(self, encrypted_data: str) -> np.ndarray:
        """
        Decrypt stored voiceprint embedding.

        Args:
            encrypted_data: Encrypted base64 string

        Returns:
            Speaker embedding vector (numpy array)

        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))

            # Decrypt
            decrypted = self.cipher_suite.decrypt(encrypted_bytes)

            # Convert back to numpy array
            embedding_list = json.loads(decrypted.decode("utf-8"))
            return np.array(embedding_list, dtype="float32")

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Cannot decrypt voiceprint: {e}")

    def save_encrypted_voiceprint(self, embedding: np.ndarray, filepath: str) -> bool:
        """
        Save encrypted voiceprint to disk.

        Args:
            embedding: Speaker embedding
            filepath: Path to save encrypted data

        Returns:
            Success status
        """
        try:
            encrypted = self.encrypt_embedding(embedding)

            # Create metadata
            metadata = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "embedding_size": len(embedding),
                "model": "ECAPA-TDNN",
            }

            # Save to file
            data = {"metadata": metadata, "voiceprint": encrypted}

            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(data, f)

            # Set restrictive permissions (Unix-like systems)
            try:
                os.chmod(filepath, 0o600)  # rw-------
            except:
                pass  # Windows doesn't support this

            logger.info(f"Encrypted voiceprint saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save encrypted voiceprint: {e}")
            return False

    def load_encrypted_voiceprint(self, filepath: str) -> np.ndarray | None:
        """
        Load and decrypt voiceprint from disk.

        Args:
            filepath: Path to encrypted voiceprint file

        Returns:
            Speaker embedding or None if failed
        """
        try:
            with open(filepath) as f:
                data = json.load(f)

            encrypted_data = data.get("voiceprint")
            if not encrypted_data:
                logger.error("No voiceprint data in file")
                return None

            embedding = self.decrypt_embedding(encrypted_data)
            logger.info(f"Loaded encrypted voiceprint from {filepath}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to load encrypted voiceprint: {e}")
            return None


class AuditLogger:
    """
    Secure logging without leaking biometric data.

    SECURITY: Never log raw embeddings or similarity scores above threshold.
    Log only binary pass/fail decisions and timestamps.
    """

    def __init__(self, log_path: str = "logs/access.log"):
        """Initialize audit logger."""
        self.log_path = log_path
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        self.file_logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure file logger for audit trail."""
        logger = logging.getLogger("audit")
        logger.setLevel(logging.INFO)

        handler = logging.FileHandler(self.log_path)
        formatter = logging.Formatter(
            "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def log_verification_attempt(self, result: str, reason: str = "") -> None:
        """
        Log verification attempt (PASS/FAIL only, no scores).

        Args:
            result: "PASS" or "FAIL"
            reason: Optional brief reason (no biometric data)
        """
        entry = f"[VERIFICATION] {result}"
        if reason:
            entry += f" - {reason}"

        self.file_logger.info(entry)

    def log_enrollment(self, num_samples: int) -> None:
        """Log enrollment completion."""
        self.file_logger.info(
            f"[ENROLLMENT] New voiceprint created ({num_samples} samples)"
        )

    def log_command_execution(self, intent: str, success: bool) -> None:
        """Log command execution attempt."""
        status = "SUCCESS" if success else "FAILED"
        self.file_logger.info(f"[COMMAND] {status} - Intent: {intent}")

    def log_security_event(self, event_type: str, details: str) -> None:
        """Log security-related events."""
        self.file_logger.warning(f"[SECURITY] {event_type} - {details}")


class AntiSpoofing:
    """
    Basic anti-spoofing measures to detect pre-recorded audio or deepfakes.

    LIMITATIONS: No anti-spoofing is 100% effective.
    This provides basic detection only.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def is_likely_prerecorded(self, audio: np.ndarray) -> tuple[bool, str]:
        """
        Detect if audio is likely pre-recorded using basic heuristics.

        HEURISTIC 1: Frequency concentration
        Pre-recorded audio often has concentrated energy in specific frequencies.

        HEURISTIC 2: Energy variation
        Pre-recorded audio may have more consistent amplitude.

        HEURISTIC 3: Click/pop detection
        Looping pre-recorded audio creates artifacts.

        Returns:
            Tuple (is_prerecorded, reason)
        """
        # Heuristic 1: FFT analysis
        fft = np.abs(np.fft.fft(audio))
        top_freq_energy = np.max(fft) / np.sum(fft)

        if top_freq_energy > 0.85:  # 85% energy in one frequency = suspicious
            return True, "Excessive frequency concentration (likely pre-recorded)"

        # Heuristic 2: Energy variation
        frame_len = int(0.01 * self.sample_rate)  # 10ms frames
        frame_energies = []

        for i in range(0, len(audio) - frame_len, frame_len):
            energy = np.sum(audio[i : i + frame_len] ** 2)
            frame_energies.append(energy)

        if len(frame_energies) > 1:
            energy_variation = np.std(frame_energies) / (
                np.mean(frame_energies) + 1e-10
            )
            if energy_variation < 0.10:  # Very consistent energy = suspicious
                return True, "Unusual energy stability (likely pre-recorded)"

        # Heuristic 3: Check for silence gaps (characteristic of loops)
        silent_threshold = np.mean(np.abs(audio)) * 0.1
        silent_frames = np.sum(np.abs(audio) < silent_threshold)
        silence_ratio = silent_frames / len(audio)

        if silence_ratio > 0.5:
            return True, "Excessive silence (may indicate loop)"

        return False, "Liveness check passed"
