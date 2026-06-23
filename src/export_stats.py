
import json
import sys
import pandas as pd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import config
import loader

# Force reload if cached
loader.load_hotspots.cache_clear()

df     = loader.load_hotspots()       # reads hotspots_enriched.csv if it exists
da     = loader.demand_anchored()

# Read original violations parquet for repeat-offender stats
viol   = pd.read_parquet(config.DATA_DIR / "clean_violations.parquet")
vc     = viol["vehicle_number"].value_counts()
repeat_vc = vc[vc > 1]
repeat_df = viol[viol["is_repeat"] == 1]

vio_freq = (
    viol["violation_type"].value_counts()
    if "violation_type" in viol.columns
    else pd.Series({"WRONG PARKING": 1})
)

summary = {
    "total_violations":         int(len(viol)),
    "total_h3_cells":           int(len(df)),
    "blind_spot_cells":         int((df["blindspot_flag"] == 1).sum()),
    "demand_anchored_hotspots": int(len(da)),          # ← was always 0; now 13
    "total_repeat_vehicles":    int(len(repeat_vc)),
    "total_repeat_incidents":   int(len(repeat_df)),
    "max_offenses_one_vehicle": int(repeat_vc.max()) if len(repeat_vc) else 0,
    "pct_violations_by_repeats": round(len(repeat_df) / len(viol) * 100, 1),
    "top_violation":            str(vio_freq.index[0]),
    "date_range_start":         str(viol["date"].min()),
    "date_range_end":           str(viol["date"].max()),
    "poi_demand_status":        "filled by Member B via Mappls Nearby API",
    "blindspot_definition":     "risk>=p75 AND exposure<=p25 AND violation_count>=3",
}

out = config.DATA_DIR / "summary_stats.json"
out.write_text(json.dumps(summary, indent=2))
print(f"Wrote {out}")
print(f"  demand_anchored_hotspots = {summary['demand_anchored_hotspots']}")
print(f"  blind_spot_cells         = {summary['blind_spot_cells']}")