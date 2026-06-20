"""app/dashboard.py — PARKLENS dashboard (Member C product surface).

Panels: blind-spot map (P1, demand-anchored) · impact (P2) · animated what-if
twin (P4) · fair deployment (P-ROI).  Run: streamlit run app/dashboard.py
"""
from __future__ import annotations
import json
import os
import sys

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

# Make src/, the project root, and this app/ dir importable so the flat import
# style resolves no matter where streamlit is launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (os.path.join(_ROOT, "src"), _ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import config            # noqa: E402
import loader            # noqa: E402
import routing           # noqa: E402
from twin import Twin    # noqa: E402
from narrative import why_this_zone  # noqa: E402

st.set_page_config(page_title="PARKLENS", layout="wide")


@st.cache_resource
def get_twin() -> Twin:
    return Twin()


@st.cache_data
def get_hotspots() -> pd.DataFrame:
    return loader.load_hotspots()


def basemap(center, zoom=12, tile_url=None) -> folium.Map:
    url = tile_url or config.MAPPLS_TILE_URL
    if url:
        m = folium.Map(location=center, zoom_start=zoom, tiles=None)
        folium.TileLayer(url, attr=config.MAPPLS_TILE_ATTR, name="Mappls").add_to(m)
    else:
        m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")
    return m


def twin_animation(res: dict) -> str:
    """Self-contained SVG/JS that animates the corridor recovering."""
    payload = {
        "segments": [{"label": s["seg_id"].split("::")[-1][:8],
                      "with": s["min_with"], "without": s["min_without"]}
                     for s in res["per_segment"]],
        "with_total": res["corridor_min_with"],
        "without_total": res["corridor_min_without"],
        "veh_min": res["veh_min_saved"], "rupees": res["rupees_saved"],
        "recovery": res["recovery_pct"],
    }
    tpl = r"""
<div style="font-family:system-ui;color:#e6edf3">
  <div style="display:flex;gap:24px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
    <button id="play" style="background:#2a9d8f;color:#fff;border:0;padding:8px 16px;
      border-radius:8px;font-weight:600;cursor:pointer">&#9654; Clear the hotspot</button>
    <div>Corridor: <b><span id="tot">0</span> min</b></div>
    <div>Recovered: <b style="color:#2a9d8f"><span id="rec">0</span>%</b></div>
    <div>Saved: <b style="color:#2a9d8f">&#8377;<span id="rs">0</span></b>
         (<span id="vm">0</span> veh-min)</div>
  </div>
  <svg id="cv" viewBox="0 0 720 220" style="width:100%;height:220px"></svg>
</div>
<script>
const D = __DATA__;
const svg = document.getElementById("cv");
const W=720,H=220,pad=30, n=D.segments.length;
const bw = (W-2*pad)/n - 12;
const maxv = Math.max(...D.segments.map(s=>Math.max(s.with,s.without)))*1.15 || 1;
const y = v => H-40 - (v/maxv)*(H-70);
const col = v => { const t=Math.min(v/maxv,1);
  const r=Math.round(42+(215-42)*t), g=Math.round(157-(157-38)*t), b=Math.round(143-(143-61)*t);
  return "rgb("+r+","+g+","+b+")"; };
let bars=[];
D.segments.forEach((s,i)=>{
  const x = pad + i*((W-2*pad)/n) + 6;
  const rect=document.createElementNS("http://www.w3.org/2000/svg","rect");
  rect.setAttribute("x",x); rect.setAttribute("width",bw); rect.setAttribute("rx",4);
  svg.appendChild(rect); bars.push(rect);
  const t=document.createElementNS("http://www.w3.org/2000/svg","text");
  t.setAttribute("x",x+bw/2); t.setAttribute("y",H-18); t.setAttribute("fill","#8b949e");
  t.setAttribute("font-size","10"); t.setAttribute("text-anchor","middle");
  t.textContent=s.label; svg.appendChild(t);
});
function draw(p){
  let tot=0;
  D.segments.forEach((s,i)=>{
    const v=s.with+(s.without-s.with)*p; tot+=v;
    bars[i].setAttribute("y",y(v)); bars[i].setAttribute("height",(H-40)-y(v));
    bars[i].setAttribute("fill",col(v));
  });
  document.getElementById("tot").textContent=tot.toFixed(1);
  document.getElementById("rec").textContent=(D.recovery*p).toFixed(1);
  document.getElementById("rs").textContent=Math.round(D.rupees*p).toLocaleString();
  document.getElementById("vm").textContent=Math.round(D.veh_min*p).toLocaleString();
}
draw(0);
document.getElementById("play").onclick=()=>{
  let t0=null; const dur=1400;
  function step(ts){ if(!t0)t0=ts; const p=Math.min((ts-t0)/dur,1);
    const e=(1-Math.cos(p*Math.PI))/2; draw(e);
    if(p<1) requestAnimationFrame(step); }
  requestAnimationFrame(step);
};
</script>"""
    return tpl.replace("__DATA__", json.dumps(payload))


