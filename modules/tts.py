import asyncio
import edge_tts
import logging

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, voice="en-US-JennyNeural"):
        self.voice = voice
        logger.info(f"TTS Service initialized with edge-tts (voice: {voice})")

    async def generate_audio_stream(self, text: str):
        """Yields chunks of MP3 audio bytes"""
        if not text.strip():
            return
            
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            logger.error(f"TTS Error: {e}")
