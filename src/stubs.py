"""src/stubs.py — Day-0 stand-ins for Member B's Contract-5 deliverables.

B will ship:
    impact_bpr.recompute(segment_id, c_io) -> {"T_a", "delay_ratio", ...}
    mappls_client.route_geometry(corridor_id) -> geojson-ish dict

C's graph.py / twin.py import ONLY these two names (via src/bdeps.py).
At Checkpoint ③ flip config.USE_REAL_B = True and these are bypassed — no other edits.

These stubs keep their own SEGMENTS registry the same way B's real recompute()
will read from mappls_cache.json, so the call signature is identical.
"""
from __future__ import annotations
import config

# graph.py registers segment attributes here so the stub can do the BPR math.
# B's real recompute() will instead look the segment up in its Mappls cache.
SEGMENTS: dict[str, dict] = {}


def register_segment(segment_id: str, **attrs) -> None:
    """Used by graph.py in stub mode. No-op effect once B is live."""
    SEGMENTS[segment_id] = attrs


def recompute(segment_id: str, c_io: float) -> dict:
    """Modified-BPR travel time for one segment with `c_io` capacity removed.

    Mirrors the signature B exposes. c_io is veh/h of capacity lost to illegal
    occupancy. Returns minutes (T_a) and the delay ratio vs. the c_io=0 baseline.
    """
    seg = SEGMENTS.get(segment_id)
    if seg is None:
        raise KeyError(f"segment {segment_id!r} not registered (stub mode)")

    T_0 = (seg["length_km"] / seg["freeflow_kmph"]) * 60.0       # minutes
    C   = seg["lanes"] * config.SAT_PER_LANE                     # veh/h
    V   = seg["volume"]                                          # veh/h

    cap_with    = max(C - c_io, 1.0)
    T_a_with    = T_0 * (1.0 + config.ALPHA * (V / cap_with) ** config.BETA)
    T_a_base    = T_0 * (1.0 + config.ALPHA * (V / C) ** config.BETA)
    return {
        "T_a": T_a_with,
        "T_a_base": T_a_base,
        "delay_ratio": T_a_with / T_a_base,
        "T_0": T_0,
        "V": V,
        "C": C,
    }


def route_geometry(corridor_id: str) -> dict:
    """Mock 5-segment corridor (~Koramangala 80ft Rd) as a LineString of 6 nodes.

    B's real version returns Mappls Routing geometry for the same corridor_id.
    Coordinates are [lon, lat] (geojson order).
    """
    coords = [
        [77.6105, 12.9352],
        [77.6128, 12.9341],
        [77.6151, 12.9330],
        [77.6174, 12.9319],
        [77.6197, 12.9308],
        [77.6220, 12.9297],
    ]
    return {
        "type": "LineString",
        "corridor_id": corridor_id,
        "coordinates": coords,
        # per-segment road attributes B's Snap-to-Road would provide:
        "segment_attrs": [
            {"lanes": 2, "freeflow_kmph": 38, "vc_baseline": 0.80},
            {"lanes": 2, "freeflow_kmph": 35, "vc_baseline": 0.88},
            {"lanes": 3, "freeflow_kmph": 42, "vc_baseline": 0.75},
            {"lanes": 2, "freeflow_kmph": 33, "vc_baseline": 0.90},
            {"lanes": 2, "freeflow_kmph": 36, "vc_baseline": 0.85},
        ],
    }
