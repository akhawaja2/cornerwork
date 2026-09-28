"""Voice-note transcription. Whisper via the OpenAI REST API when OPENAI_API_KEY is set and DEMO_MODE != 1;
otherwise a labelled canned transcript so the pipeline stays demoable offline."""
import os

import httpx

DEMO_TRANSCRIPT = "[demo transcript] Clinch felt sharper today. Kept getting countered off the jab. My left shin is sore after checks."


def transcribe(audio: bytes, filename: str, content_type: str) -> tuple[str, str]:
    """Returns (transcript, model)."""
    key = os.environ.get("OPENAI_API_KEY")
    if os.environ.get("DEMO_MODE") == "1" or not key:
        return DEMO_TRANSCRIPT, "fake-transcript"
    r = httpx.post("https://api.openai.com/v1/audio/transcriptions", headers={"Authorization": f"Bearer {key}"},
                   files={"file": (filename, audio, content_type)}, data={"model": "whisper-1"}, timeout=120)
    r.raise_for_status()
    return r.json()["text"].strip(), "whisper-1"
