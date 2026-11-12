from datetime import date
from pathlib import Path

from briefing.generate import generate, mock_briefing
from briefing.llm import LLMClient
from briefing.portfolio import build_views, load_positions
from briefing.tts import script_part

SAMPLES = Path(__file__).parents[1] / "samples"
TODAY = date(2026, 11, 12)


def views():
    return {v.advisor: v for v in build_views(load_positions(SAMPLES / "portfolios.csv"), TODAY)}


def test_aum_per_advisor():
    v = views()
    assert v["Ana Ribeiro"].aum == 420000 + 260000 + 180000 + 350000 + 190000 + 140000 + 610000 + 330000
    assert len(v["Bruno Teixeira"].clients) == 3


def test_suitability_alert_for_conservative_client():
    c001 = next(c for c in views()["Ana Ribeiro"].clients if c.client_id == "C001")
    assert any(a.startswith("Suitability") for a in c001.alerts)   # 30% risky vs 20% limit


def test_maturity_window():
    bruno = views()["Bruno Teixeira"]
    maturing = {p.product for c in bruno.clients for p in c.maturing}
    assert maturing == {"Prefixed CDB Bank C", "CDB DI Bank A"}   # 2029 Selic bond is excluded


def test_concentration_alert():
    c006 = next(c for c in views()["Bruno Teixeira"].clients if c.client_id == "C006")
    assert any(a.startswith("Concentration") for a in c006.alerts)


def test_demo_briefing_mentions_every_client():
    view = views()["Ana Ribeiro"]
    text = generate(view, "notes", LLMClient("mock", mock_fn=mock_briefing))
    assert text.startswith("PART 1")
    for c in view.clients:
        assert c.client_name in text
    assert "Good morning, Ana" in script_part(text)
