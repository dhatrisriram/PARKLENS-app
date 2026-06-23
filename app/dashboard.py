"""app/dashboard.py — PARKLENS, redesigned for anyone to understand.

A guided, plain-English story: the problem -> find hidden hotspots -> price the
congestion -> simulate a fix -> deploy officers. Run: streamlit run app/dashboard.py
"""
from __future__ import annotations
import json, os, sys
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

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

st.set_page_config(page_title="PARKLENS", page_icon="🅿️", layout="wide")

NAVY="#0E2A47"; NAVY2="#173A5E"; AMBER="#F4A300"; TEAL="#1f9e78"
RED="#D7263D"; INK="#1E293B"; SLATE="#64748B"; MIST="#EEF3F8"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family:'Inter',system-ui,sans-serif; }
.stApp, .main, [data-testid="stAppViewContainer"] { background:#F7F9FC !important; }
[data-testid="stHeader"] { background:transparent; }
#MainMenu, header, footer {visibility:hidden;}
.block-container {padding-top:1.2rem; max-width:1150px;}
.hero{background:linear-gradient(135deg,#0E2A47 0%,#173A5E 100%);border-radius:20px;
  padding:34px 40px;color:#fff;margin-bottom:8px;}
.hero h1{font-size:46px;font-weight:800;margin:0;letter-spacing:-1px;}
.hero p{font-size:19px;color:#CADCFC;margin:6px 0 22px;max-width:780px;}
.chips{display:flex;gap:14px;flex-wrap:wrap;}
.chip{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);
  border-radius:14px;padding:12px 18px;min-width:150px;}
.chip .n{font-size:28px;font-weight:800;color:#F4A300;line-height:1;}
.chip .l{font-size:13px;color:#9DB4CE;margin-top:5px;}
.steps{display:flex;gap:10px;margin:22px 0 6px;}
.step{flex:1;background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:14px 16px;}
.step .k{font-size:12px;font-weight:700;color:#94A3B8;}
.step .t{font-size:16px;font-weight:700;color:#0E2A47;margin-top:2px;}
.step .d{font-size:13px;color:#64748B;margin-top:3px;line-height:1.35;}
.step.show{background:#0E2A47;border-color:#0E2A47;}
.step.show .k{color:#F4A300;} .step.show .t{color:#fff;} .step.show .d{color:#CADCFC;}
.sec{display:flex;align-items:center;gap:14px;margin:34px 0 4px;}
.badge{width:40px;height:40px;border-radius:50%;background:#0E2A47;color:#F4A300;
  font-weight:800;font-size:18px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.sec h2{font-size:27px;font-weight:800;color:#1E293B;margin:0;}
.plain{background:#F0FaF6;border-radius:12px;padding:13px 18px;margin:10px 0 16px;
  font-size:15.5px;color:#0f5132;line-height:1.5;}
.plain b{color:#0b3d27;}
.legend{display:flex;gap:22px;font-size:14px;color:#475569;margin-top:8px;align-items:center;}
.dot{display:inline-block;width:13px;height:13px;border-radius:50%;margin-right:7px;vertical-align:-1px;}
.big{font-size:54px;font-weight:800;color:#0E2A47;line-height:1;}
.bigsub{font-size:16px;color:#475569;margin-top:6px;}
.take{background:#FFF7E6;border-radius:12px;padding:13px 18px;margin-top:14px;
  font-size:15.5px;color:#7a4d00;}
.foot{color:#64748B;font-size:13px;margin:40px 0 10px;text-align:center;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_twin(): return Twin()
@st.cache_data
def get_hotspots(): return loader.load_hotspots()
@st.cache_data
def get_stats():
    p = config.DATA_DIR / "summary_stats.json"
    return json.loads(p.read_text()) if p.exists() else {}

df = get_hotspots()
stats = get_stats()
en = loader.enriched_only()
vm_total = int(pd.to_numeric(en["veh_min_lost"], errors="coerce").fillna(0).sum())
rs_total = int(pd.to_numeric(en["rupees_lost"], errors="coerce").fillna(0).sum())
anchored = loader.demand_anchored()

def loc(lat, lon):
    return f"{lat:.3f}\u00b0N, {lon:.3f}\u00b0E"

def section(num, title, plain):
    st.markdown(f"<div class='sec'><div class='badge'>{num}</div><h2>{title}</h2></div>"
                f"<div class='plain'>{plain}</div>", unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <h1>🅿️ PARKLENS</h1>
  <p>Bad parking quietly chokes Bengaluru's traffic. PARKLENS finds the worst
     spots — even the ones nobody is watching — shows what they cost, and lets
     you test a fix before sending a single officer.</p>
  <div class="chips">
    <div class="chip"><div class="n">{stats.get('total_violations',298130):,}</div><div class="l">parking violations studied</div></div>
    <div class="chip"><div class="n">{len(anchored)}</div><div class="l">hidden hotspots found</div></div>
    <div class="chip"><div class="n">₹{rs_total:,}</div><div class="l">wasted every peak hour*</div></div>
    <div class="chip"><div class="n">{vm_total:,}</div><div class="l">vehicle-minutes lost*</div></div>
  </div>
</div>
<div style="color:#94A3B8;font-size:12px;margin:2px 0 0">*across the 100 worst spots, per peak hour</div>
""", unsafe_allow_html=True)

# ── HOW IT WORKS STRIP ───────────────────────────────────────────────────────
st.markdown("""
<div class="steps">
  <div class="step"><div class="k">STEP 1</div><div class="t">Find</div><div class="d">Spot the hidden trouble zones</div></div>
  <div class="step"><div class="k">STEP 2</div><div class="t">Price</div><div class="d">Turn delay into rupees</div></div>
  <div class="step show"><div class="k">STEP 3</div><div class="t">Simulate</div><div class="d">Clear a spot, watch traffic recover</div></div>
  <div class="step"><div class="k">STEP 4</div><div class="t">Act</div><div class="d">Send officers where it helps most</div></div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### PARKLENS")
    st.caption("A guided tour — just scroll down.")
    st.markdown("**Data:** " + ("🟢 live (real engine)" if loader.b_impact_ready()
                                 else "🟡 sample mode"))
    st.session_state["tile"] = st.text_input("Mappls map tiles (optional)",
                                              value=config.MAPPLS_TILE_URL or "")
    st.divider()

    # ========== METHODOLOGY EXPANDER (NEW) ==========
    with st.expander("🛠️ Methodology & Data Flow", expanded=False):
        st.markdown("""
        **Data Lineage**
        * **Base Data:** Bengaluru Traffic Police Jan–May violations (298,450 rows)
        * **Live Enrichment (Mappls APIs):**
            * *Snap‑to‑Road & Directions* → road class, lanes, free‑flow speed
            * *Distance Matrix / Predictive‑ETA* → back‑solve for traffic volume \(V\)
            * *Nearby POI & GeoAnalytics* → demand anchoring for blind spots

        **Core Models**
        """)

        # All LaTeX strings are raw to avoid escape warnings
        st.latex(r"T_a = T_0 \left[ 1 + 3.59 \left(\frac{V}{C - C_{io}}\right)^{0.40} \right]")
        st.markdown("*Modified‑BPR (Gore et al., 2023) — α=3.59, β=0.40 (Dhaka calibration, Anwar et al.)*")

        st.latex(r"\log(\lambda) = \beta_0 + \beta_1 \cdot \text{POI} + \beta_2 \cdot \text{road} + \log(\text{exposure})")
        st.markdown("*Poisson regression with exposure offset for de‑biased risk*")

        st.latex(r"\text{score} = \text{risk} \times \text{vehMin} \times \text{severity}")
        st.markdown("*Impact‑weighted deployment rank*")

        st.latex(r"G = \frac{\sum_i \sum_j |x_i - x_j|}{2n \sum_i x_i}")
        st.markdown("*Gini coefficient (0 = perfect equality)*")

        st.markdown("""
        **References**
        * Gore, Arkatkar, Joshi & Antoniou (2023), *Transp. Res. Rec.* 2677(5)
        * Anwar, Fujiwara & Zhang (2011) – Dhaka calibration constants
        * IISc–BTP CiSTUP MoU (Dec 2023) – enforcement context
        * Mappls API docs: https://about.mappls.com/api/
        """)
    # ========== END NEW SECTION ==========

# ── 1 · FIND ─────────────────────────────────────────────────────────────────
section(1, "Where are the hidden hotspots?",
        "A normal map only shows where police already write tickets. We correct "
        "for that and add real footfall data from maps, so a spot counts as a "
        "<b>hidden hotspot</b> only if it's genuinely busy <b>and</b> rarely "
        "patrolled. The red dots are the ones to worry about.")
c1, c2 = st.columns([3, 1])
center = [df["lat"].mean(), df["lon"].mean()]
tile = st.session_state.get("tile") or config.MAPPLS_TILE_URL
m = (folium.Map(location=center, zoom_start=12, tiles=None) if tile
     else folium.Map(location=center, zoom_start=12, tiles="CartoDB positron"))
if tile: folium.TileLayer(tile, attr="Mappls", name="Mappls").add_to(m)
aset = set(anchored["zone_id"])
view = df[df["blindspot_flag"] == 1]
rmax = max(view["risk_debiased"].max(), 1e-9)
for _, r in view.iterrows():
    anc = r["zone_id"] in aset
    folium.CircleMarker([r["lat"], r["lon"]],
        radius=5 + 9*(r["risk_debiased"]/rmax),
        color=RED if anc else "#7Fa6c4", fill=True,
        fill_opacity=0.8 if anc else 0.35, weight=2 if anc else 1,
        tooltip=("Hidden hotspot" if anc else "Known hotspot")
                + f" · busyness {int(r.get('poi_demand',0) or 0)}").add_to(m)
with c1:
    st_folium(m, height=460, use_container_width=True)
    st.markdown(f"<div class='legend'>"
                f"<span><span class='dot' style='background:{RED}'></span>Hidden hotspot — busy but rarely patrolled</span>"
                f"<span><span class='dot' style='background:#7Fa6c4'></span>Already-known hotspot</span></div>",
                unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='big'>{len(anchored)}</div>"
                f"<div class='bigsub'>hidden hotspots the usual maps miss</div>",
                unsafe_allow_html=True)
    st.markdown(f"<div class='big' style='margin-top:18px'>{int(df['blindspot_flag'].sum())}</div>"
                f"<div class='bigsub'>under-watched zones in total</div>", unsafe_allow_html=True)

# ── 2 · PRICE ────────────────────────────────────────────────────────────────
section(2, "What is all this costing us?",
        "Every blocked lane slows cars behind it. Using live traffic speeds from "
        "maps, we turn each hotspot into something a non-expert understands: "
        "<b>minutes of driver time lost</b> and <b>rupees wasted</b>.")
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown(f"<div class='big'>₹{rs_total:,}</div>"
                f"<div class='bigsub'>wasted in driver time every peak hour, "
                f"across the 100 worst spots</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='big' style='margin-top:20px'>{vm_total:,}</div>"
                f"<div class='bigsub'>vehicle-minutes lost in the same window</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='take'>One spot alone — the worst — burns about "
                "<b>1,665 vehicle-minutes</b> (~₹4,994) every peak hour.</div>",
                unsafe_allow_html=True)
with c2:
    sky = en.sort_values("veh_min_lost", ascending=False).reset_index(drop=True)
    yv = pd.to_numeric(sky["veh_min_lost"], errors="coerce").fillna(0)
    colors = [AMBER if i < 20 else NAVY for i in range(len(yv))]
    fig = go.Figure(go.Bar(x=list(range(1, len(yv)+1)), y=yv, marker_color=colors))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=44, b=40),
        title="Every hotspot, worst to least — a few cause most of the delay",
        xaxis_title="hotspots, ranked worst → least bad",
        yaxis_title="vehicle-minutes lost",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(size=12, color=INK), bargap=0.15)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("<div class='take'>The worst <b>20 spots</b> (amber) cause about "
                "<b>70%</b> of all the wasted time — so fixing a handful goes a "
                "long way.</div>", unsafe_allow_html=True)

# ── 3 · SIMULATE (showpiece) ─────────────────────────────────────────────────
section(3, "What if we cleared one hotspot?",
        "This is a live digital twin of a real road. Pick a hotspot and press the "
        "button — the model recomputes the whole road and shows you exactly how "
        "much traffic time and money you'd get back. <b>No guesswork.</b>")
twin = get_twin()
segs = [s for s in twin.corridor.segments if s.hotspots]
if segs:
    cells = [s.hotspots[0] for s in segs]
    coords = [(loader.get_zone(z)["lat"], loader.get_zone(z)["lon"]) for z in cells]
    vmls = [float(loader.get_zone(z).get("veh_min_lost") or 0) for z in cells]
    letters = [chr(65 + i) for i in range(len(cells))]
    big = max(range(len(cells)), key=lambda i: vmls[i])
    opts = [f"Spot {letters[i]}  ({loc(*coords[i])})  —  {int(vmls[i]):,} veh-min"
            + ("   ⬅ biggest" if i == big else "") for i in range(len(cells))]

    st.caption("Tip: most spots on this road are small and roughly equal — the win "
               "is the one big spot. Try the biggest first.")
    pick = st.selectbox("Pick a hotspot on this road, then press Clear:",
                        opts, index=big)
    si = opts.index(pick)
    zone = cells[si]

    cmap, cinfo = st.columns([1.25, 1])
    with cmap:
        ctr = [sum(c[0] for c in coords)/len(coords), sum(c[1] for c in coords)/len(coords)]
        cm = folium.Map(location=ctr, zoom_start=14, tiles="CartoDB positron")
        folium.PolyLine(coords, color="#94A3B8", weight=5, opacity=0.7).add_to(cm)
        for i, (lat, lon) in enumerate(coords):
            on = i == si
            folium.Marker([lat, lon], tooltip=f"Spot {letters[i]} ({loc(lat,lon)})",
                icon=folium.DivIcon(icon_size=(28, 28), icon_anchor=(14, 14),
                  html=(f"<div style='background:{RED if on else NAVY};color:#fff;"
                        f"width:26px;height:26px;border-radius:50%;display:flex;"
                        f"align-items:center;justify-content:center;font-weight:700;"
                        f"font-family:Inter;border:2px solid #fff'>{letters[i]}</div>"))
                ).add_to(cm)
        st_folium(cm, height=300, use_container_width=True)
        st.caption("Each lettered pin is a real hotspot on this stretch — red is the "
                   "one you're clearing. (Production swaps coordinates for street "
                   "names via Mappls.)")
    with cinfo:
        st.markdown(f"<div class='big' style='font-size:40px'>Spot {letters[si]}</div>"
                    f"<div class='bigsub'>{loc(*coords[si])}</div>", unsafe_allow_html=True)
        st.markdown("<div class='bigsub' style='margin-top:10px'>Press <b>Clear this "
                    "hotspot</b> below and watch the whole road recover.</div>",
                    unsafe_allow_html=True)

    res = twin.compare(zone)
    total_vm = sum(vmls) or 1
    saved_vm = int(round(vmls[si]))
    recovery = vmls[si] / total_vm * 100
    rupees = int(res["rupees_saved"])

    def anim(vmls, si, letters, veh_min, rupees, recovery):
        payload = {"segments":[{"label":letters[i],"with":vmls[i],
                    "without":(0 if i==si else vmls[i])} for i in range(len(vmls))],
                   "veh_min":veh_min,"rupees":rupees,"recovery":recovery}
        tpl = r"""
<div style="font-family:Inter,system-ui;color:#1E293B">
  <div style="display:flex;gap:30px;align-items:center;margin:0 0 14px;flex-wrap:wrap">
    <button id="play" style="background:#1f9e78;color:#fff;border:0;padding:12px 22px;
      border-radius:10px;font-weight:700;font-size:16px;cursor:pointer">&#9654;&nbsp; Clear this hotspot</button>
    <div style="font-size:14px;color:#64748B">Time saved<br><b id="vm" style="font-size:26px;color:#1f9e78">0</b> veh-min</div>
    <div style="font-size:14px;color:#64748B">Money saved<br><b id="rs" style="font-size:26px;color:#1f9e78">&#8377;0</b></div>
    <div style="font-size:14px;color:#64748B">This road frees up<br><b id="rec" style="font-size:26px;color:#1f9e78">0%</b></div>
  </div>
  <svg id="cv" viewBox="0 0 720 210" style="width:100%;height:210px"></svg>
  <div style="font-size:13px;color:#64748B;margin-top:4px">Each bar is a hotspot, lettered to match the map. Taller, redder = more time wasted there. The one you clear drops to zero.</div>
</div>
<script>
const D=__DATA__;const svg=document.getElementById("cv");const W=720,H=210,pad=28,n=D.segments.length;
const bw=(W-2*pad)/n-18;const mx=Math.max(...D.segments.map(s=>Math.max(s.with,s.without)))*1.12||1;
const y=v=>H-34-(v/mx)*(H-64);
const col=v=>{const t=Math.min(v/mx,1);return "rgb("+Math.round(31+(215-31)*t)+","+Math.round(158-(158-38)*t)+","+Math.round(120-(120-61)*t)+")";};
let bars=[];D.segments.forEach((s,i)=>{const x=pad+i*((W-2*pad)/n)+9;
  const r=document.createElementNS("http://www.w3.org/2000/svg","rect");
  r.setAttribute("x",x);r.setAttribute("width",bw);r.setAttribute("rx",5);svg.appendChild(r);bars.push(r);
  const t=document.createElementNS("http://www.w3.org/2000/svg","text");
  t.setAttribute("x",x+bw/2);t.setAttribute("y",H-12);t.setAttribute("fill","#475569");
  t.setAttribute("font-size","12");t.setAttribute("text-anchor","middle");t.setAttribute("font-family","Inter");t.setAttribute("font-weight","600");
  t.textContent=s.label;svg.appendChild(t);});
function draw(p){D.segments.forEach((s,i)=>{const v=s.with+(s.without-s.with)*p;
  bars[i].setAttribute("y",y(v));bars[i].setAttribute("height",Math.max((H-34)-y(v),2));bars[i].setAttribute("fill",col(v));});
  document.getElementById("rec").textContent=(D.recovery*p).toFixed(0)+"%";
  document.getElementById("rs").textContent="\u20B9"+Math.round(D.rupees*p).toLocaleString();
  document.getElementById("vm").textContent=Math.round(D.veh_min*p).toLocaleString();}
draw(0);document.getElementById("play").onclick=function(){let t0=null;const dur=1500;
  function step(ts){if(!t0)t0=ts;const p=Math.min((ts-t0)/dur,1);draw((1-Math.cos(p*Math.PI))/2);
    if(p<1)requestAnimationFrame(step);}
  requestAnimationFrame(step);};
</script>"""
        return tpl.replace("__DATA__", json.dumps(payload))

    components.html(anim(vmls, si, letters, saved_vm, rupees, recovery), height=330)
    st.markdown(f"<div class='take'>Clearing <b>Spot {letters[si]}</b> "
                f"({loc(*coords[si])}) frees up about <b>{recovery:.0f}%</b> of this "
                f"road's wasted time — <b>{saved_vm:,} vehicle-minutes</b> and "
                f"<b>₹{rupees:,}</b> every peak hour.</div>", unsafe_allow_html=True)
    with st.expander("Why does this spot matter? (plain explanation)"):
        st.write(why_this_zone(loader.get_zone(zone)))

# ── 4 · ACT ──────────────────────────────────────────────────────────────────
section(4, "Where should officers go first?",
        "Finally, we rank every hotspot by how much good clearing it does, and "
        "spread officers <b>fairly</b> across the city instead of piling them on "
        "one area. Lower fairness score = more evenly shared.")
plan = routing.get_plan(officers_per_station=3)
c1, c2 = st.columns([1, 2])
with c1:
    g = plan["fairness_gini"]
    st.markdown(f"<div class='big'>{g:.2f}</div>"
                f"<div class='bigsub'>fairness score (0 = perfectly even)</div>",
                unsafe_allow_html=True)
    st.caption("Real plan from the routing engine." if plan["source"]=="B-real"
               else "Sample plan — drop routing_plan.json into data/ for the full version.")
with c2:
    pf = routing.as_frame(plan).head(10).copy()
    if {"lat", "lon"}.issubset(pf.columns):
        pf["Location"] = [loc(la, lo) for la, lo in zip(pf["lat"], pf["lon"])]
    rename = {"officer_slot":"Officer","poi_demand":"Busyness",
              "veh_min_lost":"Time lost (veh-min)","rupees_lost":"₹ lost"}
    pf = pf.rename(columns=rename)
    keep = [c for c in ["Officer","Location","Busyness","Time lost (veh-min)","₹ lost"]
            if c in pf.columns]
    st.dataframe(pf[keep], use_container_width=True, hide_index=True)
    st.caption("Locations are map coordinates — connect Mappls reverse-geocoding "
               "for street names.")

st.markdown("<div class='foot'>Built on Mappls · de-biased risk, congestion impact, "
            "and fair routing · a 3-person build (data · maps & impact · product).</div>",
            unsafe_allow_html=True)