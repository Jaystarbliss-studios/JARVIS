"""
Speaker Verification Module
Text-independent voice matching using ECAPA-TDNN embeddings.

CORE ALGORITHM:
1. Extract speaker embedding from audio (512-dim vector)
2. Compare with stored voiceprint using cosine similarity
3. Return PASS/FAIL based on configurable threshold

This is the critical security module - must be fail-secure.
"""

import torch
import numpy as np
import logging
from typing import Tuple, Optional
from pathlib import Path
import time

# Compatibility patch for torchaudio 2.9.1
try:
    import torchaudio
    if not hasattr(torchaudio, 'list_audio_backends'):
        torchaudio.list_audio_backends = lambda: ['cpu']
except:
    pass

# Patch huggingface_hub for speechbrain 1.0.3 compatibility
try:
    from huggingface_hub import hf_hub_download as _orig_hf_hub_download
    def patched_hf_hub_download(*args, **kwargs):
        # Remove deprecated parameter
        kwargs.pop('use_auth_token', None)
        return _orig_hf_hub_download(*args, **kwargs)
    import huggingface_hub
    huggingface_hub.hf_hub_download = patched_hf_hub_download
except:
    pass

# Suppress SYMLINK warning on Windows
import warnings
warnings.filterwarnings("ignore", message=".*SYMLINK strategy on Windows.*")

# Patch speechbrain to make custom.py optional
try:
    import speechbrain.utils.fetching as sb_fetching
    _orig_fetch_to_dir = sb_fetching.fetch_to_dir
    
    def patched_fetch_to_dir(*args, **kwargs):
        # If fetching custom.py and it fails, allow it
        try:
            return _orig_fetch_to_dir(*args, **kwargs)
        except Exception as e:
            if 'custom.py' in str(e) or '404' in str(e):
                logger.debug(f"Skipping optional file (custom.py): {e}")
                return args[1] if len(args) > 1 else kwargs.get('savedir', '.')
            raise
    
    sb_fetching.fetch_to_dir = patched_fetch_to_dir
except:
    pass

logger = logging.getLogger(__name__)


