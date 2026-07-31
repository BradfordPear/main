import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import bank as bankmod
import calibrate as calmod


def seed(conn, ad_name, thumbstop, spend=3000, archetype=None, ad_date=None,
         is_prospecting=1):
    bankmod.upsert_creative(conn, {
        "ad_name": ad_name, "platform": "Meta", "spend": spend,
        "thumbstop": thumbstop, "hold_rate": 10.0, "is_prospecting": is_prospecting,
        "archetype": archetype, "avatar": "a-NAC", "funnel_label": "TOF",
        "ad_date": ad_date,
    })
    conn.commit()


def write_preds(path, preds):
    with open(path, "w") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")


def test_calibrate_bands_and_misses(tmp_path):
    conn = bankmod.connect(tmp_path / "bank.db")
    seed(conn, "ad_hit", 28.0)        # floor-to-strong
    seed(conn, "ad_miss", 40.0)       # strong-plus
    seed(conn, "ad_underfloor", 40.0, spend=100)  # excluded: under spend floor
    preds_path = tmp_path / "predictions.jsonl"
    write_preds(preds_path, [
        {"ad_name": "ad_hit", "predicted_band": "floor-to-strong",
         "archetype": "text_card", "confidence": "med"},
        {"ad_name": "ad_miss", "predicted_band": "sub-floor",
         "archetype": "text_card", "confidence": "high"},
        {"ad_name": "ad_underfloor", "predicted_band": "sub-floor",
         "archetype": "broll_vo", "confidence": "low"},
        {"ad_name": None, "predicted_band": "sub-floor"},  # competitor-ish, skipped
    ])
    r = calmod.calibrate(conn, preds_path)
    assert r["n_matched"] == 2
    assert r["exact_rate"] == 50.0
    assert r["adjacent_rate"] == 50.0   # sub-floor vs strong-plus is distance 2
    assert r["per_archetype"]["text_card"]["n"] == 2
    assert len(r["worst_misses"]) == 1
    assert r["worst_misses"][0]["ad_name"] == "ad_miss"


def test_band_edges():
    assert calmod.band_actual(22.9) == "sub-floor"
    assert calmod.band_actual(23.0) == "floor-to-strong"
    assert calmod.band_actual(33.0) == "floor-to-strong"
    assert calmod.band_actual(33.1) == "strong-plus"


def test_patterns_aggregate_and_fatigue(tmp_path):
    conn = bankmod.connect(tmp_path / "bank.db")
    today = datetime.now()
    recent = (today - timedelta(days=5)).strftime("%Y%m%d")
    older = (today - timedelta(days=45)).strftime("%Y%m%d")
    # Older bucket strong, recent bucket weak: should flag a >5pt drop.
    for i in range(3):
        seed(conn, f"old_{i}", 35.0 + i, archetype="text_card", ad_date=older)
        seed(conn, f"new_{i}", 24.0 + i, archetype="text_card", ad_date=recent)
    agg = bankmod.patterns_aggregate(conn, days=90)
    assert agg, "expected aggregate rows"
    assert all(row["split"] == "prospecting" for row in agg)
    fat = bankmod.fatigue_buckets(conn, days=90)
    assert fat["flags"], "expected a fatigue flag"
    assert fat["flags"][0]["archetype"] == "text_card"
    assert fat["flags"][0]["drop_pts"] == 11.0
