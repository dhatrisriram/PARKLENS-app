"""PARKLENS — Member C config. The ONE switch is USE_REAL_B."""
from pathlib import Path

ROOT          = Path(__file__).resolve().parent.parent
DATA_DIR      = ROOT / "data"
HOTSPOTS_CSV  = DATA_DIR / "hotspots.csv"             # A-only (stub phase)
ENRICHED_CSV  = DATA_DIR / "hotspots_enriched.csv"    # A+B (Contract 2, real phase)
MAPPLS_CACHE  = DATA_DIR / "mappls_cache.json"
ROUTING_JSON  = DATA_DIR / "routing_plan.json"        # B's P-ROI output (optional)

# False → src/stubs.py.  True → B's impact_bpr + mappls_client (Checkpoint ③).
USE_REAL_B = True

# Impact constants — aligned to B so twin numbers match the enriched table/routing.
ALPHA            = 3.59
BETA             = 0.40
SAT_PER_LANE     = 1800.0
VOT_RUPEES_PER_MIN = 3.0     # B uses ₹3.0/min
PEAK_WINDOW_MIN  = 480       # B uses an 8h window

# Hand-picked believable corridor: 6 adjacent enriched cells (~2.8km arterial
# stretch in W. Bengaluru, anchored by a 1,665 veh-min hotspot). Real mode uses
# these in order; set to None to auto-pick top enriched cells.
CORRIDOR_CELLS = [
    "8960145a3cbffff", "8960145a3dbffff", "8960145a07bffff",
    "8960145a01bffff", "8960145a0d7ffff", "8960145a08bffff",
]
CORRIDOR_ID    = "bengaluru_west_arterial"
TOP_N_HOTSPOTS = 12          # stub mode only

MAPPLS_TILE_URL  = None
MAPPLS_TILE_ATTR = "Mappls / MapmyIndia"
NARRATIVE_MODEL  = "claude-sonnet-4-6"

def active_hotspots_csv() -> Path:
    """Prefer B's enriched table once it exists."""
    return ENRICHED_CSV if ENRICHED_CSV.exists() else HOTSPOTS_CSV
