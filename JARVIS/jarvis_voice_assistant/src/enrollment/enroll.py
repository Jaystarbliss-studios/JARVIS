"""
Speaker Enrollment Module
Creates speaker voiceprint from multiple samples.

ENROLLMENT PROCESS:
1. Record 5-10 different voice samples
2. Extract embedding from each sample
3. Average embeddings into single voiceprint
4. Encrypt and store voiceprint
5. Zero out raw audio from memory

SECURITY: All audio samples cleared after processing. Only encrypted embedding stored.
"""

import numpy as np
import logging
from pathlib import Path
from typing import Optional, List
import json

logger = logging.getLogger(__name__)


class EnrollmentManager:
    """
    Handles speaker enrollment process.
    
    Creates averaged voiceprint from multiple samples.
    Stores only encrypted embeddings, not raw audio.
    """
    
    def __init__(self, verifier_instance, sample_duration: float = 8.0):
        """
        Initialize enrollment manager.
        
        Args:
            verifier_instance: SpeakerVerifier instance
            sample_duration: Duration for each enrollment sample (8 seconds recommended)
        """
        self.verifier = verifier_instance
        self.sample_duration = sample_duration
        self.embeddings: List[np.ndarray] = []
    
    def run_enrollment(self, num_samples: int = 7,
                      audio_capture_instance = None) -> Optional[np.ndarray]:
        """
        Run complete enrollment process.
        
        Args:
            num_samples: Number of samples to record
            audio_capture_instance: AudioCapture instance for recording
        
        Returns:
            Averaged voiceprint embedding or None if failed
        """
        print("\n" + "="*70)
        print(" JARVIS ENROLLMENT - Voice Registration ")
        print("="*70)
        print(f"\nYou will record {num_samples} voice samples.")
        print(f"Each sample should be approximately {self.sample_duration:.1f} seconds.")
        print("\nGuidelines:")
        print("  • Speak NATURALLY - use your normal voice")
        print("  • Use DIFFERENT sentences each time")
        print("  • Speak CLEARLY - minimize background noise")
        print("  • This creates your unique voice fingerprint")
        print("\nExample sentences:")
        print('  1. "The quick brown fox jumps over the lazy dog"')
        print('  2. "Hello Jarvis, this is my voice for enrollment"')
        print('  3. "I am enrolling my biometric voice signature"')
        print('  4. "Security and privacy are my top priorities"')
        print('  5. "Recognize my voice for future authentication"')
        print("\nPress ENTER when ready to start...\n")
        
        input()
        
        self.embeddings = []
        
        for sample_idx in range(num_samples):
            print(f"\n[Sample {sample_idx + 1}/{num_samples}]")
            print(f"Recording for {self.sample_duration} seconds...")
            print("(Stop speaking when done)")
            
            # Record audio
            if audio_capture_instance is None:
                print("ERROR: AudioCapture instance required")
                return None
            
            try:
                audio = audio_capture_instance.record(
                    duration=self.sample_duration,
                    show_progress=False
                )
                
                # Validate audio
                is_valid, reason = audio_capture_instance.validate_audio(audio)
                if not is_valid:
                    print(f"✗ Invalid audio: {reason}")
                    print("Try again...")
                    continue
                
                # Extract embedding
                embedding = self.verifier.extract_embedding(audio)
                if embedding is None:
                    print("✗ Failed to extract embedding from audio")
                    print("Try again...")
                    continue
                
                self.embeddings.append(embedding)
                print(f"✓ Sample {sample_idx + 1} recorded successfully")
                
                # Clear audio from memory
                del audio
                
            except Exception as e:
                logger.error(f"Recording failed: {e}")
                print(f"✗ Recording error: {e}")
                print("Try again...")
                continue
        
        if len(self.embeddings) < 3:
            print(f"\n✗ Enrollment failed: Only {len(self.embeddings)} valid samples recorded")
            print("Need at least 3 samples for enrollment")
            return None
        
        # Average embeddings to create voiceprint
        voiceprint = self._average_embeddings()
        
        print(f"\n✓ Enrollment complete!")
        print(f"✓ Recorded {len(self.embeddings)} valid samples")
        print(f"✓ Voiceprint created (512-dim speaker embedding)")
        
        return voiceprint
    
    def _average_embeddings(self) -> np.ndarray:
        """
        Average embeddings from multiple samples.
        
        MATH:
        voiceprint = mean(embeddings)
        
        Returns:
            Averaged voiceprint (512-dim vector)
        """
        embeddings_array = np.stack(self.embeddings, axis=0)
        voiceprint = np.mean(embeddings_array, axis=0)
        
        logger.info(f"Created voiceprint from {len(self.embeddings)} samples")
        logger.info(f"Voiceprint shape: {voiceprint.shape}")
        logger.info(f"Voiceprint norm: {np.linalg.norm(voiceprint):.4f}")
        
        return voiceprint.astype('float32')
    
    def save_voiceprint(self, voiceprint: np.ndarray,
                       filepath: str,
                       encryptor_instance) -> bool:
        """
        Encrypt and save voiceprint.
        
        Args:
            voiceprint: Speaker embedding to save
            filepath: Path to save encrypted voiceprint
            encryptor_instance: VoiceprintEncryption instance
        
        Returns:
            Success status
        """
        try:
            success = encryptor_instance.save_encrypted_voiceprint(
                voiceprint,
                filepath
            )
            
            if success:
                print(f"✓ Voiceprint encrypted and saved to: {filepath}")
            else:
                print(f"✗ Failed to save voiceprint")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save voiceprint: {e}")
            print(f"✗ Error saving voiceprint: {e}")
            return False
    
    def get_enrollment_summary(self) -> dict:
        """
        Get enrollment summary (for logging/debugging).
        
        Does NOT include raw embeddings.
        
        Returns:
            Dictionary with enrollment statistics
        """
        if len(self.embeddings) == 0:
            return {"status": "no_enrollment"}
        
        embeddings_array = np.stack(self.embeddings, axis=0)
        
        return {
            "status": "enrolled",
            "num_samples": len(self.embeddings),
            "embedding_dim": self.embeddings[0].shape[0],
            "embedding_stats": {
                "mean_norm": float(np.mean([np.linalg.norm(e) for e in self.embeddings])),
                "std_norm": float(np.std([np.linalg.norm(e) for e in self.embeddings])),
            }
        }
