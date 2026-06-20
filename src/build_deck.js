const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";            // 13.3 x 7.5
p.author = "PARKLENS — Member C";
p.title = "PARKLENS";

// ── palette (traffic: deep navy + amber, with risk-red and recovery-teal) ──
const NAVY="0E2A47", NAVY2="173A5E", SLATE="64748B", INK="1E293B";
const AMBER="F4A300", RED="D7263D", TEAL="2A9D8F", PAPER="FFFFFF", MIST="EEF3F8";
const W=13.3, H=7.5;
const sh = () => ({ type:"outer", color:"000000", blur:7, offset:3, angle:90, opacity:0.13 });

function card(s,x,y,w,h,fill){ s.addShape(p.shapes.ROUNDED_RECTANGLE,
  {x,y,w,h,fill:{color:fill||PAPER},rectRadius:0.08,line:{type:"none"},shadow:sh()}); }
function kicker(s,t,x,y,color){ s.addText(t.toUpperCase(),
  {x,y,w:6,h:0.3,fontFace:"Arial",fontSize:12,bold:true,color:color||AMBER,charSpacing:3,margin:0}); }
function title(s,t,x,y,w,color){ s.addText(t,
  {x,y,w:w||11.8,h:0.9,fontFace:"Cambria",fontSize:32,bold:true,color:color||INK,margin:0}); }

// ============ 1 · TITLE ============
let s = p.addSlide(); s.background={color:NAVY};
s.addShape(p.shapes.OVAL,{x:10.4,y:-2.2,w:5.6,h:5.6,fill:{color:NAVY2},line:{type:"none"}});
s.addShape(p.shapes.OVAL,{x:11.6,y:4.6,w:4.2,h:4.2,fill:{color:NAVY2},line:{type:"none"}});
s.addText("PARKLENS",{x:0.9,y:2.2,w:11,h:1.2,fontFace:"Cambria",fontSize:60,bold:true,color:PAPER,margin:0});
s.addText("Finding the parking hotspots the data can't see — and pricing the congestion they cause.",
  {x:0.95,y:3.45,w:10.5,h:0.8,fontFace:"Calibri",fontSize:20,color:"CADCFC",margin:0});
s.addText([
  {text:"298k violations",options:{color:AMBER,bold:true}},
  {text:"   •   de-biased risk   •   Mappls-calibrated impact   •   live what-if twin",options:{color:"9DB4CE"}},
],{x:0.95,y:4.5,w:11,h:0.4,fontFace:"Calibri",fontSize:15,margin:0});
s.addText("Bengaluru traffic-enforcement intelligence",
  {x:0.95,y:6.5,w:11,h:0.4,fontFace:"Arial",fontSize:12,color:"6E86A6",charSpacing:2,margin:0});

// ============ 2 · PROBLEM ============
s = p.addSlide(); s.background={color:PAPER};
kicker(s,"The problem",0.9,0.55,RED);
title(s,"Enforcement looks where it already looks",0.9,0.9);
s.addText("Ticket counts measure where officers go — not where violations actually happen. The worst spots can look clean simply because nobody patrols them.",
  {x:0.9,y:1.95,w:7.0,h:1.2,fontFace:"Calibri",fontSize:17,color:SLATE,margin:0});
const probs=[["Counting bias","High-violation cells with low patrol vanish from a raw heatmap."],
  ["No price tag","\"Lots of tickets\" doesn't tell a commissioner what congestion costs."],
  ["Static deployment","Officers aren't routed to the highest-impact cells, or fairly."]];
let py=3.4;
probs.forEach(([h,d])=>{ card(s,0.9,py,7.1,0.95);
  s.addText(h,{x:1.15,y:py+0.14,w:6.6,h:0.35,fontFace:"Cambria",fontSize:16,bold:true,color:NAVY,margin:0});
  s.addText(d,{x:1.15,y:py+0.5,w:6.6,h:0.35,fontFace:"Calibri",fontSize:13,color:SLATE,margin:0}); py+=1.1;});
card(s,8.3,1.95,4.1,4.55,NAVY);
s.addText("The blind-spot\ngap",{x:8.55,y:2.3,w:3.6,h:1.0,fontFace:"Cambria",fontSize:26,bold:true,color:PAPER,margin:0});
s.addText([{text:"620",options:{fontSize:54,bold:true,color:AMBER,breakLine:true}},
  {text:"cells flagged as shadow hotspots — high true risk, low enforcement",options:{fontSize:14,color:"CADCFC"}}],
  {x:8.55,y:3.5,w:3.6,h:2.5,fontFace:"Calibri",valign:"top",margin:0});

