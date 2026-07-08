# Bistro AI Voice Agent

A real-time, low-latency conversational AI voice agent optimized for bidirectional streaming. This application demonstrates the integration of state-of-the-art machine learning models across the audio-processing pipeline to create a seamless, human-like voice interaction experience.

## Architecture and Technical Stack

The system is built on a modular, event-driven architecture utilizing WebSockets for real-time bidirectional communication.

- **Backend Framework**: FastAPI (Python) providing asynchronous WebSocket endpoints.
- **Voice Activity Detection (VAD)**: Silero VAD for highly accurate, low-latency speech detection.
- **Speech-to-Text (STT)**: Faster-Whisper (Systran) for rapid and accurate transcription of audio streams.
- **Language Model (LLM)**: Integration with NVIDIA API (or OpenAI compatible endpoints) for intelligent, context-aware reasoning and response generation.
- **Text-to-Speech (TTS)**: Edge-TTS for natural-sounding, synthesized voice output.
- **Frontend Client**: Vanilla JavaScript and HTML5 Web Audio API, establishing a direct WebSocket connection for audio byte-stream transmission and reception.

## Key Features

- **Full-Duplex Communication**: Supports continuous audio streaming from the client while simultaneously receiving synthesized speech back from the server.
- **Interruption Handling**: Advanced state management allows the user to interrupt the agent mid-sentence, instantly halting the current TTS stream and processing the new user input.
- **Modular Design**: Each component (VAD, STT, LLM, TTS) is isolated in its own module (`modules/`), allowing for straightforward swapping of underlying models (e.g., upgrading from Whisper to a specialized medical STT model) without impacting the broader system architecture.
- **Cross-Origin Support**: Pre-configured with CORS middleware to allow embedding the frontend interface across disparate domains, such as a developer portfolio.

## Live Demonstration

A live demonstration of the backend is currently routed securely via a Cloudflare Tunnel, exposing the WebSocket endpoint without exposing the host network.

**Live Backend WebSocket Endpoint:**
`wss://bureau-render-lightweight-quoted.trycloudflare.com/ws`

*Note: As this is a live demonstration endpoint, uptime is contingent on the host machine. The frontend client (`client/index.html`) is pre-configured to connect to this endpoint automatically.*

## Setup and Installation

### Prerequisites
- Python 3.11+
- FFmpeg (required for audio processing)

### Local Deployment

1. Clone the repository and navigate to the project root.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your API keys as environment variables:
   ```bash
   export NVIDIA_API_KEY="your-api-key"
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
5. Open `client/index.html` in your web browser. If connecting to a local server instead of the Cloudflare tunnel, modify the WebSocket connection string in `index.html` to `ws://localhost:8000/ws`.

## Project Structure

- `main.py`: Entry point for the FastAPI server and WebSocket routing.
- `modules/vad.py`: Voice Activity Detection integration.
- `modules/stt.py`: Speech-to-Text transcription logic.
- `modules/llm.py`: Language Model interfacing and prompt management.
- `modules/tts.py`: Text-to-Speech generation and audio chunking.
- `client/`: Static HTML, CSS, and JS frontend for microphone capture and audio playback.
