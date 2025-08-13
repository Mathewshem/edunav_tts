# api/pipeline.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from src.intent_router import to_intent
from src.text_utils import chunks_for_tts
import httpx
import os

router = APIRouter()

STT_BASE = os.getenv("STT_BASE", "http://127.0.0.1:8010")  # your running STT service
OCR_BASE = os.getenv("OCR_BASE", "http://127.0.0.1:8000")  # your OCR classifier+auto-ocr
TTS_BASE = os.getenv("TTS_BASE", "http://127.0.0.1:8020")  # your narrator

@router.post("/ai-pipeline")
async def ai_pipeline(file: UploadFile | None = File(default=None)):
    """
    If a file is uploaded: run OCR then speak the result.
    If not: listen for a voice command; if it's 'start_ocr' return a prompt via TTS.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if file is not None:
                data = await file.read()
                # call OCR auto endpoint
                ocr = (await client.post(f"{OCR_BASE}/ocr-auto",
                                         files={"file": (file.filename, data, file.content_type or "application/octet-stream")})
                      ).json()
                text = (ocr or {}).get("text", "") or "No text found."
                # speak in chunks
                for chunk in chunks_for_tts(text):
                    await client.post(f"{TTS_BASE}/speak", json={"text": chunk, "rate": 190})
                return {"ok": True, "path": "file->ocr->tts", "ocr": ocr}

            # no file: do voice command
            stt = (await client.post(f"{STT_BASE}/listen")).json()
            intent = to_intent(stt.get("command", ""))
            spoken = None
            if intent == "start_ocr":
                spoken = "Starting OCR. Please upload an image now."
            elif intent == "stop_reading":
                spoken = "Stopped reading."
            else:
                spoken = f"I heard: {stt.get('command','')}"
            await client.post(f"{TTS_BASE}/speak", json={"text": spoken, "rate": 190})
            return {"ok": True, "path": "listen->intent->tts", "intent": intent, "stt": stt}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")
