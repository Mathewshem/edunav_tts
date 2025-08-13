# src/text_utils.py
def chunks_for_tts(text: str, max_len: int = 280):
    if not text:
        return []
    text = " ".join(text.split())
    out, buf = [], []
    length = 0
    for token in text.split(" "):
        if length + len(token) + 1 > max_len and buf:
            out.append(" ".join(buf))
            buf, length = [], 0
        buf.append(token)
        length += len(token) + 1
    if buf:
        out.append(" ".join(buf))
    return out
