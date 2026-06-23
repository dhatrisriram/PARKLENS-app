# impact_bpr.py — Member B -> Member C
ALPHA=3.59; BETA=0.40; SAT_FLOW=1800; VOT_RS_PER_MIN=3.0
FOOTPRINT_C_IO={0.5:0.10,1.0:0.25,1.5:0.40,2.0:0.60,3.0:1.00}
ROAD_CLASS_VC={'arterial':0.60,'collector':0.45,'local':0.35,'unknown':0.45}
_registry={}

def load_segments(path):
    import pandas as pd; global _registry
    df=pd.read_csv(path)
    for _,r in df.iterrows():
        C=r.get('lanes',2)*SAT_FLOW
        _registry[r['h3_cell']]={
            'lanes':int(r.get('lanes',2)),
            'v0_kmh':float(r.get('v0_kmh',40)),
            'V_calibrated':float(r.get('V_calibrated',
                ROAD_CLASS_VC.get(r.get('road_class','unknown'),0.45)*C)),
            'road_class':str(r.get('road_class','unknown'))}
    print(f'Loaded {len(_registry)} segments')

def recompute(segment_id, c_io):
    seg=_registry.get(segment_id,{'lanes':2,'v0_kmh':40,'V_calibrated':1080,'road_class':'unknown'})
    C=seg['lanes']*SAT_FLOW; V=seg['V_calibrated']
    C_eff=max(C-c_io,0.1*C); T0=(0.5/seg['v0_kmh'])*60
    Tw=T0*(1+ALPHA*(V/C_eff)**BETA); Two=T0*(1+ALPHA*(V/C)**BETA)
    dr=Tw/Two if Two>0 else 1.0; vml=(Tw-Two)*V*8
    return {'T_a_with':round(Tw,4),'T_a_without':round(Two,4),
            'delay_ratio':round(dr,4),'veh_min_lost':round(vml,1),
            'rupees_lost':round(vml*VOT_RS_PER_MIN,0)}
