# 🅿️ PARKLENS — Bengaluru Parking-Induced Congestion Intelligence

**Gridlock Hackathon · Theme 1: Poor Visibility on Parking-Induced Congestion**

> *How can AI-driven parking intelligence detect illegal-parking hotspots and quantify their impact on traffic flow to enable targeted enforcement?*

---

# 🚨 The Problem

Every parking heatmap you've seen is really a map of where police already patrol—not where violations actually happen.

Bengaluru's enforcement logs are exactly that: a record of patrol activity, not true violation incidence.

**PARKLENS** removes enforcement bias to reveal the hotspots the city is blind to, quantifies their congestion impact in **vehicle-minutes and rupees**, proves whether enforcement deters repeat offenders, and lets users simulate clearing a hotspot to visualize traffic recovery.

All of this is built using only:

* 📄 Jan–May parking violation CSV (~298K records)
* 🗺️ Mappls APIs

No external traffic datasets or OSM data are used.

---

# ✨ What Makes PARKLENS Unique

Most solutions simply plot violation density. Since violation records are actually enforcement logs, those heatmaps mostly reflect where police patrol.

PARKLENS corrects this with four differentiated pillars.

| Pillar                         | Function                                                             | Why It Matters                                           |
| ------------------------------ | -------------------------------------------------------------------- | -------------------------------------------------------- |
| **P1 — Blind-Spot Correction** | Poisson regression with patrol exposure offset and POI demand anchor | Reveals hidden hotspots missed by enforcement            |
| **P2 — Congestion Cost**       | Modified BPR model calibrated using Mappls ETA                       | Quantifies impact in vehicle-minutes and ₹               |
| **P3 — Deterrence Proof**      | Survival analysis + Difference-in-Differences                        | Measures whether enforcement actually works              |
| **P4 — What-If Traffic Twin**  | Interactive corridor graph simulation                                | Demonstrates delay recovery after hotspot removal        |
| **P-ROI Fair Deployment**      | Impact-weighted hotspot ranking + VRP optimization                   | Produces actionable patrol plans with equitable coverage |

---

# 🧩 System Architecture

```text
                CSV (298k parking violations)
                            │
                ┌───────────▼───────────┐
                │ Clean + Feature Store │
                │ H3 hex, severity,     │
                │ exposure, footprint,  │
                │ repeat offenders      │
                └───────────┬───────────┘
         ┌──────────────────┼────────────────────┐
         ▼                  ▼                    ▼
 P1 Blind-Spot         P3 Deterrence        Mappls API Cache
 De-biased Risk        DiD + Survival        Snap-to-Road
 + POI Demand          Analysis              Nearby POI
                                              GeoAnalytics
                                              ETA, VRP
                                                    │
                                                    ▼
                                      P2 MBPR Congestion Engine
                                                    │
                                                    ▼

     Impact Weighted Risk =
     RiskDeBiased × VehMinLost × Severity

         ┌────────────────┬─────────────────┬────────────────┐
         ▼                ▼                 ▼
   Fair VRP Patrol   P4 Traffic Twin    FastAPI Endpoints
     Deployment      NetworkX Graph     /risk /impact
                                         /hotspots
                                         /deploy
                                         /whatif
                            │
                            ▼

         Streamlit Dashboard + Mappls Maps SDK
          + Claude API Narrative Generation
```

---

# ⚙️ Project Flow

## 1. Data Ingestion & Cleaning

* Load raw parking violation CSV
* Remove duplicates and null columns
* Parse offence arrays
* Build feature store

Features:

* H3 resolution-9 cells
* Severity score
* Vehicle footprint
* Patrol exposure
* Repeat offender flags

---

## 2. Blind-Spot Risk Modeling (P1)

Fit a Poisson regression with patrol exposure offset:

```math
\log(\lambda)
=
\beta_0+\beta_1 POI+\beta_2 Road+\log(exposure)
```

Cells with:

* High predicted risk
* Low patrol exposure

become **shadow hotspots**.

Mappls Nearby POI density serves as a demand anchor.

---

## 3. Mappls Enrichment

Top hotspots are enriched using:

* Snap-to-Road
* Nearby POI
* GeoAnalytics
* Predictive ETA
* Isopolygons

Results are cached locally.

---

## 4. Congestion Impact Modeling (P2)

Modified Bureau of Public Roads model:

```math
T_a=T_0
\left[
1+\alpha
\left(
\frac{V}{C_{eff}}
\right)^\beta
\right]
```

where:

* (T_a): congested travel time
* (T_0): free-flow travel time
* (V): traffic volume
* (C_{eff}=C-C_{io}): effective capacity

Constants:

```text
α = 3.59
β = 0.40
```

### Traffic Volume Calibration

Volume is back-solved from Mappls ETA:

```math
delay\ ratio = \frac{T_{typical}}{T_{freeflow}}
```

```math
\frac{V}{C}
=
\left(
\frac{delay\ ratio -1}{\alpha}
\right)^{1/\beta}
```

### Impact Metrics

Vehicle Minutes Lost:

```math
(T_{with}-T_{without})
\times V
\times TimeWindow
\times 60
```

Rupees Lost:

