import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import bank as bankmod
import ingest_motion

SYNTHETIC_CSV = """Ad Name,Campaign Name,Amount Spent (USD),Thumbstop Rate,Hold Rate,CTR (All),Purchase ROAS,Reporting Starts,Reporting Ends
Video_20250614_GrassFedTruth_BeefSticks_25off_UGC_Raw_Conversions_TOF_a-NAC_Meta_cr-JD_v2_lpBundle,PV | NC | Broad | Video,"$4,210.55",27.4,11.2,1.31,2.4,2025-06-01,2025-06-30
Video_20250601_MorningRoutine_BoneBroth_none_TalkingHead_Warm_Conversions_BOF_a-LIS_Meta_cr-am_v1,PV | RC | Purchasers,3100.00,35.1,14.8,1.9,3.8,2025-06-01,2025-06-30
Static_20250520_ProteinMyth_BeefSticks_10off_Img_Clean_Sales_MOF_a-SAR_Meta_cr-JD_v3,PV | NC | Interest Stack,900.25,19.0,8.0,0.8,1.1,2025-06-01,2025-06-30
final_FINAL_v2 (1),PV | NC | Broad | Video,5000,22.0,9.9,1.0,1.5,2025-06-01,2025-06-30
Video_20250610_FarmTour_WP_none_Founder_Docu_Conversions_TOF_a-EVA_Meta_cr-mk_v1,WP | RC | Site Visitors,2801.10,31.2,,1.4,,2025-06-01,2025-06-30
"""


def make_env(tmp_path):
    drop = tmp_path / "motion_drop"
    drop.mkdir()
    (drop / "motion_export_june.csv").write_text(SYNTHETIC_CSV)
    conn = bankmod.connect(tmp_path / "bank.db")
    return conn, drop


def test_ingest_and_field_mapping(tmp_path):
    conn, drop = make_env(tmp_path)
    summary = ingest_motion.ingest_drop(conn, drop)
    assert summary["added"] == 5
    assert summary["updated"] == 0
    # one malformed name got warnings but was still stored, raw name intact
    assert any("final_FINAL" in u for u in summary["unparseable"])
    row = conn.execute(
        "SELECT * FROM creatives WHERE ad_name LIKE 'final_FINAL%'"
    ).fetchone()
    assert row is not None
    assert row["spend"] == 5000.0

    row = conn.execute(
        "SELECT * FROM creatives WHERE ad_name LIKE '%GrassFedTruth%'"
    ).fetchone()
    assert row["spend"] == 4210.55            # currency + thousands separator
    assert row["thumbstop"] == 27.4           # Motion pre-scaled, stored as-is
    assert row["avatar"] == "a-NAC"
    assert row["editor"] == "cr-JD"
    assert row["is_prospecting"] == 1         # NC in campaign name

    row = conn.execute(
        "SELECT * FROM creatives WHERE ad_name LIKE '%MorningRoutine%'"
    ).fetchone()
    assert row["is_prospecting"] == 0         # RC in campaign name


def test_ingest_is_idempotent(tmp_path):
    conn, drop = make_env(tmp_path)
    ingest_motion.ingest_drop(conn, drop)
    before = conn.execute("SELECT COUNT(*) n FROM creatives").fetchone()["n"]
    summary2 = ingest_motion.ingest_drop(conn, drop)
    after = conn.execute("SELECT COUNT(*) n FROM creatives").fetchone()["n"]
    assert before == after == 5
    assert summary2["added"] == 0
    assert summary2["skipped"] == ["motion_export_june.csv"]


def test_spend_floor_and_benchmarks(tmp_path):
    conn, drop = make_env(tmp_path)
    ingest_motion.ingest_drop(conn, drop)
    stats = bankmod.bank_stats(conn)
    # $900 row is under the floor: in the bank, out of the qualified pool
    assert stats["total"] == 5
    assert stats["qualified"] == 4
    bm = bankmod.benchmarks(conn, "Meta")
    assert bm["prospecting"]["n"] == 2   # NC rows over floor
    assert bm["remarketing"]["n"] == 2   # RC rows over floor
    # prospecting and remarketing never blended
    assert bm["prospecting"]["thumbstop_median"] != bm["remarketing"]["thumbstop_median"]


def test_thin_bank_marks_ungrounded(tmp_path):
    conn, drop = make_env(tmp_path)
    ingest_motion.ingest_drop(conn, drop)
    ctx = bankmod.bank_context(conn, avatar="a-NAC")
    assert ctx["bank_thin"] is True            # 4 qualified < 10
    assert "UNGROUNDED" in ctx["instruction"]
    assert ctx["nearest_neighbors"] == []


def test_platform_inference_from_filename(tmp_path):
    drop = tmp_path / "motion_drop"
    drop.mkdir()
    (drop / "tiktok_export.csv").write_text(
        "Ad Name,Spend,Thumbstop\nVideo_20250101_X_BS_a-NAC_TOF_cr-aa_v1,3000,25\n")
    conn = bankmod.connect(tmp_path / "bank.db")
    ingest_motion.ingest_drop(conn, drop)
    row = conn.execute("SELECT platform FROM creatives").fetchone()
    assert row["platform"] == "TikTok"