// ============ 3 · DATA ============
s = p.addSlide(); s.background={color:PAPER};
kicker(s,"The data",0.9,0.55);
title(s,"Five clean months of Bengaluru violations",0.9,0.9);
const stats=[["298,130","violations logged"],["2,534","H3 hex cells"],
  ["35,425","repeat vehicles"],["34.1%","of violations by repeat offenders"]];
let sx=0.9;
stats.forEach(([n,l])=>{ card(s,sx,2.1,2.85,1.9);
  s.addText(n,{x:sx,y:2.35,w:2.85,h:0.8,align:"center",fontFace:"Cambria",fontSize:34,bold:true,color:NAVY,margin:0});
  s.addText(l,{x:sx+0.2,y:3.2,w:2.45,h:0.6,align:"center",fontFace:"Calibri",fontSize:13,color:SLATE,margin:0}); sx+=3.05;});
s.addText([
  {text:"Window: ",options:{bold:true,color:INK}},{text:"9 Nov 2023 – 8 Apr 2024.   ",options:{color:SLATE}},
  {text:"Top violation: ",options:{bold:true,color:INK}},{text:"wrong parking.   ",options:{color:SLATE}},
  {text:"Grid: ",options:{bold:true,color:INK}},{text:"H3 res-9 hexagons — equal-area, unbiased, clean Mappls joins.",options:{color:SLATE}},
],{x:0.9,y:4.5,w:11.5,h:0.9,fontFace:"Calibri",fontSize:15,margin:0});
s.addText("Cleaned, de-duplicated and day-grain aggregated by Member A (Contract 1 → B & C).",
  {x:0.9,y:6.5,w:11,h:0.4,fontFace:"Arial",fontSize:11,italic:true,color:SLATE,margin:0});

// ============ 4 · P1 BLIND SPOTS ============
s = p.addSlide(); s.background={color:PAPER};
kicker(s,"Pillar 1 · true risk",0.9,0.55,RED);
title(s,"De-biased risk, anchored to real demand",0.9,0.9);
s.addText([
  {text:"Poisson model with a patrol-exposure offset",options:{bold:true,color:INK,breakLine:true}},
  {text:"recovers the violation rate the raw counts hide. We then keep only blind spots that Mappls POI data confirms are genuine demand magnets.",options:{color:SLATE}},
],{x:0.9,y:1.95,w:6.7,h:1.4,fontFace:"Calibri",fontSize:16,margin:0});
const b1=[["Exposure offset","risk ≠ tickets ÷ patrol effort"],
  ["Demand anchor","Mappls Nearby POI confirms pull"],
  ["SHAP-explained","unique_officers & exposure drive the flag"]];
let by=3.5;
b1.forEach(([h,d])=>{ card(s,0.9,by,6.7,0.82);
  s.addText([{text:h+"  ",options:{bold:true,color:NAVY}},{text:d,options:{color:SLATE}}],
    {x:1.15,y:by+0.24,w:6.2,h:0.4,fontFace:"Calibri",fontSize:14,margin:0}); by+=0.95;});
card(s,8.0,1.95,4.4,4.55,NAVY);
s.addText("Demand-anchored shadow hotspots",{x:8.25,y:2.2,w:3.9,h:0.8,fontFace:"Cambria",fontSize:18,bold:true,color:PAPER,margin:0});
s.addText([{text:"53",options:{fontSize:60,bold:true,color:AMBER,breakLine:true}},
  {text:"high-risk, low-patrol cells with strong nearby POI demand",options:{fontSize:14,color:"CADCFC"}}],
  {x:8.25,y:3.1,w:3.9,h:1.8,fontFace:"Calibri",valign:"top",margin:0});
s.addText("These are the cells to patrol first.",{x:8.25,y:5.7,w:3.9,h:0.5,fontFace:"Calibri",fontSize:13,italic:true,color:"9DB4CE",margin:0});

// ============ 5 · P2 IMPACT ============
s = p.addSlide(); s.background={color:PAPER};
kicker(s,"Pillar 2 · impact",0.9,0.55);
title(s,"Congestion cost, calibrated by Mappls live traffic",0.9,0.9);
s.addText([
  {text:"Modified-BPR delay engine. ",options:{bold:true,color:INK}},
  {text:"Volume is back-solved from Mappls typical-vs-freeflow ETA, then we add the illegal-occupancy share — \"we calibrated volume,\" not \"we assumed it.\"",options:{color:SLATE}},
],{x:0.9,y:1.9,w:6.6,h:1.5,fontFace:"Calibri",fontSize:16,margin:0});
s.addText([{text:"1,665",options:{fontSize:46,bold:true,color:NAVY,breakLine:true}},
  {text:"vehicle-minutes lost at the worst cell, per peak window  ≈  ₹4,994",options:{fontSize:15,color:SLATE}}],
  {x:0.9,y:3.5,w:6.6,h:1.6,fontFace:"Cambria",valign:"top",margin:0});
