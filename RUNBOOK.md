# PARKLENS — Member C integration runbook (B → C swap)

## Who fixes what (so you don't do B's work)

| # | Blocker | Owner | Effort | Re-upload? |
|---|---------|-------|--------|-----------|
| 1 | `impact_bpr.py` / `mappls_client.py` are 0 bytes (real code in `__1_`) | upload artifact | trivial | **No** — already fixed in this bundle |
| 2 | `mappls_client` SyntaxError (line 16) | B's code | 1 line | No — fixed here for you |
| 3 | `recompute()` returns `T_a_with`, not `T_a` | C adapter | done | No |
| 4 | `route_geometry()` signature / no segment_attrs | C adapter | done | No |
| 5 | `recompute` keyed by `h3_cell` + needs `load_segments()` | C adapter | done | No |
| 6 | only 100/2534 cells enriched | **B (optional)** | only if you need a specific corridor | No |
| 7 | `impact_weighted_rank` is a score, not 1..N rank | C loader | done | No |
| – | leaked Mappls key in source | **B (tell them)** | rotate key | No |

**Bottom line:** every C-side fix is already done in this bundle. The only things
to *raise with B* are optional: (a) enrich the few extra cells if your chosen demo
corridor isn't in the top 100, and (b) rotate the API key that was committed.

## What I changed for you
- `src/impact_bpr.py`  — B's real engine, renamed from `__1_` (logic untouched).
- `src/mappls_client.py` — B's client, **syntax fixed** + key moved to `MAPPLS_KEY` env.
- `src/config.py` — points at `hotspots_enriched.csv`; `USE_REAL_B = True`; ₹3/min + 8h to match B.
- `src/bdeps.py` — calls `load_segments()` once; adds the `T_a` alias over B's `T_a_with`.
- `src/graph.py` — real mode builds the corridor from enriched cells (segment id = h3_cell).
- `src/twin.py` — uses B's real `C_io` as the capacity input.
- `src/loader.py` — reads enriched table, flips rank to score-descending, drops unscored zeros.
- `src/api.py` — sanitizes numpy/NaN; `/hotspots` ranks by B's score.

## Run it
```bash
pip install -r requirements.txt
cd src && python twin.py            # prints a real-engine what-if
uvicorn api:app --reload            # http://127.0.0.1:8000/docs
streamlit run ../app/dashboard.py
```
Verified real-mode result: clearing the top cell → **1,666 veh-min / ₹4,997 saved**,
matching B's published `veh_min_lost` (1,664.7) for that cell.

## If you DO need to re-upload (upload tips)
You don't, for this bundle. But if you re-pull B's files later and see `__1_`
suffixes again, that's the dedupe artifact — just save them as the plain names
(`impact_bpr.py`, `mappls_client.py`) into `src/`, then re-apply the one-line
syntax fix to `mappls_client` (or copy this bundle's fixed copy).

## Two honest caveats for the demo
1. The enriched table has **no `police_station`** column (only `routing_plan.json`
   does), so the real-mode corridor is the top-12 enriched cells chained by
   proximity — they're city-wide, not one literal road. For a believable corridor,
   hand-pick 4–6 enriched cells on one stretch, or ask B to tag a `corridor_id`.
2. `/deploy` and the dashboard Deploy tab still use the impact-ranked fallback.
   To show B's real fairness-scored plan, drop `routing_plan.json` into `data/`
   and read it there (it has `police_station`, `officer_slot`, `fairness_gini`).

---

## All six next-steps — status (done in this bundle)
1. ✅ **Corridor** — hand-picked 6 adjacent enriched cells (~2.8 km W-Bengaluru
   arterial, anchored by a 1,665 veh-min cell) in `config.CORRIDOR_CELLS`.
2. ✅ **Deploy tab → routing** — `src/routing.py` loads B's `routing_plan.json`
   if present, else a derived fallback. **Drop `routing_plan.json` into `data/`**
   to show B's real station-zoned, Gini-0.60 plan.
3. ✅ **Animated twin** — `dashboard.py` embeds an SVG/JS component; "Clear the
   hotspot" animates the corridor and ticks the ₹ / veh-min counters.
4. ✅ **Basemap + narrative** — sidebar accepts a Mappls tile URL and shows
   narrative/engine status. Set `MAPPLS_TILE_URL` (config) and `ANTHROPIC_API_KEY`
   (env) to go fully live; both degrade gracefully.
5. ✅ **Demand-anchored blind spots** — `loader.demand_anchored()` (53 cells);
   the map highlights blind spots that also have high Mappls POI demand.
6. ✅ **Demo script + deck** — `docs/demo_script.md` (90-sec walkthrough) and
   `docs/PARKLENS_deck.pptx` (9 slides). Rebuild the deck with
   `node docs/build_deck.js` (needs `npm i -g pptxgenjs`).

### One manual step remaining
Drop B's `routing_plan.json` into `data/` for the real fairness-scored Deploy
plan (everything else runs as-is).
