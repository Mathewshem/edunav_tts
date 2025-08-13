import pyttsx3, platform

def _engine():
    # Windows: sapi5; Linux (Pi): espeak
    driver = "sapi5" if platform.system() == "Windows" else "espeak"
    return pyttsx3.init(driverName=driver)

def list_voices():
    eng = _engine()
    out = []
    for v in eng.getProperty("voices"):
        out.append({"id": v.id, "name": getattr(v, "name", ""), "lang": getattr(v, "languages", [])})
    eng.stop()
    return out

def speak_text(text: str, voice_id: str | None = None, rate: int | None = None, volume: float | None = None):
    eng = _engine()
    if voice_id:
        eng.setProperty("voice", voice_id)
    if rate:
        eng.setProperty("rate", rate)        # ~200 default
    if volume is not None:
        eng.setProperty("volume", max(0.0, min(1.0, float(volume))))
    eng.say(text)
    eng.runAndWait()
    eng.stop()
