"""Optional: turn the spoken script into an MP3 with OpenAI text-to-speech.

Requires `pip install openai` and OPENAI_API_KEY. Delivery (e-mail, Teams,
WhatsApp) is left to the channel your team already uses.
"""

from __future__ import annotations

import os
from pathlib import Path


def script_part(briefing: str) -> str:
    text = briefing.split("PART 2", 1)[0]
    return text.replace("PART 1 - Script", "").strip()


def to_mp3(text: str, out_path: Path, voice: str = "alloy") -> Path:
    try:
        import openai
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Run `pip install openai` to generate audio.") from exc
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for audio.")
    client = openai.OpenAI()
    model = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
    with client.audio.speech.with_streaming_response.create(model=model, voice=voice, input=text) as resp:
        resp.stream_to_file(out_path)
    return out_path
