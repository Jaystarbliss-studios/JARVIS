"""
Unit Tests for JARVIS Components
Run with: python -m pytest tests/
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio.capture import AudioCapture
from src.command.executor import CommandExecutor, CommandParser
from src.security.encryption import AuditLogger, VoiceprintEncryption
from src.verification.verify import SpeakerVerifier

# Fixtures


@pytest.fixture
def sample_audio():
    """Generate synthetic audio for testing."""
    sample_rate = 16000
    duration = 3.0
    frequency = 440  # A4 note
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.5 * np.sin(2 * np.pi * frequency * t).astype("float32")
    return audio


@pytest.fixture
def audio_capturer():
    """Create AudioCapture instance."""
    return AudioCapture(sample_rate=16000, channels=1)


@pytest.fixture
def verifier():
    """Create SpeakerVerifier instance (may fail if model not available)."""
    try:
        return SpeakerVerifier(threshold=0.70)
    except RuntimeError:
        pytest.skip("SpeakerVerifier model not available")


@pytest.fixture
def encryptor():
    """Create encryption instance with temp key."""
    import os

    from cryptography.fernet import Fernet

    # Set temp encryption key
    key = Fernet.generate_key()
    os.environ["JARVIS_ENCRYPTION_KEY"] = key.decode()

    return VoiceprintEncryption()


# Audio Tests


def test_audio_normalize(audio_capturer, sample_audio):
    """Test audio normalization."""
    normalized = audio_capturer.normalize_audio(sample_audio * 10)
    assert np.max(np.abs(normalized)) <= 1.0
    assert normalized.dtype == np.float32


def test_audio_validate_good(audio_capturer, sample_audio):
    """Test validation of good audio."""
    is_valid, reason = audio_capturer.validate_audio(sample_audio)
    assert is_valid == True


def test_audio_validate_empty(audio_capturer):
    """Test validation of empty audio."""
    is_valid, reason = audio_capturer.validate_audio(np.array([]))
    assert is_valid == False


def test_audio_validate_silent(audio_capturer):
    """Test validation of silent audio."""
    silent = np.zeros(16000, dtype="float32")
    is_valid, reason = audio_capturer.validate_audio(silent)
    assert is_valid == False


def test_audio_preemphasis(audio_capturer, sample_audio):
    """Test preemphasis filter."""
    filtered = audio_capturer.apply_preemphasis(sample_audio)
    assert filtered.shape == sample_audio.shape
    assert filtered.dtype == np.float32


# Verification Tests


@pytest.mark.skipif(not Path("models").exists(), reason="Models not downloaded")
def test_embedding_extraction(verifier, sample_audio):
    """Test embedding extraction."""
    embedding = verifier.extract_embedding(sample_audio)
    assert embedding is not None
    assert embedding.shape == (512,)  # ECAPA-TDNN output
    assert np.isfinite(embedding).all()


@pytest.mark.skipif(not Path("models").exists(), reason="Models not downloaded")
def test_cosine_similarity(verifier):
    """Test cosine similarity computation."""
    emb1 = np.random.randn(512).astype("float32")
    emb2 = np.random.randn(512).astype("float32")

    similarity = verifier.compute_similarity(emb1, emb2)
    assert 0.0 <= similarity <= 1.0


@pytest.mark.skipif(not Path("models").exists(), reason="Models not downloaded")
def test_identical_embeddings(verifier):
    """Test similarity of identical embeddings."""
    emb = np.random.randn(512).astype("float32")
    similarity = verifier.compute_similarity(emb, emb)
    assert 0.99 < similarity <= 1.0  # Should be very close to 1.0


@pytest.mark.skipif(not Path("models").exists(), reason="Models not downloaded")
def test_orthogonal_embeddings(verifier):
    """Test similarity of orthogonal embeddings."""
    emb1 = np.array([1, 0, 0] + [0] * 509, dtype="float32")
    emb2 = np.array([0, 1, 0] + [0] * 509, dtype="float32")
    similarity = verifier.compute_similarity(emb1, emb2)
    assert abs(similarity) < 0.1  # Should be close to 0


def test_threshold_setting(verifier):
    """Test threshold adjustment."""
    verifier.set_threshold(0.75)
    assert verifier.threshold == 0.75

    with pytest.raises(ValueError):
        verifier.set_threshold(1.5)  # Out of range


# Encryption Tests


def test_encryption_decryption(encryptor):
    """Test voiceprint encryption and decryption."""
    original = np.random.randn(512).astype("float32")

    encrypted = encryptor.encrypt_embedding(original)
    decrypted = encryptor.decrypt_embedding(encrypted)

    assert np.allclose(original, decrypted)


def test_voiceprint_file_save_load(encryptor):
    """Test saving and loading encrypted voiceprint."""
    original = np.random.randn(512).astype("float32")

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "voiceprint.encrypted"

        # Save
        success = encryptor.save_encrypted_voiceprint(original, str(filepath))
        assert success == True
        assert filepath.exists()

        # Load
        loaded = encryptor.load_encrypted_voiceprint(str(filepath))
        assert loaded is not None
        assert np.allclose(original, loaded)


# Command Parsing Tests


def test_command_parser():
    """Test command intent parsing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test commands file
        config_path = Path(tmpdir) / "commands.yaml"
        config_path.write_text("""commands:
  - intent: "what time|current time|time"
    command: "echo time"
    description: "Report time"
    sandbox: true
""")

        parser = CommandParser(str(config_path))

        result = parser.parse_intent("what time is it")
        assert result is not None
        assert result["description"] == "Report time"


def test_command_parser_no_match():
    """Test command parsing with no match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "commands.yaml"
        config_path.write_text("""commands:
  - intent: "time"
    command: "echo time"
    description: "Time"
    sandbox: true
""")

        parser = CommandParser(str(config_path))
        result = parser.parse_intent("launch nuclear missile")
        assert result is None


# Command Execution Tests


def test_command_executor_safe():
    """Test safe command execution."""
    executor = CommandExecutor(timeout=5)
    success, output = executor.execute_safe_echo("Hello, World!")
    assert success == True
    assert "Hello" in output


def test_command_executor_timeout():
    """Test command timeout."""
    executor = CommandExecutor(timeout=1)

    cmd_config = {"command": "sleep 10", "description": "Sleep"}

    success, output = executor.execute(cmd_config)
    assert success == False
    assert "timeout" in output.lower()


# Audit Logger Tests


def test_audit_logger():
    """Test audit logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "access.log"
        logger = AuditLogger(str(log_path))

        logger.log_verification_attempt("PASS", "Test pass")
        logger.log_verification_attempt("FAIL", "Test fail")

        assert log_path.exists()
        content = log_path.read_text()
        assert "PASS" in content
        assert "FAIL" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
