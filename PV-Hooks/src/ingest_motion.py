"""Motion/TikTok/YouTube CSV export -> SQLite bank.

Motion export columns vary run to run. Headers are mapped case-insensitively
and missing columns are tolerated. Everything here is deterministic parsing;
no model calls.
"""

import csv
import re
from pathlib import Path

from nameparse import parse_name
import bank as bankmod
from ingest_video import file_hash

# Case-insensitive header aliases -> target columns. First match wins.
COLUMN_ALIASES = {
    "ad_name": ["ad name", "ad_name", "ad", "creative name", "creative", "name"],
    "spend": ["spend", "amount spent", "amount spent (usd)", "cost", "total spend"],
    "thumbstop": ["thumbstop", "thumbstop rate", "thumb stop", "thumb-stop",
                  "hook rate", "3s view rate"],
    "hold_rate": ["hold rate", "hold_rate", "hold", "15s hold rate",
                  "thruplay rate"],
    "ctr": ["ctr", "ctr (all)", "ctr (link click-through rate)",
            "link ctr", "outbound ctr"],
    "roas": ["roas", "purchase roas", "website purchase roas",
             "purchase roas (return on ad spend)"],
    "campaign_name": ["campaign name", "campaign_name", "campaign"],
    "platform": ["platform", "publisher platform"],
    "period_start": ["reporting starts", "period start", "start date", "date start"],
    "period_end": ["reporting ends", "period end", "end date", "date stop"],
}


def _to_float(val):
    if val is None:
        return None
    s = str(val).strip().replace("$", "").replace(",", "").replace("%", "")
    if not s or s.lower() in ("n/a", "na", "-", "--", "none", "null"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def map_headers(fieldnames):
    lower = {(h or "").strip().lower(): h for h in fieldnames or []}
    mapping = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower:
                mapping[target] = lower[alias]
                break
    return mapping


def infer_platform(filename, row_platform=None):
    if row_platform:
        p = str(row_platform).strip().lower()
        if "tiktok" in p:
            return "TikTok"
        if "youtube" in p or p == "yt":
            return "YouTube"
        if p:
            return "Meta"
    f = filename.lower()
    if "tiktok" in f:
        return "TikTok"
    if "youtube" in f or re.search(r"\byt\b", f):
        return "YouTube"
    return "Meta"


def infer_prospecting(campaign_name):
    """Campaign name is authoritative: NC = prospecting, RC = remarketing.
    NOT the ad-name funnel label."""
    if not campaign_name:
        return None
    tokens = re.split(r"[^A-Za-z]+", campaign_name)
    upper = {t.upper() for t in tokens if t}
    if "NC" in upper:
        return 1
    if "RC" in upper:
        return 0
    return None


def ingest_csv(conn, csv_path):
    """One CSV -> bank rows. Returns (added, updated, unparseable_names)."""
    csv_path = Path(csv_path)
    added = updated = 0
    unparseable = []
    with open(csv_path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        mapping = map_headers(reader.fieldnames)
        if "ad_name" not in mapping:
            return 0, 0, [f"{csv_path.name}: no recognizable ad-name column"]
        for raw in reader:
            ad_name = (raw.get(mapping["ad_name"]) or "").strip()
            if not ad_name:
                continue

            def get(target):
                col = mapping.get(target)
                return raw.get(col) if col else None

            parsed = parse_name(ad_name)
            if parsed["parse_warnings"]:
                unparseable.append(f"{ad_name}: {'; '.join(parsed['parse_warnings'])}")

            campaign = (get("campaign_name") or "").strip() or None
            row = {
                "ad_name": ad_name,
                "platform": infer_platform(csv_path.name, get("platform")),
                "spend": _to_float(get("spend")),
                # Motion pre-scales: 17.3 means 17.3%. Store as-is.
                "thumbstop": _to_float(get("thumbstop")),
                "hold_rate": _to_float(get("hold_rate")),
                "ctr": _to_float(get("ctr")),
                "roas": _to_float(get("roas")),
                "campaign_name": campaign,
                "is_prospecting": infer_prospecting(campaign),
                "avatar": parsed["avatar"],
                "editor": parsed["editor"],
                "funnel_label": parsed["funnel"],
                "fmt": parsed["fmt"],
                "product": parsed["product"],
                "ad_date": parsed["ad_date"],
                "period_start": (get("period_start") or "").strip(),
                "period_end": (get("period_end") or "").strip(),
            }
            outcome = bankmod.upsert_creative(conn, row)
            if outcome == "added":
                added += 1
            else:
                updated += 1
    conn.commit()
    return added, updated, unparseable


def ingest_drop(conn, drop_dir):
    """Parse everything new in the drop directory. A file is 'new' if its
    (name, content hash) has not been ingested before; re-running on the same
    CSV is a no-op at the file level, and the upsert key makes row-level
    ingestion idempotent anyway."""
    drop_dir = Path(drop_dir)
    summary = {"files": [], "added": 0, "updated": 0, "unparseable": [],
               "skipped": []}
    for csv_path in sorted(drop_dir.glob("*.csv")):
        fhash = file_hash(csv_path)
        seen = conn.execute(
            "SELECT 1 FROM ingested_files WHERE filename=? AND file_hash=?",
            (csv_path.name, fhash)).fetchone()
        if seen:
            summary["skipped"].append(csv_path.name)
            continue
        added, updated, unparseable = ingest_csv(conn, csv_path)
        conn.execute(
            "INSERT OR IGNORE INTO ingested_files (filename, file_hash, ingested_at) "
            "VALUES (?, ?, datetime('now'))", (csv_path.name, fhash))
        conn.commit()
        summary["files"].append(csv_path.name)
        summary["added"] += added
        summary["updated"] += updated
        summary["unparseable"].extend(unparseable)
    summary["bank"] = bankmod.bank_stats(conn)
    return summary
