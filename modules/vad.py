import torch
import logging
import numpy as np
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

class VADService:
    def __init__(self):
        logger.info("Loading Silero VAD...")
        # Use trust_repo=True as required by newer torch.hub versions
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        (self.get_speech_timestamps,
         self.save_audio,
         self.read_audio,
         self.VADIterator,
         self.collect_chunks) = utils
        logger.info("Silero VAD loaded.")

    def is_speech(self, audio_data: bytes, sample_rate: int = 16000) -> bool:
        """Returns True if speech is detected in the audio chunk."""
        if not audio_data:
            return False
            
        # Convert raw audio bytes to float32 tensor
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_np)
        
        # Ensure we have at least some samples (Silero expects e.g. 512 or 1536)
        if len(audio_tensor) < 512:
            return False
            
        # Get speech timestamps for this chunk
        timestamps = self.get_speech_timestamps(
            audio_tensor, 
            self.model, 
            sampling_rate=sample_rate,
            threshold=0.5
        )
        return len(timestamps) > 0
