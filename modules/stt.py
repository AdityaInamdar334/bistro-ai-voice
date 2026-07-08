import numpy as np
from faster_whisper import WhisperModel
import asyncio
import logging

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, model_size="base.en"):
        logger.info(f"Loading faster-whisper model '{model_size}'...")
        # device="cpu" since MPS support for faster-whisper can be tricky to set up seamlessly in a basic environment
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info("STT model loaded.")

    async def transcribe_audio(self, audio_data: bytes) -> str:
        # faster-whisper blocking call, we run it in a thread
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, self._transcribe, audio_data)
        return text

    def _transcribe(self, audio_data: bytes) -> str:
        # Expecting raw 16kHz PCM 16-bit audio
        if not audio_data:
            return ""
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        segments, _ = self.model.transcribe(audio_np, beam_size=5, language="en", condition_on_previous_text=False)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
