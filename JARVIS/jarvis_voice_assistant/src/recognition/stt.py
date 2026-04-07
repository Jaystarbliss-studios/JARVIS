"""
Speech Recognition Module
Offline speech-to-text using Vosk.

Only triggered AFTER voice verification passes.
Converts verified speech to text for command parsing.
"""

import logging
from pathlib import Path
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class OfflineSTT:
    """
    Offline speech-to-text using Vosk recognizer.
    
    SECURITY: Only called after speaker verification.
    Models are small (~40MB) for CPU efficiency.
    """
    
    def __init__(self, model_path: str = "models/speech_recognition/vosk-model-small-en-us-0.15",
                 sample_rate: int = 16000):
        """
        Initialize offline STT.
        
        Args:
            model_path: Path to Vosk model directory
            sample_rate: Audio sample rate
        """
        self.model_path = Path(model_path)
        self.sample_rate = sample_rate
        self.recognizer = None
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Vosk speech recognition model."""
        try:
            from vosk import Model, KaldiRecognizer
            
            if not self.model_path.exists():
                logger.error(f"Model not found at {self.model_path}")
                logger.info("Download Vosk model from:")
                logger.info("  https://alphacephei.com/vosk/models")
                raise RuntimeError("Vosk model not found")
            
            logger.info(f"Loading Vosk model from {self.model_path}")
            model = Model(str(self.model_path))
            self.recognizer = KaldiRecognizer(model, self.sample_rate)
            
            logger.info("✓ Vosk STT model loaded")
            
        except ImportError:
            logger.error("vosk not installed: pip install vosk")
            raise RuntimeError("Install vosk: pip install vosk")
        except Exception as e:
            logger.error(f"Failed to load STT model: {e}")
            raise RuntimeError(f"STT initialization error: {e}")
    
    def transcribe(self, audio: np.ndarray) -> Optional[str]:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio array (16kHz mono, float32)
        
        Returns:
            Transcribed text or None if failed
        """
        try:
            if self.recognizer is None:
                logger.error("Recognizer not initialized")
                return None
            
            # Convert float32 to int16
            audio_int16 = (audio * 32767).astype('int16')
            
            # Process audio in chunks
            self.recognizer.AcceptWaveform(audio_int16.tobytes())
            result = self.recognizer.Result()
            
            # Parse result
            import json
            result_dict = json.loads(result)
            
            if "text" in result_dict:
                text = result_dict["text"].strip()
                if text:
                    logger.info(f"Transcribed: {text}")
                    return text
            
            logger.warning("No text recognized from audio")
            return None
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None


class WakeWordDetector:
    """
    Optional: Offline wake-word detection (e.g., "Jarvis").
    
    Prevents constant verification loop.
    Uses porcupine or similar small-footprint detector.
    """
    
    def __init__(self, wake_words: list = ["jarvis"],
                 sensitivity: float = 0.5):
        """
        Initialize wake-word detector.
        
        Args:
            wake_words: List of wake words to detect
            sensitivity: Detection sensitivity (0.0-1.0)
        """
        self.wake_words = wake_words
        self.sensitivity = sensitivity
        self.detector = None
        
        logger.info(f"Wake-word detection disabled by default (optional feature)")
        logger.info(f"To enable: 'pip install pvporcupine' and set config wake_word_enabled=true")
    
    def detect(self, audio: np.ndarray) -> bool:
        """
        Detect if wake word present in audio.
        
        Args:
            audio: Audio array
        
        Returns:
            True if wake word detected, False otherwise
        """
        # This is a placeholder - full implementation requires Porcupine SDK
        # For now, always return False (wake-word detection disabled)
        return False
