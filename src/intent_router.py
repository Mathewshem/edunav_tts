# src/intent_router.py
import re

_PATTERNS = [
    (r"\b(start|run|do)\b.*\bocr\b", "start_ocr"),
    (r"\b(read|speak)\b.*\b(text|result|selection)\b", "read_text"),
    (r"\b(stop|cancel|end)\b.*\b(read(ing)?|speech|talk)\b", "stop_reading"),
]

def to_intent(text: str) -> str | None:
    t = (text or "").lower()
    for pat, intent in _PATTERNS:
        if re.search(pat, t):
            return intent
    # quick synonyms
    if t.strip() in {"start ocr", "start", "begin"}: return "start_ocr"
    if t.strip() in {"stop", "stop reading", "cancel"}: return "stop_reading"
    return None
