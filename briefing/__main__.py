"""python -m briefing samples/portfolios.csv samples/market_notes.md --today 2026-11-12 --out out/"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .generate import generate, mock_briefing
from .llm import LLMClient
from .portfolio import build_views, load_positions


def slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def main() -> None:
    p = argparse.ArgumentParser(description="Personalised daily briefings for investment advisors")
    p.add_argument("portfolios", type=Path)
    p.add_argument("market_notes", type=Path)
    p.add_argument("--today", type=date.fromisoformat, default=date.today())
    p.add_argument("--provider", default=None, help="mock (default), anthropic or openai")
    p.add_argument("--model", default=None)
    p.add_argument("--out", type=Path, default=None, help="folder for one briefing file per advisor")
    p.add_argument("--audio", action="store_true", help="also create an MP3 of the script (OpenAI TTS)")
    a = p.parse_args()

    views = build_views(load_positions(a.portfolios), a.today)
    notes = a.market_notes.read_text(encoding="utf-8")
    client = LLMClient(a.provider, a.model, mock_fn=mock_briefing)

    for view in views:
        text = generate(view, notes, client)
        if a.out:
            a.out.mkdir(parents=True, exist_ok=True)
            path = a.out / f"{slug(view.advisor)}.md"
            path.write_text(f"# Briefing: {view.advisor} ({a.today:%d/%m/%Y})\n\n{text}\n", encoding="utf-8")
            print(f"Wrote {path}")
            if a.audio:
                from .tts import script_part, to_mp3
                print(f"Wrote {to_mp3(script_part(text), a.out / f'{slug(view.advisor)}.mp3')}")
        else:
            print(f"=== {view.advisor} ===\n{text}\n")


if __name__ == "__main__":
    main()
