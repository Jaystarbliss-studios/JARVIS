"""
Audio Capture Module
Real-time microphone input with noise normalization and sample rate standardization.
"""

import sounddevice as sd
import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Handles real-time microphone input and preprocessing.
    Standardizes audio to 16kHz mono for speaker verification models.
    """
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, 
                 chunk_size: int = 1024, device_index: Optional[int] = None):
        """
        Initialize audio capture.
        
        Args:
            sample_rate: Target sample rate in Hz (default: 16000)
            channels: Number of channels (1 = mono only)
            chunk_size: Frames per buffer
            device_index: Microphone device index (None = default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_index = device_index
        
        logger.info(f"AudioCapture initialized: {sample_rate}Hz, {channels} channel(s)")
    
    def record(self, duration: float, show_progress: bool = True) -> np.ndarray:
        """
        Record audio from microphone for specified duration.
        
        SECURITY: Records to memory only, not disk (unless explicitly saved).
        
        Args:
            duration: Recording duration in seconds
            show_progress: Print progress indicator
        
        Returns:
            numpy array: Audio data (mono, 16-bit PCM)
        
        Raises:
            RuntimeError: If microphone unavailable
        """
        try:
            num_frames = int(duration * self.sample_rate)
            
            if show_progress:
                logger.info(f"Recording for {duration:.1f} seconds...")
            
            # Record from microphone
            audio = sd.rec(
                num_frames,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                device=self.device_index
            )
            sd.wait()
            
            # Convert to mono if needed
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            
            logger.info(f"Recording complete: {audio.shape[0]} samples captured")
            return audio.astype('float32')
            
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            raise RuntimeError(f"Audio capture error: {e}")
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to [-1.0, 1.0] range.
        Prevents clipping and standardizes amplitude.
        
        Args:
            audio: numpy array of audio samples
        
        Returns:
            Normalized audio array
        """
        max_val = np.max(np.abs(audio))
        
        if max_val > 0:
            audio = audio / max_val
        
        return audio.astype('float32')
    
    def remove_silence_padding(self, audio: np.ndarray, 
                               threshold: float = 0.01,
                               min_duration: float = 0.5) -> np.ndarray:
        """
        Remove leading/trailing silence from audio.
        
        Args:
            audio: Input audio array
            threshold: Amplitude threshold for silence detection
            min_duration: Minimum speech duration to keep (seconds)
        
        Returns:
            Trimmed audio array
        """
        # Calculate energy per frame
        frame_len = int(0.02 * self.sample_rate)  # 20ms frames
        energy = np.array([
            np.sum(audio[i:i+frame_len]**2) 
            for i in range(0, len(audio), frame_len)
        ])
        
        # Find non-silent frames
        energy_normalized = energy / (np.max(energy) + 1e-10)
        non_silent = energy_normalized > threshold
        
        if not np.any(non_silent):
            return audio  # All silent, return as-is
        
        # Find first and last non-silent frame
        first_idx = np.argmax(non_silent)
        last_idx = len(non_silent) - np.argmax(non_silent[::-1]) - 1
        
        # Convert back to sample indices
        start_sample = first_idx * frame_len
        end_sample = (last_idx + 1) * frame_len
        
        # Check minimum duration
        if (end_sample - start_sample) / self.sample_rate < min_duration:
            return audio  # Too short, return original
        
        return audio[start_sample:end_sample].astype('float32')
    
    def apply_preemphasis(self, audio: np.ndarray, coeff: float = 0.97) -> np.ndarray:
        """
        Apply preemphasis filter to enhance high frequencies.
        Improves speaker recognition accuracy.
        
        Args:
            audio: Input audio
            coeff: Preemphasis coefficient (typical: 0.97)
        
        Returns:
            Filtered audio
        """
        return np.append(
            audio[0], 
            audio[1:] - coeff * audio[:-1]
        ).astype('float32')
    
    def validate_audio(self, audio: np.ndarray) -> Tuple[bool, str]:
        """
        Validate audio quality for speaker verification.
        
        Returns:
            Tuple (is_valid, reason)
        """
        # Check if empty
        if len(audio) == 0:
            return False, "Empty audio"
        
        # Check if mostly silent
        energy = np.sum(audio ** 2)
        if energy < 1e-4:
            return False, "Audio too quiet (insufficient energy)"
        
        # Check for clipping (sign of audio saturation)
        peak = np.max(np.abs(audio))
        if peak > 0.99:
            return False, "Audio clipped (may be corrupted)"
        
        # Check for reasonable duration
        duration = len(audio) / self.sample_rate
        if duration < 0.5:
            return False, f"Audio too short ({duration:.2f}s < 0.5s)"
        
        if duration > 20:
            return False, f"Audio too long ({duration:.2f}s > 20s)"
        
        return True, "Valid"


def list_audio_devices():
    """List available audio input devices."""
    devices = sd.query_devices()
    logger.info("Available audio devices:")
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            logger.info(f"  [{i}] {device['name']}")
