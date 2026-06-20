# PARKLENS — Member C (Twin · API · Dashboard)

Day-0 scaffold for the **what-if twin + FastAPI + Streamlit** vertical. Runs
**today** on Member A's real `hotspots.csv` and on stubs for Member B's two
functions, so nothing blocks you. The swap to real Mappls geometry + the real
MBPR engine is **three one-line changes** (below).

## Layout
```
src/
  config.py      paths, BPR constants, the USE_REAL_B swap flag
  bdeps.py       the single seam: stubs  ↔  B's real modules
  stubs.py       Day-0 stand-ins for B's recompute() + route_geometry() (Contract 5)
  loader.py      reads hotspots.csv, maps to Contract-2 names, fallback for B's cols
  graph.py       NetworkX corridor from route_geometry(); maps hotspots → segments
  twin.py        propagation engine: clear a hotspot → recompute → WITH/WITHOUT
  api.py         FastAPI — /hotspots /risk /impact /deploy /whatif (Contract 4)
app/
  dashboard.py   Streamlit: blind-spot map · impact · twin · deploy
  narrative.py   Claude "why this zone" (claude-sonnet-4-6) + static fallback
data/
  hotspots.csv   A's real output (already seeded)
```

## Run
```bash
pip install -r requirements.txt

# API
cd src && uvicorn api:app --reload          # http://127.0.0.1:8000/docs

# Dashboard
streamlit run app/dashboard.py

# Smoke-test the twin alone
cd src && python twin.py
```

## The 3 drop-in swaps (Checkpoint ③)
1. **B's engine:** set `USE_REAL_B = True` in `src/config.py`. `bdeps.py` then
   imports B's `impact_bpr.recompute` and `mappls_client.route_geometry`; nothing
   in `graph.py`/`twin.py` changes (same signatures — Contract 5).
2. **Real impact columns:** once B writes `veh_min_lost`, `rupees_lost`,
   `delay_ratio`, `V_calibrated`, `impact_weighted_rank` into `hotspots.csv`,
   `loader.py` uses them automatically and the dashboard's fallback banner
   disappears. `twin._c_io_for()` also starts using B's `veh_min_lost`.
3. **Real deployment:** replace the `/deploy` fallback in `api.py` and the
   Deploy tab with B's `routing.py` output (VRP + Isopolygon + Gini fairness).

## Mappls basemap
Set `MAPPLS_TILE_URL` (+ key) in `config.py` for the on-brand basemap. Until then
the map uses a neutral Carto basemap (not OSM-branded — stays within the no-OSM
constraint).

## Honesty notes baked in (so the demo doesn't overclaim)
- `poi_demand` is still A's stub (all 0) → the blind-spot panel currently flags on
  risk + exposure only. The "demand-anchored" story lands when B fills POI and A
  re-derives the flag.
- Impact numbers are the `risk × severity` fallback until swap #2.
- `narrative.py` degrades to template text if `ANTHROPIC_API_KEY` is unset.
- The mock corridor clusters scattered city-wide hotspots onto a few segments;
  `twin._MAX_CIO_FRAC` clamps c_io so BPR stays believable until real geometry.
