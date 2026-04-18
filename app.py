from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel
import numpy as np
import logging
import asyncio

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SpeechAI")

# ---------------- APP ----------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------- MODEL ----------------
model = WhisperModel("medium", compute_type="int8")


# ---------------- STREAM ENGINE ----------------
class SpeechStream:
    def __init__(self):
        self.audio = np.array([], dtype=np.float32)
        self.raw = b""
        self.last_text = ""
        self.counter = 0

    def add(self, chunk):
        self.raw += chunk

        if len(self.raw) % 2 != 0:
            return None

        audio = np.frombuffer(self.raw, dtype=np.int16).astype(np.float32) / 32768.0
        self.raw = b""

        self.audio = np.concatenate((self.audio, audio))
        return self.audio

    def voice_detected(self):
        return np.abs(self.audio).mean() > 0.012

    def should_process(self):
        self.counter += 1
        return len(self.audio) > 48000 and self.counter % 2 == 0

    def window(self):
        w = self.audio.copy()
        self.audio = self.audio[-24000:]
        return w


# ---------------- TRANSCRIBE ----------------
def run_transcription(audio):
    segments, info = model.transcribe(
        audio,
        beam_size=5,
        best_of=3,
        language=None,
        condition_on_previous_text=True
    )

    text = " ".join([s.text for s in segments]).strip()
    lang = info.language

    logger.info(f"🗣️ {text}")
    logger.info(f"🌍 {lang}")

    return text


# ---------------- ROUTES ----------------
@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    logger.info("✅ Session started")

    stream = SpeechStream()

    try:
        while True:
            chunk = await ws.receive_bytes()

            audio = stream.add(chunk)
            if audio is None:
                continue

            # silence filter
            if not stream.voice_detected():
                continue

            # debounce processing (VERY IMPORTANT)
            if stream.should_process():
                window = stream.window()

                text = run_transcription(window)

                # avoid spam repeats
                if text and text != stream.last_text:
                    stream.last_text = text
                    await ws.send_text(text)

            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("🔌 Session closed")

    except Exception as e:
        logger.error(f"❌ Error: {e}")

    finally:
        logger.info("🧹 Cleanup done")