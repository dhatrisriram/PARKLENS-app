# PARKLENS — 90-second demo script

**Setup before you start:** dashboard running, on the **Blind spots** tab, sidebar
showing "Impact engine: 🟢 B real". Have the corridor anchor cell handy
(`8960145a01bffff`).

---

**[0:00–0:15] The hook — the blind-spot problem**
> "Bengaluru wrote 298,000 parking-violation tickets in five months. But
> enforcement goes where enforcement already goes. So we asked: where are the
> hotspots the data *can't* see?"

Point at the **Blind spots** map. The red dots are *demand-anchored shadow
hotspots* — high true risk, low patrol, and high nearby POI demand from Mappls.
> "53 of these. High risk, barely patrolled, and Mappls confirms there's real
> demand pulling cars in. The raw heatmap shows them as clean."

**[0:15–0:35] We de-biased the risk**
> "We don't just count tickets — that measures *enforcement*, not *violations*.
> A Poisson model with a patrol-exposure offset recovers the true risk, and we
> anchor it to Mappls POI demand so a blind spot is credible, not a modelling
> artifact."

**[0:35–0:50] Impact — in rupees, calibrated by Mappls**
Switch to **Impact** tab.
> "We turn risk into cost. A modified-BPR engine, with volume *calibrated from
> Mappls live ETAs*, gives vehicle-minutes lost and rupees per hotspot. The top
> cell alone burns 1,665 vehicle-minutes a peak window."

**[0:50–1:15] The what-if twin — the showpiece**
Switch to **What-if twin**, corridor already selected, anchor cell chosen.
> "Here's a real arterial. Watch what happens when we clear the worst hotspot."

Click **▶ Clear the hotspot**. Let the counter tick to ₹4,997 / 1,666 veh-min.
> "One cell, cleared: ~1,666 vehicle-minutes back, nearly 5,000 rupees a window —
> and that number comes straight from B's Mappls-calibrated engine, not a guess."

**[1:15–1:30] From insight to action — fairly**
Switch to **Deploy**.
> "Finally we route officers to the highest-impact cells with a fairness
> constraint — Gini 0.60 — so enforcement isn't dumped on one ward. Blind spots
> found, cost quantified, officers deployed. That's PARKLENS."

---

## If asked (have ready)
- **"Did you assume the traffic volume?"** → No — back-solved from Mappls
  typical-vs-freeflow ETA per segment, then added the illegal-occupancy share.
- **"Does enforcement actually help?"** → Zone-month difference-in-differences on
  five clean months shows enforced zones drop in subsequent violations; we report
  it with an honest identification caveat (treated zones start highest).
- **"Why H3?"** → Equal-area hexagons, no MAU bias, clean POI/Mappls joins.
- **Failure modes covered:** narrative falls back to static text; twin has a
  pre-rendered clip; impact degrades to risk×severity if the engine is down.
