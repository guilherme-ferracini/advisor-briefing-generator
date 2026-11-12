"""Portfolio aggregation and deterministic alerts per advisor and client."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

RISKY_CLASSES = {"equities", "multimarket", "international", "real_estate"}
# Maximum share of risky assets per suitability profile (illustrative policy)
MAX_RISKY_SHARE = {"conservative": 0.20, "moderate": 0.50, "aggressive": 1.00}
CONCENTRATION_LIMIT = 0.60
MATURITY_WINDOW_DAYS = 30


@dataclass
class Position:
    advisor: str
    client_id: str
    client_name: str
    risk_profile: str
    asset_class: str
    product: str
    amount: float
    maturity: Optional[date]


@dataclass
class ClientView:
    client_id: str
    client_name: str
    risk_profile: str
    total: float = 0.0
    by_class: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    maturing: List[Position] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)

    @property
    def risky_share(self) -> float:
        risky = sum(v for k, v in self.by_class.items() if k in RISKY_CLASSES)
        return risky / self.total if self.total else 0.0


@dataclass
class AdvisorView:
    advisor: str
    clients: List[ClientView]

    @property
    def aum(self) -> float:
        return sum(c.total for c in self.clients)

    @property
    def maturing_total(self) -> float:
        return sum(p.amount for c in self.clients for p in c.maturing)


def load_positions(path: Path) -> List[Position]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(Position(
                advisor=r["advisor"],
                client_id=r["client_id"],
                client_name=r["client_name"],
                risk_profile=r["risk_profile"],
                asset_class=r["asset_class"],
                product=r["product"],
                amount=float(r["amount_brl"]),
                maturity=datetime.strptime(r["maturity"], "%Y-%m-%d").date() if r["maturity"] else None,
            ))
    return rows


def build_views(positions: List[Position], today: date) -> List[AdvisorView]:
    grouped: Dict[str, Dict[str, ClientView]] = defaultdict(dict)
    for p in positions:
        client = grouped[p.advisor].setdefault(
            p.client_id, ClientView(p.client_id, p.client_name, p.risk_profile))
        client.total += p.amount
        client.by_class[p.asset_class] += p.amount
        if p.maturity and 0 <= (p.maturity - today).days <= MATURITY_WINDOW_DAYS:
            client.maturing.append(p)

    for clients in grouped.values():
        for c in clients.values():
            limit = MAX_RISKY_SHARE.get(c.risk_profile, 1.0)
            if c.risky_share > limit:
                c.alerts.append(
                    f"Suitability: {c.risky_share:.0%} in risk assets vs. {limit:.0%} limit for a {c.risk_profile} profile.")
            top_class, top_value = max(c.by_class.items(), key=lambda kv: kv[1])
            if c.total and top_value / c.total > CONCENTRATION_LIMIT:
                c.alerts.append(f"Concentration: {top_value / c.total:.0%} of the portfolio in {top_class}.")
            for p in c.maturing:
                c.alerts.append(
                    f"Maturity: {p.product} (R$ {p.amount:,.0f}) matures on {p.maturity:%d/%m}. Plan the reinvestment.")

    return [AdvisorView(a, sorted(cs.values(), key=lambda c: -c.total)) for a, cs in sorted(grouped.items())]
