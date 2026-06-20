"""src/routing.py — serve B's fair deployment plan to the Deploy tab.

Prefers B's real routing_plan.json (has police_station, officer_slot, fairness_gini).
If it isn't in data/ yet, derives a labelled fallback from the enriched table so
the tab is never empty. Drop B's file into data/ to upgrade automatically.
"""
from __future__ import annotations
import json
import pandas as pd
import config
import loader


def _gini(values) -> float:
    xs = sorted(float(v) for v in values if v is not None)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * sum(xs)) - (n + 1) / n


def get_plan(officers_per_station: int = 3) -> dict:
    # ── real plan from B ──────────────────────────────────────────────────────
    if config.ROUTING_JSON.exists():
        data = json.loads(config.ROUTING_JSON.read_text())
        return {
            "source": "B-real",
            "fairness_gini": data.get("fairness_gini"),
            "officers_per_station": data.get("officers_per_station"),
            "stops": data.get("plan", data.get("stops", [])),
        }

    # ── derived fallback (no police_station in enriched → single pool) ─────────
    df = loader.top_by_impact(officers_per_station * 6).copy()
    stops = []
    for n, (_, r) in enumerate(df.iterrows()):
        stops.append({
            "police_station": "(unzoned — drop routing_plan.json for stations)",
            "officer_slot": (n % officers_per_station) + 1,
            "h3_cell": r["zone_id"], "lat": r["lat"], "lon": r["lon"],
            "blindspot_flag": int(r["blindspot_flag"]),
            "poi_demand": int(r.get("poi_demand", 0) or 0),
            "impact_weighted_rank": float(r["impact_weighted_rank"]),
            "veh_min_lost": float(r.get("veh_min_lost", 0) or 0),
            "rupees_lost": float(r.get("rupees_lost", 0) or 0),
            "severity_score": float(r["severity_score"]),
            "peak_dow": int(r["peak_dow"]),
        })
    return {
        "source": "derived-fallback",
        "fairness_gini": round(_gini([s["veh_min_lost"] for s in stops]), 4),
        "officers_per_station": officers_per_station,
        "stops": stops,
    }


def as_frame(plan: dict) -> pd.DataFrame:
    return pd.DataFrame(plan["stops"])


if __name__ == "__main__":
    p = get_plan()
    print(f"source={p['source']}  gini={p['fairness_gini']}  stops={len(p['stops'])}")
