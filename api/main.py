from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from src.tts_engine import list_voices, speak_text

app = FastAPI(title="EduNav+ TTS Narrator", version="1.0.0")

class SpeakIn(BaseModel):
    text: str
    voice_id: str | None = None
    rate: int | None = None
    volume: float | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/voices")
def voices():
    return {"voices": list_voices()}

@app.post("/speak")
def speak(payload: SpeakIn):
    try:
        speak_text(payload.text, payload.voice_id, payload.rate, payload.volume)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")


from api.pipeline import router as pipeline_router
app.include_router(pipeline_router)
