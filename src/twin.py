"""src/twin.py — the what-if propagation engine (P4).

Toggle a hotspot off → its illegal-occupancy capacity (c_io) is freed on its
segment → recompute that segment's BPR travel time via B's engine → re-sum the
corridor → report recovered vehicle-minutes and ₹.

The c_io magnitude is the ONE thing the stub guesses; once B fills
hotspots.csv.veh_min_lost (or exposes per-zone c_io) we read the real value
(see _c_io_for). The propagation mechanics never change.
"""
from __future__ import annotations
import os
import sys
from dataclasses import dataclass

# Make src/ (and the project root) importable no matter where this is launched
# from, so the flat `import config` / `import loader` style resolves.
_HERE = os.path.dirname(os.path.abspath(__file__))   # src/
_ROOT = os.path.dirname(_HERE)                        # project root
for _p in (_HERE, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config            # noqa: E402
import loader            # noqa: E402
from bdeps import recompute               # noqa: E402
from graph import build_corridor, Corridor  # noqa: E402


# ── c_io model ───────────────────────────────────────────────────────────────
# Plan: C_io = f(footprint × severity × concurrent count). hotspots.csv has
# severity_score but not footprint, so the stub scales a base block by severity.
# B's real impact engine replaces this with a calibrated number.
_BASE_BLOCK_VEH_H = 220.0   # veh/h of capacity one uncleared hotspot removes @ sev≈3
_REF_SEVERITY     = 3.0


def _c_io_for(zone_id: str) -> float:
    z = loader.get_zone(zone_id) or {}
    # Prefer B's real capacity-removed value (the correct input to recompute).
    c_io = z.get("C_io")
    if c_io is not None and c_io == c_io and float(c_io) > 0:   # not NaN, >0
        return float(c_io)
    # Stub fallback (pre-integration): scale a base block by severity.
    sev = float(z.get("severity_score", _REF_SEVERITY) or _REF_SEVERITY)
    return _BASE_BLOCK_VEH_H * (sev / _REF_SEVERITY)


@dataclass
class SegmentResult:
    seg_id: str
    T_with: float        # min/veh, hotspots present
    T_without: float     # min/veh, after the chosen clear
    veh_min_saved: float
    rupees_saved: float


@dataclass
class TwinResult:
    cleared: list[str]
    corridor_T_with: float          # total corridor travel time (min/veh)
    corridor_T_without: float
    recovery_pct: float             # % travel-time reduction
    veh_min_saved: float
    rupees_saved: float
    segments: list[SegmentResult]


class Twin:
    def __init__(self, corridor: Corridor | None = None):
        self.corridor = corridor or build_corridor()

    # never let illegal occupancy remove more than this fraction of a segment's
    # capacity — keeps BPR finite when the MOCK corridor piles many hotspots on
    # one segment. Real Mappls geometry (Checkpoint ③) spreads them out.
    _MAX_CIO_FRAC = 0.85

    def _segment_time(self, seg, cleared: set[str]) -> float:
        """BPR travel time for a segment given which of its hotspots are cleared."""
        active = [z for z in seg.hotspots if z not in cleared]
        c_io = sum(_c_io_for(z) for z in active)
        cap = seg.lanes * config.SAT_PER_LANE
        c_io = min(c_io, self._MAX_CIO_FRAC * cap)
        return recompute(seg.seg_id, c_io)["T_a"]

    def evaluate(self, cleared: set[str] | None = None) -> TwinResult:
        cleared = cleared or set()
        seg_results: list[SegmentResult] = []
        tot_with = tot_without = 0.0
        tot_vm = tot_rs = 0.0
        win_h = config.PEAK_WINDOW_MIN / 60.0

        for seg in self.corridor.segments:
            t_with    = self._segment_time(seg, cleared=set())     # status quo
            t_without = self._segment_time(seg, cleared=cleared)   # after clears
            # veh-min saved = ΔT[min/veh] × V[veh/h] × window[h]
            vm = max(t_with - t_without, 0.0) * seg.volume * win_h
            rs = vm * config.VOT_RUPEES_PER_MIN
            tot_with += t_with
            tot_without += t_without
            tot_vm += vm
            tot_rs += rs
            seg_results.append(SegmentResult(seg.seg_id, t_with, t_without, vm, rs))

        recovery = 0.0 if tot_with == 0 else (tot_with - tot_without) / tot_with * 100
        return TwinResult(sorted(cleared), tot_with, tot_without, recovery,
                          tot_vm, tot_rs, seg_results)

    def compare(self, zone_id: str) -> dict:
        """The /whatif payload: clear ONE hotspot, report the recovery."""
        res = self.evaluate(cleared={zone_id})
        return {
            "zone": zone_id,
            "corridor_min_with": round(res.corridor_T_with, 2),
            "corridor_min_without": round(res.corridor_T_without, 2),
            "recovery_pct": round(res.recovery_pct, 1),
            "veh_min_saved": round(res.veh_min_saved, 0),
            "rupees_saved": round(res.rupees_saved, 0),
            "per_segment": [
                {"seg_id": s.seg_id,
                 "min_with": round(s.T_with, 2),
                 "min_without": round(s.T_without, 2)}
                for s in res.segments
            ],
        }


if __name__ == "__main__":
    twin = Twin()
    # clear the single highest-impact hotspot that actually sits on the corridor
    on_corridor = [z for seg in twin.corridor.segments for z in seg.hotspots]
    if on_corridor:
        demo = on_corridor[0]
        from pprint import pprint
        print(f"What-if: clear {demo}")
        pprint(twin.compare(demo))
    else:
        print("No hotspots mapped to corridor — check geometry/top_n.")
