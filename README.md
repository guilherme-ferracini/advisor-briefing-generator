# Advisor Briefing Generator

[![tests](https://github.com/guilherme-ferracini/advisor-briefing-generator/actions/workflows/tests.yml/badge.svg)](https://github.com/guilherme-ferracini/advisor-briefing-generator/actions)

Generates a **personalised daily briefing for each investment advisor**: a short spoken-style script plus talking points per client. It combines each advisor's book (positions, suitability, upcoming maturities) with the day's market notes. Optionally, it turns the script into an **MP3**.

## Why this exists

At an investment advisory office with 6 branches across 3 states, I led **KAT.IA**, an AI solution for the advisory team: a text assistant inside Microsoft Teams, plus automated, personalised audio briefings sent to each advisor based on their client portfolio and the market scenario.

This repo is a clean, standalone rewrite of the briefing idea, with fictional data, showing how I structure that kind of system:

- **Facts from code, wording from the model.** AUM, allocations, suitability breaches, concentration and maturities are computed deterministically in `portfolio.py` and covered by tests. The LLM only turns those facts and the market notes into a briefing, and is told not to recommend securities or promise returns.
- **Alerts first.** Maturities in the next 30 days, suitability breaches and concentration lead the talking points, because those are the calls that move money and reduce compliance risk.
- **Provider-agnostic, demo-ready.** `anthropic`, `openai`, or `mock` mode with no API key.

## Pipeline

```
portfolios.csv ──► portfolio.py ──► generate.py ──► one briefing per advisor (.md)
market_notes.md ─────────────────────┘                └──► tts.py ──► .mp3 (optional)
```

## Quickstart

```bash
pip install -r requirements.txt

# Demo mode: no API key needed
python -m briefing samples/portfolios.csv samples/market_notes.md --today 2026-11-12 --out out/

# AI-written briefings
export LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=...      # or openai
python -m briefing samples/portfolios.csv samples/market_notes.md --out out/

# Add audio (OpenAI text-to-speech)
export OPENAI_API_KEY=...
python -m briefing samples/portfolios.csv samples/market_notes.md --out out/ --audio
```

Example output (demo mode): [`samples/sample_output/ana-ribeiro.md`](samples/sample_output/ana-ribeiro.md)

```
Good morning, Ana. Your book is at R$ 2,480,000 across 3 clients, with R$ 770,000
maturing in the next 30 days. Today you have 4 alerts to work through...

- Client 001 (conservative, R$ 860,000): Suitability: 30% in risk assets vs. 20% limit
  for a conservative profile. Maturity: CDB DI Bank A (R$ 420,000) matures on 02/12.
```

## Rules (illustrative policy, easy to change)

| Rule | Default |
|---|---|
| Max share in risk assets | conservative 20% · moderate 50% · aggressive 100% |
| Concentration alert | one asset class above 60% of the portfolio |
| Maturity window | next 30 days |

## Tests

```bash
python -m pytest -q
```

## Notes

- All names, clients and market notes are fictional.
- Delivery (Teams, e-mail, WhatsApp) is intentionally left out: plug in the channel your team already uses.

## License

MIT