s.addChart(p.charts.BAR,[{name:"veh-min lost",
  labels:["a01b","e4c3","acf","259a","209b","145a"],
  values:[1665,1665,1665,403,403,96]}],
  {x:8.0,y:1.95,w:4.5,h:4.4,barDir:"col",chartColors:[NAVY],
   chartArea:{fill:{color:PAPER}},showLegend:false,showValue:true,
   dataLabelPosition:"outEnd",dataLabelColor:INK,dataLabelFontSize:9,
   catAxisLabelColor:SLATE,valAxisLabelColor:SLATE,
   valGridLine:{color:"E2E8F0",size:0.5},catGridLine:{style:"none"},
   showTitle:true,title:"Vehicle-minutes lost (top cells)",titleColor:INK,titleFontSize:13});

// ============ 6 · P3 DETERRENCE ============
s = p.addSlide(); s.background={color:PAPER};
kicker(s,"Pillar 3 · deterrence",0.9,0.55,RED);
title(s,"Does enforcing a zone actually help?",0.9,0.9);
s.addText([
  {text:"Zone-month difference-in-differences",options:{bold:true,color:INK,breakLine:true}},
  {text:"on five clean months: above-median-enforced zones are compared with matched low-enforcement zones in the following month.",options:{color:SLATE}},
],{x:0.9,y:1.95,w:7.0,h:1.3,fontFace:"Calibri",fontSize:16,margin:0});
card(s,0.9,3.4,7.0,1.5,MIST);
s.addText([
  {text:"Finding:  ",options:{bold:true,color:TEAL}},
  {text:"enforced zones show lower subsequent violations than matched controls — the ROI rationale for routed deployment.",options:{color:INK}},
],{x:1.15,y:3.62,w:6.5,h:1.1,fontFace:"Calibri",fontSize:15,margin:0,valign:"top"});
card(s,8.3,1.95,4.1,2.9,NAVY);
s.addText("Honest caveat",{x:8.55,y:2.2,w:3.6,h:0.4,fontFace:"Cambria",fontSize:18,bold:true,color:AMBER,margin:0});
s.addText("Treated zones start highest, so part of the drop is regression to the mean. We report the effect with that caveat rather than overclaim causality.",
  {x:8.55,y:2.75,w:3.6,h:1.9,fontFace:"Calibri",fontSize:14,color:"CADCFC",margin:0,valign:"top"});
s.addText("Recurrence curve is shown as recidivism context — not as the deterrence proof.",
  {x:8.3,y:5.05,w:4.1,h:0.6,fontFace:"Calibri",fontSize:11,italic:true,color:SLATE,margin:0});

// ============ 7 · P4 TWIN (showpiece) ============
s = p.addSlide(); s.background={color:NAVY};
kicker(s,"Pillar 4 · the showpiece",0.9,0.55,AMBER);
s.addText("Clear a hotspot — watch the corridor recover",
  {x:0.9,y:0.9,w:11.8,h:0.9,fontFace:"Cambria",fontSize:32,bold:true,color:PAPER,margin:0});
s.addText("A live digital twin of a real arterial. Toggle a hotspot off and B's Mappls-calibrated engine recomputes the corridor in real time.",
  {x:0.9,y:1.85,w:11.5,h:0.7,fontFace:"Calibri",fontSize:17,color:"CADCFC",margin:0});
const tw=[["1,666","vehicle-minutes recovered",TEAL],["₹4,997","saved per peak window",AMBER],
  ["1 cell","cleared on the corridor",PAPER]];
let tx=0.9;
tw.forEach(([n,l,c])=>{ card(s,tx,2.9,3.85,2.2,NAVY2);
  s.addText(n,{x:tx,y:3.2,w:3.85,h:0.9,align:"center",fontFace:"Cambria",fontSize:40,bold:true,color:c,margin:0});
  s.addText(l,{x:tx+0.25,y:4.25,w:3.35,h:0.6,align:"center",fontFace:"Calibri",fontSize:14,color:"CADCFC",margin:0}); tx+=4.1;});
