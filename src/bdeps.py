"""src/bdeps.py — the ONE seam that resolves B's functions (stub vs real).

Real mode reconciles the two Contract-5 mismatches automatically:
  • recompute() returns {T_a_with,...}; we add a normalised "T_a" key.
  • B's recompute reads a registry keyed by h3_cell, populated by
    load_segments() — we call it once here at import.
"""
import config

if config.USE_REAL_B:
    import impact_bpr
    import mappls_client  # noqa: F401  (used for live geometry if you want it)

    # populate B's segment registry (keyed by h3_cell) from the enriched table
    impact_bpr.load_segments(str(config.active_hotspots_csv()))

    _raw = impact_bpr.recompute

    def recompute(segment_id, c_io):
        """Adapter: B returns T_a_with/T_a_without; expose a unified T_a."""
        r = _raw(segment_id, c_io)
        r.setdefault("T_a", r.get("T_a_with"))
        return r

    def route_geometry(corridor_id):
        """Not needed for numbers in real mode (corridor is built from enriched
        cell coords). Kept as a no-op-ish hook if you later want a live polyline."""
        return {"type": "LineString", "coordinates": [], "corridor_id": corridor_id}

    def register_segment(*_a, **_k):
        return None
else:
    from stubs import recompute, route_geometry, register_segment  # noqa: F401
