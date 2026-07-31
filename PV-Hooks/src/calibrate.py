"""Calibrate: join predictions.jsonl to actuals in the bank.

Bands: sub-floor < 23, floor-to-strong 23-33, strong-plus > 33.
Only rows with actual thumbstop and spend >= $2,500 count.
"""

import json
from pathlib import Path

from bank import SPEND_FLOOR, THUMBSTOP_FLOOR, THUMBSTOP_STRONG

BANDS = ["sub-floor", "floor-to-strong", "strong-plus"]


def band_actual(thumbstop):
    if thumbstop < THUMBSTOP_FLOOR:
        return "sub-floor"
    if thumbstop <= THUMBSTOP_STRONG:
        return "floor-to-strong"
    return "strong-plus"


def load_predictions(predictions_path):
    path = Path(predictions_path)
    if not path.exists():
        return []
    preds = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                preds.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return preds


def calibrate(conn, predictions_path):
    """Match predictions to actuals on ad_name. Latest prediction per ad_name
    wins (re-analyzing a video supersedes the earlier read)."""
    preds = load_predictions(predictions_path)
    by_ad = {}
    for p in preds:
        if p.get("ad_name") and p.get("predicted_band") in BANDS:
            by_ad[p["ad_name"]] = p  # later lines overwrite earlier ones

    matched = []
    for ad_name, pred in by_ad.items():
        row = conn.execute(
            "SELECT ad_name, thumbstop, spend FROM creatives "
            "WHERE ad_name=? AND thumbstop IS NOT NULL AND spend >= ? "
            "ORDER BY spend DESC LIMIT 1",
            (ad_name, SPEND_FLOOR)).fetchone()
        if row is None:
            continue
        actual_band = band_actual(row["thumbstop"])
        pi, ai = BANDS.index(pred["predicted_band"]), BANDS.index(actual_band)
        matched.append({
            "ad_name": ad_name,
            "archetype": pred.get("archetype"),
            "confidence": pred.get("confidence"),
            "predicted_band": pred["predicted_band"],
            "actual_band": actual_band,
            "actual_thumbstop": row["thumbstop"],
            "band_distance": abs(pi - ai),
        })

    n = len(matched)
    exact = sum(1 for m in matched if m["band_distance"] == 0)
    adjacent = sum(1 for m in matched if m["band_distance"] <= 1)

    per_archetype = {}
    for m in matched:
        arch = m["archetype"] or "(unclassified)"
        a = per_archetype.setdefault(arch, {"n": 0, "exact": 0, "adjacent": 0})
        a["n"] += 1
        a["exact"] += m["band_distance"] == 0
        a["adjacent"] += m["band_distance"] <= 1

    worst = sorted(matched, key=lambda m: (-m["band_distance"],
                                           m["ad_name"]))[:5]
    worst = [m for m in worst if m["band_distance"] > 0]

    return {
        "n_matched": n,
        "n_predictions_total": len(preds),
        "exact_rate": round(100.0 * exact / n, 1) if n else None,
        "adjacent_rate": round(100.0 * adjacent / n, 1) if n else None,
        "per_archetype": per_archetype,
        "worst_misses": worst,
    }
