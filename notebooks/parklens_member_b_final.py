"""
parklens_member_b_final.py — Member B complete pipeline
Run: python parklens_member_b_final.py YOUR_KEY

Reads:  /content/data/hotspots.csv
        /content/data/clean_violations.parquet
Writes: /content/output/hotspots_enriched_FINAL.csv
        /content/output/routing_plan.csv
        /content/output/routing_plan.json
        /content/output/impact_bpr.py
        /content/output/mappls_cache.json
"""

import os, sys, json, time, math, requests
from pathlib import Path
import pandas as pd
import numpy as np
import polyline as _poly
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
if len(sys.argv) < 2:
    sys.exit("Usage: python parklens_member_b_final.py YOUR_MAPPLS_KEY")

KEY      = sys.argv[1].strip()
TOP_N    = int(sys.argv[2]) if len(sys.argv) > 2 else 100
DATA_DIR = Path(os.environ.get("DATA_DIR", "/content/data"))
OUT_DIR  = Path(os.environ.get("OUT_DIR",  "/content/output"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALPHA                = 3.59
BETA                 = 0.40
VOT_RS_PER_MIN       = 3.0
SAT_FLOW             = 1800
ENFORCEMENT_WINDOW_H = 8
PATROL_RADIUS_KM     = 30 * (15/60)
PATROL_AREA_KM2      = round(math.pi * PATROL_RADIUS_KM**2, 2)
OFFICERS_PER_STATION = 3

FOOTPRINT_C_IO = {0.5:0.10, 1.0:0.25, 1.5:0.40, 2.0:0.60, 3.0:1.00}
ROAD_CLASS_VC  = {"arterial":0.60, "collector":0.45, "local":0.35, "unknown":0.45}
CATEGORIES     = ["TRNPMP", "FODCOF", "HOTPRE", "SHPG", "EDUC", "HOSP"]

# ── Cache ─────────────────────────────────────────────────────────────────────
CACHE_FILE = OUT_DIR / "mappls_cache.json"
def _load(): return json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
def _save(c): CACHE_FILE.write_text(json.dumps(c, indent=2))
CACHE = _load()
print(f"Cache loaded: {len(CACHE)} entries")

# ── Mappls API calls ──────────────────────────────────────────────────────────
def _tiny_poly(lat, lon, offset=0.0003):
    return _poly.encode([(lat-offset, lon), (lat+offset, lon)], 5)

def get_poi(lat, lon, h3):
    key = f"poi_{h3}"
    if key in CACHE: return CACHE[key]
    path = _tiny_poly(lat, lon)
    total = 0
    for cat in CATEGORIES:
        try:
            r = requests.post(
                f"https://search.mappls.com/search/places/along-route?access_token={KEY}",
                data={"geometries":"polyline5","path":path,"category":cat,
                      "buffer":"1000","page":"1","sort":""},
                timeout=15)
            if r.status_code == 200:
                total += len(r.json().get("suggestedPOIs", []))
        except: pass
        time.sleep(0.1)
    CACHE[key] = total; _save(CACHE)
    return total

def get_road_class(lat, lon, h3):
    key = f"road_{h3}"
    if key in CACHE: return CACHE[key]
    result = {"road_class":"unknown","lanes":2,"v0_kmh":40}
    try:
        # Snap to road
        lon2, lat2 = lon+0.003, lat+0.003
        rs = requests.post(
            f"https://route.mappls.com/route/movement/snapToRoad?access_token={KEY}",
            data={"pts":f"{lon},{lat};{lon2},{lat2}","geometries":"polyline"},
            timeout=10)
        slat, slon = lat, lon
        if rs.status_code == 200:
            pts = rs.json().get("results",{}).get("snappedPoints",[])
            if pts:
                loc = pts[0]["location"]
                slat, slon = loc[1], loc[0]
        # Directions for speed
        dlat = slat + 0.0018
        rd = requests.get(
            f"https://route.mappls.com/route/direction/route_adv/driving/"
            f"{slon},{slat};{slon},{dlat}?access_token={KEY}",
            timeout=10)
        if rd.status_code == 200:
            routes = rd.json().get("routes",[])
            if routes:
                legs = routes[0].get("legs",[])
                if legs:
                    dur = legs[0].get("duration",0)
                    dst = legs[0].get("distance",1)
                    if dur > 0 and dst > 0:
                        spd = (dst/1000)/(dur/3600)
                        if spd >= 55:   result = {"road_class":"arterial",  "lanes":2,"v0_kmh":round(spd)}
                        elif spd >= 35: result = {"road_class":"collector", "lanes":2,"v0_kmh":round(spd)}
                        else:           result = {"road_class":"local",     "lanes":1,"v0_kmh":round(spd)}
    except Exception as e:
        print(f"  [Road] {h3}: {e}")
    CACHE[key] = result; _save(CACHE); time.sleep(0.2)
    return result

def get_eta(lat, lon, h3):
    key = f"eta_{h3}"
    if key in CACHE:
        cached = CACHE[key]
        # If cached value is flat 1.0 from old run, re-call
        if isinstance(cached, dict) and cached.get("eta_ratio", 1.0) != 1.0:
            return cached
    dlat = lat + 0.0045
    result = {"eta_ratio":1.0, "T_freeflow_s":None, "distance_m":None}
    try:
        url = (f"https://route.mappls.com/route/dm/distance_matrix/driving/"
               f"{lon},{lat};{lon},{dlat}?access_token={KEY}")
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            d    = r.json()
            # correct keys: results.durations and results.distances
            res  = d.get("results", {})
            durs = res.get("durations") or d.get("durations")
            dist = res.get("distances") or d.get("distances")
            if durs and dist and len(durs[0]) > 1 and durs[0][1] and dist[0][1]:
                T_free   = durs[0][1]       # seconds
                distance = dist[0][1]       # metres
                # compute ratio vs assumed free-flow speed (40 km/h)
                assumed_free = distance / (40/3.6)
                ratio = T_free / assumed_free if assumed_free > 0 else 1.0
                result = {
                    "eta_ratio":   round(ratio, 4),
                    "T_freeflow_s": round(T_free, 2),
                    "distance_m":   round(distance, 1),
                }
        else:
            print(f"  [ETA] {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  [ETA] {h3}: {e}")
    CACHE[key] = result; _save(CACHE); time.sleep(0.15)
    return result

# ── BPR functions ─────────────────────────────────────────────────────────────
def footprint_to_cio(fp):
    for k in sorted(FOOTPRINT_C_IO):
        if fp <= k: return FOOTPRINT_C_IO[k]
    return FOOTPRINT_C_IO[max(FOOTPRINT_C_IO)]

def backsove_vc(ratio):
    val = max(ratio - 1.0, 0.0) / ALPHA
    return val**(1.0/BETA) if val > 0 else None

def compute_impact(V, C, v0_kmh, avg_fp, severity):
    C_io  = footprint_to_cio(avg_fp) * min(severity/5.0, 1.0) * SAT_FLOW
    C_eff = max(C - C_io, 0.1*C)
    T0    = (0.5/v0_kmh)*60
    Tw    = T0*(1+ALPHA*(V/C_eff)**BETA)
    Two   = T0*(1+ALPHA*(V/C)**BETA)
    dr    = Tw/Two if Two>0 else 1.0
    vml   = (Tw-Two)*V*ENFORCEMENT_WINDOW_H
    return {
        "delay_ratio":  round(dr, 4),
        "veh_min_lost": round(vml, 1),
        "rupees_lost":  round(vml*VOT_RS_PER_MIN, 0),
        "C_io":         round(C_io, 1),
    }

def gini(arr):
    arr = np.array(arr, dtype=float)
    if arr.sum() == 0: return 0.0
    arr.sort(); n=len(arr); idx=np.arange(1,n+1)
    return (2*np.sum(idx*arr)/(n*arr.sum()))-(n+1)/n

# ── Load data ─────────────────────────────────────────────────────────────────
print("\nLoading data...")
hotspots = pd.read_csv(DATA_DIR/"hotspots.csv")
if "h3_9" in hotspots.columns and "h3_cell" not in hotspots.columns:
    hotspots.rename(columns={"h3_9":"h3_cell"}, inplace=True)

viol = pd.read_parquet(DATA_DIR/"clean_violations.parquet")
if "h3_9" in viol.columns and "h3_cell" not in viol.columns:
    viol.rename(columns={"h3_9":"h3_cell"}, inplace=True)

# Footprint + severity per cell
fp_cell = viol.groupby("h3_cell").agg(
    avg_footprint=("vehicle_footprint","mean"),
).reset_index()

# Police station per cell
ps_map = viol.groupby("h3_cell")["police_station"].agg(
    lambda x: x.mode()[0]).reset_index()

top = hotspots.nlargest(TOP_N, "risk_debiased").reset_index(drop=True)
top = top.merge(fp_cell, on="h3_cell", how="left")
top["avg_footprint"] = top["avg_footprint"].fillna(1.0)
print(f"Loaded {len(hotspots)} hotspots. Enriching top {TOP_N}.")

# ── Step 1: POI demand ────────────────────────────────────────────────────────
print("\n[1/5] POI demand...")
poi_counts = []
for _, row in tqdm(top.iterrows(), total=len(top), desc="POI"):
    poi_counts.append(get_poi(row["lat"], row["lon"], row["h3_cell"]))
top["poi_demand"] = poi_counts
print(f"POI done. Non-zero: {sum(p>0 for p in poi_counts)}/{TOP_N}")

# ── Step 2: Road class ────────────────────────────────────────────────────────
print("\n[2/5] Road class (Snap + Directions)...")
road_infos = []
for _, row in tqdm(top.iterrows(), total=len(top), desc="Road"):
    road_infos.append(get_road_class(row["lat"], row["lon"], row["h3_cell"]))
top["road_class"] = [r["road_class"] for r in road_infos]
top["lanes"]      = [r["lanes"]      for r in road_infos]
top["v0_kmh"]     = [r["v0_kmh"]     for r in road_infos]
print(f"Road class dist: {top['road_class'].value_counts().to_dict()}")

# ── Step 3: ETA calibration ───────────────────────────────────────────────────
print("\n[3/5] ETA calibration (Distance Matrix)...")
eta_results = []
for _, row in tqdm(top.iterrows(), total=len(top), desc="ETA"):
    eta_results.append(get_eta(row["lat"], row["lon"], row["h3_cell"]))

top["eta_ratio"]   = [e["eta_ratio"]    for e in eta_results]
top["T_freeflow_s"]= [e.get("T_freeflow_s") for e in eta_results]
top["distance_m"]  = [e.get("distance_m")   for e in eta_results]

# Back-solve V from ETA, floor at road-class baseline
top["C"]           = top["lanes"] * SAT_FLOW
vc_from_eta        = top["eta_ratio"].apply(backsove_vc)
vc_from_road       = top["road_class"].map(ROAD_CLASS_VC).fillna(0.45)
top["vc_calibrated"]= vc_from_eta.where(vc_from_eta.notna(), vc_from_road)
top["vc_calibrated"]= top["vc_calibrated"].combine(vc_from_road, max)
top["V_calibrated"] = (top["vc_calibrated"] * top["C"]).round(0)

n_real = (top["eta_ratio"] > 1.0).sum()
print(f"ETA > 1.0 (congested): {n_real}/{TOP_N} zones")
print(f"eta_ratio range: {top['eta_ratio'].min():.3f} – {top['eta_ratio'].max():.3f}")
print(f"V_calibrated range: {top['V_calibrated'].min():.0f} – {top['V_calibrated'].max():.0f}")

# ── Step 4: MBPR impact ───────────────────────────────────────────────────────
print("\n[4/5] MBPR impact engine...")
impacts = []
for _, row in top.iterrows():
    imp = compute_impact(
        V        = row["V_calibrated"],
        C        = row["C"],
        v0_kmh   = row["v0_kmh"],
        avg_fp   = row["avg_footprint"],
        severity = row["severity_score"],
    )
    impacts.append(imp)

impact_df = pd.DataFrame(impacts)
top = pd.concat([top, impact_df], axis=1)

top["impact_weighted_rank"] = (
    top["risk_debiased"]
    * top["veh_min_lost"].clip(lower=0)
    * top["severity_score"].clip(lower=0.1)
)
top["rank"] = top["impact_weighted_rank"].rank(ascending=False).astype(int)
top.sort_values("rank", inplace=True)
top["coverage_radius_km"] = PATROL_RADIUS_KM
top["coverage_area_km2"]  = PATROL_AREA_KM2

print("Top 5 impact zones:")
print(top[["rank","h3_cell","eta_ratio","V_calibrated","delay_ratio",
           "veh_min_lost","rupees_lost"]].head(5).to_string(index=False))

# ── Step 5: Merge to full hotspot table ───────────────────────────────────────
print("\n[5/5] Merging and saving...")
bpr_cols = ["h3_cell","poi_demand","lanes","v0_kmh","road_class","eta_ratio",
            "T_freeflow_s","distance_m","V_calibrated","vc_calibrated","C",
            "delay_ratio","veh_min_lost","rupees_lost","C_io",
            "impact_weighted_rank","rank","coverage_radius_km","coverage_area_km2"]

# Start from hotspots (has police_station)
final = hotspots.copy()
for col in [c for c in bpr_cols if c != "h3_cell"]:
    if col in final.columns: final.drop(columns=[col], inplace=True)

final = final.merge(top[bpr_cols], on="h3_cell", how="left")
for col in [c for c in bpr_cols if c != "h3_cell"]:
    if col in final.columns: final[col] = final[col].fillna(0)

# Add police_station from violations if missing
if "police_station" not in final.columns or final["police_station"].isna().all():
    final = final.merge(ps_map, on="h3_cell", how="left")
    final["police_station"] = final["police_station"].fillna("Unknown")

# Contract 2 check
contract2 = ["h3_cell","lat","lon","police_station","risk_debiased","blindspot_flag",
             "poi_demand","severity_score","exposure","peak_dow","V_calibrated",
             "delay_ratio","veh_min_lost","rupees_lost","deterrence_effect","impact_weighted_rank"]
missing = [c for c in contract2 if c not in final.columns]
if missing: print(f"WARNING Contract 2 missing: {missing}")
else:        print("Contract 2: all columns present")

final.to_csv(OUT_DIR/"hotspots_enriched_FINAL.csv", index=False)
print(f"Saved hotspots_enriched_FINAL.csv — {final.shape}")

# ── VRP deployment ────────────────────────────────────────────────────────────
# drop police_station from top if it exists from a previous merge
if "police_station" in top.columns:
    top.drop(columns=["police_station"], inplace=True)
tz_ps = top.merge(ps_map, on="h3_cell", how="left")
tz_ps["police_station"] = tz_ps["police_station"].fillna("Unknown")

plan = []
for station, grp in tz_ps.groupby("police_station"):
    for i, (_, z) in enumerate(
        grp.sort_values("impact_weighted_rank", ascending=False)
           .head(OFFICERS_PER_STATION).iterrows()):
        plan.append({
            "police_station":       station,
            "officer_slot":         i+1,
            "h3_cell":              z["h3_cell"],
            "lat":                  z["lat"],
            "lon":                  z["lon"],
            "blindspot_flag":       int(z["blindspot_flag"]),
            "poi_demand":           int(z.get("poi_demand",0)),
            "impact_weighted_rank": z.get("impact_weighted_rank",0),
            "veh_min_lost":         z.get("veh_min_lost",0),
            "rupees_lost":          z.get("rupees_lost",0),
            "severity_score":       z["severity_score"],
            "peak_dow":             int(z["peak_dow"]),
            "coverage_area_km2":    PATROL_AREA_KM2,
        })

deploy_df     = pd.DataFrame(plan)
fairness_gini = gini(deploy_df.groupby("police_station")["veh_min_lost"].sum().values)

routing_out = {
    "fairness_gini":        fairness_gini,
    "officers_per_station": OFFICERS_PER_STATION,
    "coverage_method":      "haversine_15min",
    "coverage_radius_km":   PATROL_RADIUS_KM,
    "plan":                 deploy_df.to_dict(orient="records"),
}
deploy_df.to_csv(OUT_DIR/"routing_plan.csv", index=False)
with open(OUT_DIR/"routing_plan.json","w") as f:
    json.dump(routing_out, f, indent=2)

print(f"Saved routing_plan — Gini:{fairness_gini:.3f} Stations:{deploy_df['police_station'].nunique()} Assignments:{len(deploy_df)}")

# ── impact_bpr.py for Member C ────────────────────────────────────────────────
module = (
    "# impact_bpr.py — Member B -> Member C\n"
    "ALPHA=3.59; BETA=0.40; SAT_FLOW=1800; VOT_RS_PER_MIN=3.0\n"
    "FOOTPRINT_C_IO={0.5:0.10,1.0:0.25,1.5:0.40,2.0:0.60,3.0:1.00}\n"
    "ROAD_CLASS_VC={'arterial':0.60,'collector':0.45,'local':0.35,'unknown':0.45}\n"
    "_registry={}\n\n"
    "def load_segments(path):\n"
    "    import pandas as pd; global _registry\n"
    "    df=pd.read_csv(path)\n"
    "    for _,r in df.iterrows():\n"
    "        C=r.get('lanes',2)*SAT_FLOW\n"
    "        _registry[r['h3_cell']]={\n"
    "            'lanes':int(r.get('lanes',2)),\n"
    "            'v0_kmh':float(r.get('v0_kmh',40)),\n"
    "            'V_calibrated':float(r.get('V_calibrated',\n"
    "                ROAD_CLASS_VC.get(r.get('road_class','unknown'),0.45)*C)),\n"
    "            'road_class':str(r.get('road_class','unknown'))}\n"
    "    print(f'Loaded {len(_registry)} segments')\n\n"
    "def recompute(segment_id, c_io):\n"
    "    seg=_registry.get(segment_id,{'lanes':2,'v0_kmh':40,'V_calibrated':1080,'road_class':'unknown'})\n"
    "    C=seg['lanes']*SAT_FLOW; V=seg['V_calibrated']\n"
    "    C_eff=max(C-c_io,0.1*C); T0=(0.5/seg['v0_kmh'])*60\n"
    "    Tw=T0*(1+ALPHA*(V/C_eff)**BETA); Two=T0*(1+ALPHA*(V/C)**BETA)\n"
    "    dr=Tw/Two if Two>0 else 1.0; vml=(Tw-Two)*V*8\n"
    "    return {'T_a_with':round(Tw,4),'T_a_without':round(Two,4),\n"
    "            'delay_ratio':round(dr,4),'veh_min_lost':round(vml,1),\n"
    "            'rupees_lost':round(vml*VOT_RS_PER_MIN,0)}\n"
)
with open(OUT_DIR/"impact_bpr.py","w") as f:
    f.write(module)

# ── Final summary ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("MEMBER B DELIVERABLES")
print("="*60)
for fname in ["hotspots_enriched_FINAL.csv","routing_plan.csv",
              "routing_plan.json","mappls_cache.json","impact_bpr.py"]:
    path = OUT_DIR/fname
    size = path.stat().st_size/1024 if path.exists() else 0
    print(f"  {'OK' if size>0 else 'MISSING'}  {fname:35s}  {size:.1f} KB")

print()
print("TOP 5 IMPACT ZONES:")
print(top[["rank","h3_cell","eta_ratio","V_calibrated","delay_ratio",
           "veh_min_lost","rupees_lost","poi_demand"]].head(5).to_string(index=False))
print()
print(f"eta_ratio range:    {top['eta_ratio'].min():.3f} – {top['eta_ratio'].max():.3f}")
print(f"V_calibrated range: {top['V_calibrated'].min():.0f} – {top['V_calibrated'].max():.0f}")
print(f"Fairness Gini:      {fairness_gini:.3f}")
print(f"Cache entries:      {len(CACHE)}")
print()
print("CITATIONS:")
print("  MBPR: Gore et al. (2023) TRR 2677(5):966-990")
print("  Constants: Anwar et al. (2011) Dhaka alpha=3.59 beta=0.40")
print("  V: Mappls Distance Matrix typical/freeflow ETA back-solve")
print("  Road class: Snap-to-Road + Directions speed inference")
print()
print("MEMBER C:")
print("  import impact_bpr")
print("  impact_bpr.load_segments('hotspots_enriched_FINAL.csv')")
print("  result = impact_bpr.recompute('<h3_cell>', c_io=450)")
