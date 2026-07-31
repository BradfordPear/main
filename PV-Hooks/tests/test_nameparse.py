import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nameparse import parse_name


def test_full_canonical_name():
    n = ("Video_20250614_GrassFedTruth_BeefSticks_25off_UGC_Raw_Conversions_"
         "TOF_a-NAC_Meta_cr-JD_v2_lpBundle")
    r = parse_name(n)
    assert r["ad_date"] == "20250614"
    assert r["avatar"] == "a-NAC"
    assert r["editor"] == "cr-JD"
    assert r["funnel"] == "TOF"
    assert r["platform"] == "Meta"
    assert r["version"] == "v2"
    assert r["landing_page"] == "lpBundle"
    assert r["fmt"] == "Video"
    assert r["concept"] == "GrassFedTruth"
    assert r["product"] == "BeefSticks"
    assert r["offer"] == "25off"
    assert r["parse_warnings"] == []


def test_wild_pastures_name_with_drift():
    # Positions drifted: platform before funnel, extra token; anchors still hit.
    n = "Static_20250101_WinterBox_WP_holiday_Img_Clean_Sales_YT_BOF_a-AVA_cr-mk_v11"
    r = parse_name(n)
    assert r["ad_date"] == "20250101"
    assert r["avatar"] == "a-AVA"
    assert r["editor"] == "cr-mk"
    assert r["funnel"] == "BOF"
    assert r["platform"] == "YT"
    assert r["version"] == "v11"
    assert r["product"] == "WP"


def test_nodisc_funnel_and_disc_avatar():
    n = "Video_20240930_PolyphenolStory_OliveOil_none_BrollVO_Docu_Reach_NoDisc_a-DISC_TikTok_cr-QQ_v1"
    r = parse_name(n)
    assert r["funnel"] == "NoDisc"
    assert r["avatar"] == "a-DISC"
    assert r["platform"] == "TikTok"


def test_short_name_missing_positions():
    n = "Video_20250320_QuickTest_a-SUS"
    r = parse_name(n)
    assert r["ad_date"] == "20250320"
    assert r["avatar"] == "a-SUS"
    assert r["concept"] == "QuickTest"
    assert r["funnel"] is None
    assert r["editor"] is None


def test_malformed_name_never_crashes():
    for bad in ("final_FINAL_v2 (1).mp4", "", None, "___", "no separators here",
                "20259999_baddate_only"):
        r = parse_name(bad)
        assert r["parse_warnings"], f"expected warnings for {bad!r}"
        assert r["raw_name"] == bad
        # every field is present even when nothing parses
        assert "avatar" in r and "editor" in r and "funnel" in r