s.addText("Numbers match B's published veh_min_lost for the cell — the twin and the impact table agree.",
  {x:0.9,y:5.5,w:11.5,h:0.5,fontFace:"Calibri",fontSize:14,italic:true,color:"9DB4CE",margin:0});

// ============ 8 · DEPLOYMENT ============
s = p.addSlide(); s.background={color:PAPER};
kicker(s,"From insight to action",0.9,0.55);
title(s,"Fair, routed deployment",0.9,0.9);
s.addText("Officers are routed to the highest impact-weighted cells within each station, with a fairness constraint so enforcement isn't dumped on one ward.",
  {x:0.9,y:1.95,w:7.0,h:1.1,fontFace:"Calibri",fontSize:16,color:SLATE,margin:0});
const dz=[["Impact-weighted","risk × veh-min × severity ranks the queue"],
  ["Mappls VRP","route optimisation + 15-min Isopolygon coverage"],
  ["Gini fairness","spread across wards, not piled on one"]];
let dy=3.2;
dz.forEach(([h,d])=>{ card(s,0.9,dy,7.0,0.92);
  s.addText([{text:h+"  ",options:{bold:true,color:NAVY}},{text:d,options:{color:SLATE}}],
    {x:1.15,y:dy+0.28,w:6.5,h:0.4,fontFace:"Calibri",fontSize:14,margin:0}); dy+=1.05;});
card(s,8.3,1.95,4.1,4.55,NAVY);
s.addText("Fairness score",{x:8.55,y:2.25,w:3.6,h:0.5,fontFace:"Cambria",fontSize:20,bold:true,color:PAPER,margin:0});
s.addText([{text:"0.60",options:{fontSize:64,bold:true,color:TEAL,breakLine:true}},
  {text:"Gini across wards, 3 officers per station",options:{fontSize:14,color:"CADCFC"}}],
  {x:8.55,y:3.0,w:3.6,h:2.0,fontFace:"Calibri",valign:"top",margin:0});

// ============ 9 · CLOSE / ARCHITECTURE ============
s = p.addSlide(); s.background={color:NAVY};
s.addShape(p.shapes.OVAL,{x:-2,y:4.6,w:5,h:5,fill:{color:NAVY2},line:{type:"none"}});
kicker(s,"The whole pipeline",0.9,0.7,AMBER);
s.addText("Find it. Price it. Act on it.",
  {x:0.9,y:1.15,w:11.5,h:0.9,fontFace:"Cambria",fontSize:34,bold:true,color:PAPER,margin:0});
const flow=[["Clean","298k rows → H3, severity, exposure"],
  ["Blind spots","de-biased risk + Mappls demand"],
  ["Impact","Mappls-calibrated MBPR → ₹"],
  ["Twin + Deploy","what-if recovery + fair routing"]];
let fx=0.9;
flow.forEach(([h,d],i)=>{ card(s,fx,2.6,2.85,2.2,NAVY2);
  s.addText(String(i+1),{x:fx+0.25,y:2.8,w:0.8,h:0.6,fontFace:"Cambria",fontSize:26,bold:true,color:AMBER,margin:0});
  s.addText(h,{x:fx+0.25,y:3.45,w:2.4,h:0.4,fontFace:"Cambria",fontSize:16,bold:true,color:PAPER,margin:0});
  s.addText(d,{x:fx+0.25,y:3.9,w:2.4,h:0.8,fontFace:"Calibri",fontSize:12,color:"CADCFC",margin:0}); fx+=3.05;});
s.addText("Built on Mappls end-to-end — Snap-to-Road, Nearby POI, ETA, VRP, Isopolygon. No OpenStreetMap.",
  {x:0.9,y:5.5,w:11.5,h:0.5,fontFace:"Calibri",fontSize:15,color:"9DB4CE",margin:0});
s.addText("PARKLENS",{x:0.9,y:6.5,w:6,h:0.5,fontFace:"Cambria",fontSize:18,bold:true,color:AMBER,margin:0});

[ "Title.","The blind-spot problem.","The dataset.","Pillar 1 — de-biased, demand-anchored risk.",
  "Pillar 2 — Mappls-calibrated congestion cost.","Pillar 3 — deterrence DiD with honest caveat.",
  "Pillar 4 — the live what-if twin (showpiece).","Fair routed deployment.","Close — full pipeline + Mappls usage."
].forEach((n,i)=> p.slides[i].addNotes(n));

p.writeFile({ fileName: "PARKLENS_deck.pptx" }).then(f=>console.log("wrote",f));
