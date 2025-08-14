# api/pipeline.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from src.intent_router import to_intent
from src.text_utils import chunks_for_tts
import os, base64, httpx

router = APIRouter()

STT_BASE     = os.getenv("STT_BASE", "http://127.0.0.1:8010")
OCR_BASE     = os.getenv("OCR_BASE", "http://127.0.0.1:8000")
TTS_BASE     = os.getenv("TTS_BASE", "http://127.0.0.1:8020")
BRAILLE_BASE = os.getenv("BRAILLE_BASE", "http://127.0.0.1:8040")

@router.post("/ai-pipeline")
async def ai_pipeline(
    file: UploadFile | None = File(default=None),
    braille: bool = Query(False),
    width: int = Query(40),
):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if file is not None:
                # ---- FILE PATH: OCR -> (speak) -> (braille)
                data = await file.read()
                ocr = (await client.post(
                    f"{OCR_BASE}/ocr-auto",
                    files={"file": (file.filename, data, file.content_type or "application/octet-stream")},
                )).json()

                text = (ocr or {}).get("text", "") or "No text found."

                # speak result in chunks
                for chunk in chunks_for_tts(text):
                    await client.post(f"{TTS_BASE}/speak", json={"text": chunk, "rate": 190})

                # optional braille file (base64 in response)
                brf_b64 = None
                if braille and text.strip():
                    br = await client.post(f"{BRAILLE_BASE}/braille-file", json={"text": text, "width": width})
                    br.raise_for_status()
                    brf_b64 = base64.b64encode(br.content).decode("ascii")

                return {"ok": True, "path": "file->ocr->tts", "ocr": ocr, "braille_b64": brf_b64}

            # ---- NO FILE: STT -> intent -> TTS
            stt = (await client.post(f"{STT_BASE}/listen")).json()
            intent = to_intent(stt.get("command", ""))

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
