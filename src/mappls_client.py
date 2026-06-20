
# mappls_client.py — shared Mappls client (Member B → Member A & C)
# Set MAPPLS_KEY before importing

import os, json, time, requests
from pathlib import Path
import dotenv

MAPPLS_KEY = os.getenv("MAPPLS_KEY", "")   # set via env; do NOT commit a real key
CACHE_FILE = Path("mappls_cache.json")

def _load(): return json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
def _save(c): CACHE_FILE.write_text(json.dumps(c, indent=2))
CACHE = _load()

def route_geometry(origin_lat, origin_lon, dest_lat, dest_lon, corridor_id=None):
    key = f"route_{corridor_id or f'{origin_lat:.4f}_{origin_lon:.4f}'}"
    if key in CACHE: return CACHE[key]
    url = (
        f"https://apis.mappls.com/advancedmaps/v1/{MAPPLS_KEY}/route_adv/driving"
        f"/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        f"?geometries=geojson&steps=false"
    )
    result = {"type": "LineString", "coordinates": []}
    try:
        r = requests.get(url, timeout=15)
        result = r.json()["routes"][0]["geometry"]
    except: pass
    CACHE[key] = result; _save(CACHE); time.sleep(0.2)
    return result