class SpeakerVerifier:
    """
    Text-independent speaker verification using pre-trained ECAPA-TDNN model.
    
    The ECAPA-TDNN model:
    - Works on any text/content (text-independent)
    - Produces 512-dim embeddings
    - Based on speaker recognition research (VoxCeleb dataset)
    - Achieves ~99% accuracy on standard benchmarks
    
    Security: Fail-secure - any error results in FAIL
    """
    
    def __init__(self, model_name: str = "speechbrain/spkrec-ecapa-voxceleb",
                 threshold: float = 0.70,
                 sample_rate: int = 16000):
        """
        Initialize speaker verification model.
        
        Args:
            model_name: HuggingFace model identifier
            threshold: Cosine similarity threshold (0.0-1.0)
            sample_rate: Audio sample rate in Hz
        
        Raises:
            RuntimeError: If model loading fails
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.model = None
        self.embedding_dim = 512  # ECAPA-TDNN output dimension
        
        self._load_model(model_name)
    
    def _load_model(self, model_name: str) -> None:
        """
        Load pre-trained speaker verification model.
        
        SECURITY: Model loaded once at startup. Fail if unavailable.
        """
        try:
            logger.info(f"Loading speaker verification model: {model_name}")
            
            # Try new API first
            try:
                from speechbrain.inference.speaker import SpeakerRecognition
                self.model = SpeakerRecognition.from_hparams(
                    source=model_name,
                    savedir=str(Path("models/speaker_verification")),
                    run_opts={"device": "cpu"}
                )
            except Exception as e1:
                # Fallback to older API with custom handling
                logger.debug(f"New API failed ({e1}), trying legacy API...")
                try:
                    from speechbrain.pretrained import EncoderClassifier
                    self.model = EncoderClassifier.from_hparams(
                        source=model_name,
                        savedir=str(Path("models/speaker_verification")),
                        run_opts={"device": "cpu"}
                    )
                except Exception as e2:
                    # If both fail, provide helpful error
                    logger.error(f"Both APIs failed: {e1} | {e2}")
                    raise RuntimeError(f"Model loading failed. Check internet connection and HuggingFace access.")
            
            logger.info("✓ Speaker verification model loaded successfully")
            
        except ImportError as e:
            logger.error(f"speechbrain not installed: {e}")
            raise RuntimeError("Install speechbrain: pip install speechbrain")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading error: {e}")
    
    def extract_embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract speaker embedding from audio.
        
        ALGORITHM:
        1. Preprocess audio (normalize, convert to tensor)
        2. Pass through ECAPA-TDNN encoder
        3. Get 512-dim speaker representation
        
        Args:
            audio: Audio array (16kHz mono, float32)
        
        Returns:
            Embedding vector (512-dim numpy array) or None if error
        """
        start_time = time.time()
        
        try:
            # Validate audio
            if len(audio) == 0:
                logger.error("Empty audio provided to embedding extraction")
                return None
            
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Normalize audio to [-1, 1]
            max_abs = np.max(np.abs(audio))
            if max_abs > 0:
                audio = audio / max_abs
            else:
                logger.error("Audio has zero amplitude")
                return None
            
            # Convert to torch tensor
            audio_tensor = torch.FloatTensor(audio).unsqueeze(0)
            
            # Extract embedding
            with torch.no_grad():
                embedding = self.model.encode_batch(audio_tensor)
            
            # Get numpy array and ensure shape
            embedding_np = embedding.squeeze().cpu().numpy()
            
            if embedding_np.ndim == 0:  # Scalar, something wrong
                logger.error("Invalid embedding shape")
                return None
            
            # Validate embedding
            if not np.isfinite(embedding_np).all():
                logger.error("Embedding contains NaN or Inf values")
                return None
            
            elapsed = time.time() - start_time
            logger.debug(f"Embedding extraction took {elapsed:.3f}s")
            
            return embedding_np.astype('float32')
            
        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None
    
    def compute_similarity(self, embedding1: np.ndarray, 
                          embedding2: np.ndarray) -> Optional[float]:
        """
        Compute cosine similarity between two embeddings.
        
        FORMULA:
        similarity = (e1 · e2) / (||e1|| * ||e2||)
        
        Range: 0.0 (completely different) to 1.0 (identical)
        
        Args:
            embedding1: First speaker embedding
            embedding2: Second speaker embedding
        
        Returns:
            Similarity score (0.0-1.0) or None if error
        """
        try:
            # Validate inputs
            if embedding1 is None or embedding2 is None:
                logger.error("None embedding provided")
                return None
            
            if len(embedding1) != len(embedding2):
                logger.error(f"Embedding dimension mismatch: {len(embedding1)} vs {len(embedding2)}")
                return None
            
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 < 1e-10 or norm2 < 1e-10:
                logger.error("Embedding has near-zero norm")
                return None
            
            emb1_normalized = embedding1 / norm1
            emb2_normalized = embedding2 / norm2
            
            # Cosine similarity
            similarity = float(np.dot(emb1_normalized, emb2_normalized))
            
            # Clamp to [0, 1] range (should already be in range)
            similarity = np.clip(similarity, 0.0, 1.0)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return None
    
    def verify(self, test_audio: np.ndarray, 
               enrolled_embedding: np.ndarray,
               return_score: bool = False) -> Tuple[bool, Optional[float]]:
        """
        Verify if test audio matches enrolled voiceprint.
        
        SECURITY DECISION LOGIC:
        - Fail-secure: Any error → FAIL
        - Extract embedding from test audio
        - Compute cosine similarity with voiceprint
        - Compare against threshold
        
        Args:
            test_audio: Audio to verify (numpy array)
            enrolled_embedding: Stored voiceprint embedding
            return_score: If True, return similarity score
        
        Returns:
            Tuple (verified: bool, similarity_score: Optional[float])
        """
        try:
            # Extract embedding from test audio
            test_embedding = self.extract_embedding(test_audio)
            if test_embedding is None:
                logger.warning("Could not extract embedding from test audio")
                return False, None
            
            # Compute similarity with enrolled embedding
            similarity = self.compute_similarity(test_embedding, enrolled_embedding)
            if similarity is None:
                logger.warning("Could not compute similarity score")
                return False, None
            
            # Make decision
            verified = similarity >= self.threshold
            
            # Log result (no biometric data in log)
            decision = "✓ PASS" if verified else "✗ FAIL"
            logger.info(f"Verification: {decision} (score: {similarity:.4f}, threshold: {self.threshold})")
            
            if return_score:
                return verified, similarity
            else:
                return verified, None
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            # Fail-secure: reject on any error
            return False, None
    
    def set_threshold(self, new_threshold: float) -> None:
        """
        Adjust verification threshold.
        
        Args:
            new_threshold: New similarity threshold (0.0-1.0)
        
        Raises:
            ValueError: If threshold out of valid range
        """
        if not (0.0 <= new_threshold <= 1.0):
            raise ValueError(f"Threshold must be in [0.0, 1.0], got {new_threshold}")
        
        self.threshold = new_threshold
        logger.info(f"Verification threshold set to {new_threshold:.2f}")
    
    @staticmethod
    def get_default_thresholds() -> dict:
        """Get recommended thresholds for different security levels."""
        return {
            "low_security": 0.60,     # Very permissive
            "normal": 0.70,           # Recommended (default)
            "high_security": 0.75,    # Stricter
            "paranoid": 0.80          # Very strict
        }