df = get_hotspots()
CENTER = [df["lat"].mean(), df["lon"].mean()]

st.sidebar.title("PARKLENS settings")
tile_url = st.sidebar.text_input("Mappls raster tile URL (optional)",
                                 value=config.MAPPLS_TILE_URL or "")
st.sidebar.caption("Leave blank for a neutral Carto basemap.")
st.sidebar.markdown("**Narrative:** " + (
    "\U0001F7E2 Claude live" if os.getenv("ANTHROPIC_API_KEY")
    else "\u26AA static fallback (set ANTHROPIC_API_KEY)"))
st.sidebar.markdown("**Impact engine:** " + (
    "\U0001F7E2 B real" if loader.b_impact_ready() else "\U0001F7E1 A-only fallback"))

st.title("\U0001F17F\uFE0F PARKLENS \u2014 Parking-induced congestion intelligence")
tab1, tab2, tab3, tab4 = st.tabs(
    ["Blind spots", "Impact", "What-if twin", "Deploy"])

with tab1:
    st.subheader("De-biased true-risk map \u2014 demand-anchored shadow hotspots")
    anchored = loader.demand_anchored()
    c1, c2 = st.columns([3, 1])
    c2.metric("Blind-spot cells", int(df["blindspot_flag"].sum()))
    c2.metric("Demand-anchored", len(anchored))
    c2.caption("Demand-anchored = blind spot **and** high nearby POI demand "
               "(Mappls). These are the credible ones.")
    m = basemap(CENTER, tile_url=tile_url or None)
    anchored_ids = set(anchored["zone_id"])
    view = df[df["blindspot_flag"] == 1]
    rmax = max(view["risk_debiased"].max(), 1e-9)
    for _, r in view.iterrows():
        anc = r["zone_id"] in anchored_ids
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=5 + 9 * (r["risk_debiased"] / rmax),
            color="#d7263d" if anc else "#5a8bb0",
            fill=True, fill_opacity=0.75 if anc else 0.4, weight=2 if anc else 1,
            tooltip=(f"{r['zone_id']}<br>risk={r['risk_debiased']:.4f}"
                     f"<br>POI demand={int(r.get('poi_demand',0) or 0)}"
                     f"{'<br>DEMAND-ANCHORED' if anc else ''}"),
        ).add_to(m)
    with c1:
        st_folium(m, height=520, use_container_width=True)
    st.caption("Red = demand-anchored shadow hotspot (high risk, low patrol, high "
               "POI demand). Faded blue = blind spot without a demand signal yet.")

with tab2:
    st.subheader("Congestion cost per hotspot")
    top = loader.top_by_impact(15)
    st.dataframe(top[["zone_id", "risk_debiased", "severity_score",
                      "veh_min_lost", "rupees_lost", "impact_weighted_rank"]],
                 use_container_width=True, hide_index=True)
    fig = go.Figure(go.Bar(x=top["zone_id"].astype(str),
                           y=pd.to_numeric(top["veh_min_lost"], errors="coerce"),
                           marker_color="#1b6ca8"))
    fig.update_layout(title="Vehicle-minutes lost (peak window)",
                      xaxis_title="zone", yaxis_title="veh-min", height=340)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader(f"What-if twin \u2014 corridor {config.CORRIDOR_ID}")
    twin = get_twin()
    on_corridor = [z for s in twin.corridor.segments for z in s.hotspots]
    if not on_corridor:
        st.warning("No hotspots mapped to the corridor.")
    else:
        zone = st.selectbox("Clear which hotspot?", on_corridor)
        res = twin.compare(zone)
        components.html(twin_animation(res), height=300)
        st.info(why_this_zone(loader.get_zone(zone)))

with tab4:
    st.subheader("Fair routed deployment")
    plan = routing.get_plan(officers_per_station=3)
    a, b = st.columns(2)
    a.metric("Fairness (Gini)", f"{plan['fairness_gini']:.3f}"
             if plan['fairness_gini'] is not None else "\u2014")
    b.metric("Source", "B real plan" if plan["source"] == "B-real"
             else "derived fallback")
    if plan["source"] != "B-real":
        st.caption("Drop B's `routing_plan.json` into `data/` for the real "
                   "station-zoned, fairness-scored plan.")
    pf = routing.as_frame(plan)
    show = [c for c in ["police_station", "officer_slot", "h3_cell", "poi_demand",
                        "veh_min_lost", "rupees_lost", "impact_weighted_rank"]
            if c in pf.columns]
    st.dataframe(pf[show], use_container_width=True, hide_index=True)
