"""app/narrative.py — the dashboard "why this zone" generator (Claude API only).

Per the plan this is NOT engineering load and is the first thing to cut to static
text under time pressure — so it ALWAYS degrades to a template if the API key is
missing or the call fails. Never let it block a demo.

Needs:  pip install anthropic   and   export ANTHROPIC_API_KEY=...
"""
from __future__ import annotations
import os
import sys

# Make src/ and the project root importable regardless of launch dir.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (os.path.join(_ROOT, "src"), _ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import config  # noqa: E402

_SYSTEM = (
    "You are PARKLENS, a Bengaluru parking-congestion analyst. In 2–3 crisp "
    "sentences explain why a given hotspot matters to a traffic officer. Be "
    "concrete about blind-spot status, severity and congestion impact. No preamble."
)


def _template(z: dict) -> str:
    bs = "a blind spot (high de-biased risk, low patrol exposure)" if z.get(
        "blindspot_flag") else "an observed hotspot"
    vml = z.get("veh_min_lost")
    impact = (f" It costs ~{vml:,.0f} vehicle-minutes per peak window."
              if vml and vml == vml else
              " Congestion cost pending Mappls-calibrated impact from B.")
    return (f"Zone {z['zone_id']} is {bs}, with a de-biased risk of "
            f"{z['risk_debiased']:.4f} and severity {z['severity_score']:.1f}."
            f"{impact}")


def why_this_zone(zone: dict) -> str:
    """Return a short natural-language rationale. Falls back to a template."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return _template(zone)
    try:
        import anthropic
        client = anthropic.Anthropic()
        facts = {k: zone.get(k) for k in (
            "zone_id", "risk_debiased", "blindspot_flag", "severity_score",
            "peak_dow", "exposure", "veh_min_lost", "rupees_lost")}
        msg = client.messages.create(
            model=config.NARRATIVE_MODEL,
            max_tokens=160,
            system=_SYSTEM,
            messages=[{"role": "user",
                       "content": f"Hotspot facts (JSON): {facts}"}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()
    except Exception as e:                 # any failure → static text
        return _template(zone) + f"\n\n_(narrative fallback: {e})_"


if __name__ == "__main__":
    import loader  # type: ignore
    z = loader.top_blindspots(1).iloc[0].to_dict()
    print(why_this_zone(z))