```math
VehMinLost \times ₹3/min
```

---

## 5. Deterrence Analysis (P3)

### Repeat Offender Survival Analysis

Measure:

* Time-to-next violation
* Recurrence curves

Dataset:

**35,587 repeat-offender vehicles**

### Difference-in-Differences

Zone-month causal analysis estimates whether increased enforcement reduces violations.

---

## 6. Fair Deployment Planning

Hotspots are ranked by:

```math
ImpactWeightedRisk
=
RiskDeBiased
\times VehMinLost
\times Severity
```

Mappls Route Optimization solves patrol allocation.

A Gini fairness constraint prevents excessive concentration in a few wards.

---

## 7. Digital Twin (P4)

NetworkX corridor graph:

* Nodes = intersections
* Edges = road segments

Users can:

* Toggle hotspot ON/OFF
* Recompute delays
* Visualize flow recovery

This creates the key demo moment:

> "Clear the hotspot and watch congestion disappear."

---

# 📁 Repository Structure

```text
PARKLENS-app/
│
├── data/                                  # Data artifacts
│   ├── raw_violations.csv                 # Raw parking violation dataset (input)
│   ├── clean_violations.parquet           # Cleaned & feature-engineered data
│   ├── hotspots.csv                       # Final hotspot table with all pillar outputs
│   └── mappls_cache.json                  # Cached Mappls API responses (optional)
│
├── src/                                   # Core source code
│   ├── clean.py                           # Data cleaning, parsing and deduplication
│   ├── features.py                        # H3 indexing, severity, exposure, repeat flags
│   ├── blindspot.py                       # Poisson-offset model + shadow hotspot detection
│   ├── deterrence.py                      # Survival analysis and Difference-in-Differences
│   ├── forecast.py                        # Optional LightGBM hotspot forecasting
│   ├── mappls_client.py                   # Mappls API wrapper, auth and caching
│   ├── impact_bpr.py                      # Modified BPR congestion engine + ETA calibration
│   ├── routing.py                         # Fair VRP patrol deployment
│   ├── graph.py                           # Corridor graph construction
│   ├── twin.py                            # Digital twin propagation engine
│   └── api.py                             # FastAPI backend endpoints
│
├── app/                                   # Dashboard and explainability layer
│   ├── dashboard.py                       # Streamlit interface and guided tour
│   └── narrative.py                       # LLM-powered "Why this zone?" explanations
│
├── deck/                                  # Presentation materials
│   ├── slides.pdf                         # Final hackathon pitch deck
│   └── demo_script.md                     # 90-second demo walkthrough
│
├── contracts.md                           # Team interface contracts
├── requirements.txt                       # Python dependencies
├── README.md                              # Project documentation
└── LICENSE                                # Open-source license (optional)
```

---

## 📂 Folder Overview

### **data/**

Stores the raw dataset and generated artifacts. Intermediate outputs such as cleaned parquet files, hotspot rankings, and cached Mappls responses are persisted here.

### **src/**

Contains the complete analytical pipeline, including:

* **P1:** Blind-Spot Correction
* **P2:** Congestion Impact Modeling
* **P3:** Deterrence Analysis
* **P4:** Digital Twin Simulation
* **P-ROI:** Patrol Deployment Optimization

### **app/**

Interactive Streamlit dashboard and narrative generation layer for explaining hotspot significance.

---

# 🚀 Getting Started

## Prerequisites

* Python 3.10+
* Mappls API Key
* Raw violation CSV

```
data/raw_violations.csv
```

---

## Installation

```bash
git clone https://github.com/dhatrisriram/PARKLENS-app.git

cd PARKLENS-app

pip install -r requirements.txt
```

---

## Generate Data

```bash
python notebooks/parklens_member_b_final.py YOUR_MAPPLS_API_KEY

python src/export_stats.py
```

---

## Launch FastAPI Backend

```bash
uvicorn src.api:app --reload
```

---

## Launch Dashboard

```bash
streamlit run app/dashboard.py
```

---

# 🌐 API Endpoints

| Endpoint    | Purpose                   |
| ----------- | ------------------------- |
| `/hotspots` | Top hotspot information   |
| `/risk`     | De-biased risk scores     |
| `/impact`   | Congestion cost estimates |
| `/deploy`   | Patrol routing plan       |
| `/whatif`   | Digital twin simulation   |

---

# 📚 References

### Modified BPR Function

Gore, Arkatkar, Joshi & Antoniou (2023)

*Transportation Research Record 2677(5), 966–990*

---

### South Asian Calibration Constants

Anwar, Fujiwara & Zhang (2011)

Dhaka Urban Arterials

```
α = 3.59
β = 0.40
```

---

### Causal Congestion Attribution

arXiv:2206.02164

*Curbside Pick-Up and Drop-Off Causal Impact Study*

---

### Enforcement Bias and Deterrence Gap

IISc Sustainable Transportation Lab

BTP–IISc CiSTUP MoU (2023)

---

### Mappls APIs

https://about.mappls.com/api/

---

# 🏁 PARKLENS

## Find it. Price it. Clear it. Deploy it.

**Seeing what enforcement misses. Quantifying what congestion costs. Deploying where it matters most.**
