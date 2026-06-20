"""src/loader.py — read the active hotspot table (A-only or A+B enriched),
normalise names, and pick the right ranking direction for each phase.
"""
from __future__ import annotations
import functools
import pandas as pd
import config

_RENAME = {"h3_cell": "zone_id", "violation_count": "density"}
_B_COLS = ["V_calibrated", "delay_ratio", "veh_min_lost", "rupees_lost",
           "impact_weighted_rank", "C_io"]


@functools.lru_cache(maxsize=1)
def load_hotspots() -> pd.DataFrame:
    df = pd.read_csv(config.active_hotspots_csv()).rename(columns=_RENAME)
    df["h3_9"] = df["zone_id"]
    df.attrs["b_columns_present"] = [c for c in _B_COLS if c in df.columns]
    if "impact_weighted_rank" not in df:                 # A-only fallback rank
        df["impact_weighted_rank"] = (
            df["risk_debiased"] * df["severity_score"]
        ).rank(ascending=False, method="min").astype(int)
        df.attrs["rank_is_score"] = False
    else:
        # B's impact_weighted_rank is a SCORE: higher = more impact, 0 = unscored.
        df.attrs["rank_is_score"] = True
    return df


def b_impact_ready() -> bool:
    df = load_hotspots()
    if "veh_min_lost" not in df.columns:
        return False
    return (pd.to_numeric(df["veh_min_lost"], errors="coerce").fillna(0) > 0).any()


def _rank_score() -> bool:
    return load_hotspots().attrs.get("rank_is_score", False)


def get_zone(zone_id: str) -> dict | None:
    df = load_hotspots()
    row = df[df["zone_id"] == zone_id]
    return None if row.empty else row.iloc[0].to_dict()


def enriched_only() -> pd.DataFrame:
    """Cells B actually enriched (others are 0 and must not be shown as impact)."""
    df = load_hotspots()
    if "veh_min_lost" not in df.columns:
        return df
    m = pd.to_numeric(df["veh_min_lost"], errors="coerce").fillna(0) > 0
    return df[m]


def demand_anchored() -> pd.DataFrame:
    """Blind spots that are ALSO demand magnets (B's poi_demand) — Upgrade #2.

    A shadow hotspot is far more credible when something nearby *generates* the
    parking pressure. We keep blind-spot cells whose POI demand is at/above the
    median among cells that have any demand signal.
    """
    df = load_hotspots()
    if "poi_demand" not in df.columns:
        return df[df["blindspot_flag"] == 1]
    dem = pd.to_numeric(df["poi_demand"], errors="coerce").fillna(0)
    has = dem[dem > 0]
    thr = has.median() if len(has) else 0
    m = (df["blindspot_flag"] == 1) & (dem >= thr) & (dem > 0)
    return df[m].sort_values("poi_demand", ascending=False)


def top_by_impact(n: int = 12) -> pd.DataFrame:
    df = load_hotspots()
    if _rank_score():                       # B live: higher score first, drop zeros
        df = df[df["impact_weighted_rank"] > 0]
        return df.sort_values("impact_weighted_rank", ascending=False).head(n)
    return df.sort_values("impact_weighted_rank").head(n)   # A-only: 1..N rank


def top_blindspots(n: int = 12) -> pd.DataFrame:
    df = load_hotspots()
    return df[df["blindspot_flag"] == 1].sort_values(
        "risk_debiased", ascending=False).head(n)


def by_station(station: str) -> pd.DataFrame:
    df = load_hotspots()
    if "police_station" not in df.columns:
        return top_by_impact(50)
    sub = df[df["police_station"] == station]
    asc = not _rank_score()
    return sub.sort_values("impact_weighted_rank", ascending=asc)
