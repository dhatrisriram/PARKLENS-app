"""src/graph.py — build the corridor graph.

Stub mode : mock 5-segment Koramangala corridor (segment_attrs from stub).
Real mode : corridor = B's enriched hotspot cells. Each cell IS a segment, so
            segment_id == h3_cell (exactly what B's recompute() expects), and
            lanes / v0 / V_calibrated / C_io come straight from the enriched table.
            No live Mappls call needed for the numbers.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field

import networkx as nx
import config
from bdeps import route_geometry, register_segment
import loader


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2 +
         math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


@dataclass
class Segment:
    seg_id: str
    a: tuple[float, float]
    b: tuple[float, float]
    lanes: int
    freeflow_kmph: float
    length_km: float
    volume: float
    c_io: float = 0.0
    hotspots: list[str] = field(default_factory=list)

    @property
    def mid(self):
        return ((self.a[0] + self.b[0]) / 2, (self.a[1] + self.b[1]) / 2)


@dataclass
class Corridor:
    corridor_id: str
    graph: nx.DiGraph
    segments: list[Segment]

    def segment(self, seg_id):
        return next(s for s in self.segments if s.seg_id == seg_id)


def build_corridor(corridor_id=config.CORRIDOR_ID, top_n=config.TOP_N_HOTSPOTS):
    return (_build_real(top_n) if config.USE_REAL_B
            else _build_stub(corridor_id, top_n))


# ── real: corridor from B's enriched cells ───────────────────────────────────
def _build_real(top_n: int) -> Corridor:
    df = loader.enriched_only().copy()
    cells_order = getattr(config, "CORRIDOR_CELLS", None)
    if cells_order:
        # explicit hand-picked corridor, kept in the given order
        idx = {c: i for i, c in enumerate(cells_order)}
        sub = df[df["zone_id"].isin(cells_order)].copy()
        sub = sub.sort_values("zone_id", key=lambda s: s.map(idx)).reset_index(drop=True)
        cid = config.CORRIDOR_ID
        ordered = sub.to_dict("records")
    else:
        # fallback: most-enriched police_station, else top cells, chained by proximity
        if "police_station" in df.columns and df["police_station"].notna().any():
            station = df["police_station"].value_counts().idxmax()
            sub = df[df["police_station"] == station]
            cid = f"corridor::{station}"
        else:
            sub, cid = df, "corridor::top"
        sub = sub.sort_values("impact_weighted_rank", ascending=False).head(max(top_n, 3))
        cells = sub.reset_index(drop=True).to_dict("records")
        ordered, used = [cells[0]], {0}
        while len(ordered) < len(cells):
            last = ordered[-1]
            nxt = min((i for i in range(len(cells)) if i not in used),
                      key=lambda i: _haversine_km(last["lat"], last["lon"],
                                                  cells[i]["lat"], cells[i]["lon"]))
            ordered.append(cells[nxt]); used.add(nxt)

    G = nx.DiGraph(); segs = []
    for i, c in enumerate(ordered):
        nb = ordered[i + 1] if i + 1 < len(ordered) else c
        length = max(_haversine_km(c["lat"], c["lon"], nb["lat"], nb["lon"]), 0.05)
        lanes = int(c.get("lanes") or 2)
        v0    = float(c.get("v0_kmh") or 40)
        V     = float(c.get("V_calibrated") or 0.3 * lanes * config.SAT_PER_LANE)
        c_io  = float(c.get("C_io") or 0.0)
        seg = Segment(c["zone_id"], (c["lat"], c["lon"]), (nb["lat"], nb["lon"]),
                      lanes, v0, length, V, c_io, hotspots=[c["zone_id"]])
        segs.append(seg)
        G.add_edge(i, i + 1, seg_id=c["zone_id"])
    return Corridor(cid, G, segs)


# ── stub: mock corridor (unchanged behaviour) ────────────────────────────────
def _build_stub(corridor_id: str, top_n: int) -> Corridor:
    geo = route_geometry(corridor_id)
    coords, attrs = geo["coordinates"], geo.get("segment_attrs", [])
    G = nx.DiGraph(); segs = []
    for i in range(len(coords) - 1):
        lon_a, lat_a = coords[i]; lon_b, lat_b = coords[i + 1]
        at = attrs[i] if i < len(attrs) else {"lanes": 2, "freeflow_kmph": 40,
                                              "vc_baseline": 0.85}
        length = max(_haversine_km(lat_a, lon_a, lat_b, lon_b), 0.05)
        V = at["vc_baseline"] * at["lanes"] * config.SAT_PER_LANE
        sid = f"{corridor_id}::s{i}"
        segs.append(Segment(sid, (lat_a, lon_a), (lat_b, lon_b),
                            at["lanes"], at["freeflow_kmph"], length, V))
        register_segment(sid, length_km=length, lanes=at["lanes"],
                         freeflow_kmph=at["freeflow_kmph"], volume=V)
        G.add_edge(i, i + 1, seg_id=sid)
    corridor = Corridor(corridor_id, G, segs)
    hot = loader.top_by_impact(top_n)
    for _, h in hot.iterrows():
        nearest = min(segs, key=lambda s: _haversine_km(h["lat"], h["lon"], *s.mid))
        nearest.hotspots.append(h["zone_id"])
    return corridor


if __name__ == "__main__":
    c = build_corridor()
    print(f"[{'REAL' if config.USE_REAL_B else 'STUB'}] {c.corridor_id}: "
          f"{len(c.segments)} segments")
    for s in c.segments:
        print(f"  {s.seg_id}  {s.length_km:.2f}km  {s.lanes}ln  V={s.volume:.0f}  "
              f"C_io={s.c_io:.0f}  hotspots={s.hotspots}")
