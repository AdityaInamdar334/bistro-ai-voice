import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

from modules.vad import VADService
from modules.stt import STTService
from modules.llm import LLMService
from modules.tts import TTSService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vad_service = VADService()
stt_service = STTService()
llm_service = LLMService()
tts_service = TTSService()

# Ensure client directory exists
os.makedirs("client", exist_ok=True)
app.mount("/client", StaticFiles(directory="client"), name="client")

@app.get("/")
async def get():
    with open("client/index.html") as f:
        return HTMLResponse(f.read())

# Simple state class to share across callbacks
class AppState:
    is_answering = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected.")
    
    audio_buffer = bytearray()
    conversation_history = []
    answering_task = None
    state = AppState()

    def task_done_callback(t):
        state.is_answering = False

    try:
        while True:
            data = await websocket.receive_bytes()
            
            # If the user speaks, interrupt the bot immediately
            if state.is_answering and vad_service.is_speech(data):
                logger.info("User interrupted the bot!")
                if answering_task and not answering_task.done():
                    answering_task.cancel()
                state.is_answering = False
                await websocket.send_json({"type": "interrupt"})

            audio_buffer.extend(data)
            
            # Basic endpointing: process if we have >= 2 seconds of audio and the last 0.5s is silence
            if len(audio_buffer) >= 16000 * 2:  # assuming 16kHz, 1 byte per sample is wrong, 16bit is 2 bytes per sample, so 32000 bytes = 1s.
                # Let's fix the byte size: 16kHz 16-bit PCM = 32000 bytes/sec
                if len(audio_buffer) >= 32000 * 1.5:  # 1.5 seconds min
                    last_chunk = audio_buffer[-16000:] # last 0.5s
                    if not vad_service.is_speech(bytes(last_chunk)):
                        # User stopped speaking!
                        audio_to_process = bytes(audio_buffer)
                        audio_buffer.clear()
                        
                        if vad_service.is_speech(audio_to_process):
                            logger.info("Speech detected, processing...")
                            state.is_answering = True
                            answering_task = asyncio.create_task(
                                process_and_respond(websocket, audio_to_process, conversation_history)
                            )
                            answering_task.add_done_callback(task_done_callback)
                        
    except WebSocketDisconnect:
        logger.info("Client disconnected.")

async def process_and_respond(websocket: WebSocket, audio_data: bytes, conversation_history: list):
    try:
        # 1. STT
        await websocket.send_json({"type": "status", "message": "Listening..."})
        text = await stt_service.transcribe_audio(audio_data)
        if not text:
            return
            
        logger.info(f"User said: {text}")
        await websocket.send_json({"type": "transcript", "text": text, "sender": "user"})
        
        # 2. LLM
        system_prompt = "You are a helpful, concise AI voice assistant. Keep answers brief (1-2 sentences) and conversational."
        
        full_response = ""
        sentence_buffer = ""
        
        await websocket.send_json({"type": "status", "message": "Thinking..."})
        
        async for token in llm_service.generate_response_stream(system_prompt, text, conversation_history):
            full_response += token
            sentence_buffer += token
            
            # Simple sentence splitting
            if any(char in sentence_buffer for char in ['.', '?', '!']):
                sentence = sentence_buffer.strip()
                sentence_buffer = ""
                if sentence:
                    await websocket.send_json({"type": "transcript", "text": sentence, "sender": "ai"})
                    
                    audio_bytes = bytearray()
                    async for audio_chunk in tts_service.generate_audio_stream(sentence):
                        audio_bytes.extend(audio_chunk)
                    if audio_bytes:
                        await websocket.send_bytes(bytes(audio_bytes))
        
        # Process remaining buffer
        if sentence_buffer.strip():
            await websocket.send_json({"type": "transcript", "text": sentence_buffer.strip(), "sender": "ai"})
            
            audio_bytes = bytearray()
            async for audio_chunk in tts_service.generate_audio_stream(sentence_buffer.strip()):
                audio_bytes.extend(audio_chunk)
            if audio_bytes:
                await websocket.send_bytes(bytes(audio_bytes))
                
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": full_response})
        await websocket.send_json({"type": "status", "message": "Idle"})
        
    except asyncio.CancelledError:
        logger.info("Task cancelled due to interruption.")
    except Exception as e:
        logger.error(f"Error in process_and_respond: {e}")
