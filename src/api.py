"""src/api.py — FastAPI surface (Contract 4), served from A/B outputs + the twin.

Endpoints:
  GET  /hotspots                         all zones (filter ?blindspot=1&limit=)
  GET  /risk?h3=<cell>                   de-biased risk for one cell
  GET  /impact?zone=<cell>               impact numbers (B cols or fallback)
  GET  /deploy?station=<s>&officers=<n>  ranked patrol plan (fallback until B's VRP)
  POST /whatif {zone, action}            twin recompute for clearing a hotspot

Run:  uvicorn src.api:app --reload   (from the project root)
      or:  cd src && uvicorn api:app --reload
"""
from __future__ import annotations
import os
import sys
import math
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# Make src/ (and the project root) importable regardless of cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))   # src/
_ROOT = os.path.dirname(_HERE)                        # project root
for _p in (_HERE, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import loader            # noqa: E402
from twin import Twin    # noqa: E402


def _clean(o):
    """Convert numpy scalars / NaN so FastAPI can JSON-serialise B's enriched data."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(x) for x in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        v = float(o)
        return None if math.isnan(v) else v
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, float) and math.isnan(o):
        return None
    return o

app = FastAPI(title="PARKLENS API", version="0.1")
_twin: Twin | None = None


def twin() -> Twin:
    global _twin
    if _twin is None:
        _twin = Twin()          # builds corridor once
    return _twin


@app.get("/hotspots")
def hotspots(blindspot: int | None = None, limit: int = 200):
    df = loader.load_hotspots()
    if blindspot is not None:
        df = df[df["blindspot_flag"] == blindspot]
    if loader.b_impact_ready():                 # B live: higher score first, no zeros
        df = df[df["impact_weighted_rank"] > 0].sort_values(
            "impact_weighted_rank", ascending=False)
    else:                                        # A-only: 1..N rank, ascending
        df = df.sort_values("impact_weighted_rank")
    df = df.head(limit)
    return _clean({
        "b_impact_ready": loader.b_impact_ready(),
        "count": len(df),
        "zones": df.to_dict(orient="records"),
    })


@app.get("/risk")
def risk(h3: str = Query(..., description="H3 res-9 cell")):
    z = loader.get_zone(h3)
    if z is None:
        raise HTTPException(404, f"cell {h3} not found")
    return _clean({
        "h3": h3,
        "risk_debiased": z["risk_debiased"],
        "blindspot_flag": int(z["blindspot_flag"]),
        "peak_dow": int(z["peak_dow"]),
        "exposure": int(z["exposure"]),
    })


@app.get("/impact")
def impact(zone: str):
    z = loader.get_zone(zone)
    if z is None:
        raise HTTPException(404, f"zone {zone} not found")
    return _clean({
        "zone": zone,
        "severity_score": z["severity_score"],
        "veh_min_lost": z.get("veh_min_lost"),
        "rupees_lost": z.get("rupees_lost"),
        "delay_ratio": z.get("delay_ratio"),
        "impact_weighted_rank": z["impact_weighted_rank"],
        "source": "B-real" if loader.b_impact_ready() else "fallback(risk×severity)",
    })


@app.get("/deploy")
def deploy(station: str | None = None, officers: int = 3):
    """Serve B's fair plan via the routing module (real file if present, else a
    derived fallback). Filters by station when the column is available."""
    import routing
    plan = routing.get_plan(officers_per_station=officers)
    stops = plan["stops"]
    if station:
        stops = [s for s in stops if s.get("police_station") == station]
    return _clean({"station": station, "officers": officers,
                   "source": plan["source"], "fairness_gini": plan["fairness_gini"],
                   "stops": stops})


class WhatIf(BaseModel):
    zone: str
    action: str = "off"        # "off" = clear the hotspot


@app.post("/whatif")
def whatif(req: WhatIf):
    if loader.get_zone(req.zone) is None:
        raise HTTPException(404, f"zone {req.zone} not found")
    if req.action == "off":
        return twin().compare(req.zone)
    return {"zone": req.zone, "note": "hotspot left in place (no recovery)",
            "recovery_pct": 0.0}
