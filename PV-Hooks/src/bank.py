"""SQLite bank: creative performance rows, benchmarks, nearest neighbors.

Rules baked in:
- Spend significance floor $2,500. Below-floor rows exist in the bank but are
  excluded from benchmarks and nearest-neighbor pools.
- Benchmarks are computed per platform, split prospecting vs remarketing.
  Never blended.
- Thumbstop reference points (Meta video): editor floor 23%, strong 33%.
"""

import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

SPEND_FLOOR = 2500.0
THUMBSTOP_FLOOR = 23.0
THUMBSTOP_STRONG = 33.0
THIN_BANK_ROWS = 10

SCHEMA = """
CREATE TABLE IF NOT EXISTS creatives (
    ad_name TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'Meta',
    spend REAL,
    thumbstop REAL,
    hold_rate REAL,
    ctr REAL,
    roas REAL,
    campaign_name TEXT,
    is_prospecting INTEGER,
    avatar TEXT,
    editor TEXT,
    funnel_label TEXT,
    fmt TEXT,
    product TEXT,
    ad_date TEXT,
    hook_transcript TEXT,
    first_cut REAL,
    archetype TEXT,
    fingerprint_path TEXT,
    period_start TEXT DEFAULT '',
    period_end TEXT DEFAULT '',
    ingested_at TEXT,
    UNIQUE (ad_name, platform, period_start, period_end)
);
CREATE TABLE IF NOT EXISTS ingested_files (
    filename TEXT,
    file_hash TEXT,
    ingested_at TEXT,
    UNIQUE (filename, file_hash)
);
"""


def connect(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_creative(conn, row):
    """Insert or update on (ad_name, platform, period_start, period_end).
    Returns 'added' or 'updated'."""
    keys = (row["ad_name"], row.get("platform", "Meta"),
            row.get("period_start", ""), row.get("period_end", ""))
    cur = conn.execute(
        "SELECT rowid FROM creatives WHERE ad_name=? AND platform=? "
        "AND period_start=? AND period_end=?", keys)
    existing = cur.fetchone()
    row = dict(row)
    row.setdefault("platform", "Meta")
    row.setdefault("period_start", "")
    row.setdefault("period_end", "")
    row["ingested_at"] = datetime.now(timezone.utc).isoformat()
    cols = [c for c in row if c != "parse_warnings"]
    if existing:
        sets = ", ".join(f"{c}=?" for c in cols)
        conn.execute(
            f"UPDATE creatives SET {sets} WHERE rowid=?",
            [row[c] for c in cols] + [existing["rowid"]])
        return "updated"
    placeholders = ", ".join("?" for _ in cols)
    conn.execute(
        f"INSERT INTO creatives ({', '.join(cols)}) VALUES ({placeholders})",
        [row[c] for c in cols])
    return "added"


def qualified_where(prefix=""):
    p = prefix
    return f"{p}spend >= {SPEND_FLOOR} AND {p}thumbstop IS NOT NULL"


def bank_stats(conn):
    total = conn.execute("SELECT COUNT(*) n FROM creatives").fetchone()["n"]
    qualified = conn.execute(
        f"SELECT COUNT(*) n FROM creatives WHERE {qualified_where()}"
    ).fetchone()["n"]
    linked = conn.execute(
        f"SELECT COUNT(*) n FROM creatives WHERE {qualified_where()} "
        "AND fingerprint_path IS NOT NULL"
    ).fetchone()["n"]
    coverage = (100.0 * linked / qualified) if qualified else 0.0
    return {"total": total, "qualified": qualified, "linked": linked,
            "coverage_pct": round(coverage, 1)}


def _pct(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def benchmarks(conn, platform="Meta"):
    """Median + p75 thumbstop and hold, per prospecting/remarketing split.
    Never blended."""
    out = {}
    for label, flag in (("prospecting", 1), ("remarketing", 0)):
        rows = conn.execute(
            f"SELECT thumbstop, hold_rate FROM creatives "
            f"WHERE {qualified_where()} AND platform=? AND is_prospecting=?",
            (platform, flag)).fetchall()
        ts = [r["thumbstop"] for r in rows if r["thumbstop"] is not None]
        hold = [r["hold_rate"] for r in rows if r["hold_rate"] is not None]
        out[label] = {
            "n": len(rows),
            "thumbstop_median": round(statistics.median(ts), 1) if ts else None,
            "thumbstop_p75": round(_pct(ts, 0.75), 1) if ts else None,
            "hold_median": round(statistics.median(hold), 1) if hold else None,
            "hold_p75": round(_pct(hold, 0.75), 1) if hold else None,
        }
    return out


def nearest_neighbors(conn, archetype=None, avatar=None, product=None,
                      platform="Meta", k=3):
    """Up to k qualified rows: same archetype first, then same avatar, then
    same product. No fuzzy matching, plain SQL."""
    picked, seen = [], set()

    def grab(where, params):
        if len(picked) >= k:
            return
        rows = conn.execute(
            f"SELECT ad_name, thumbstop, hold_rate, spend, hook_transcript, "
            f"archetype, avatar, product FROM creatives "
            f"WHERE {qualified_where()} AND platform=? AND {where} "
            f"ORDER BY thumbstop DESC LIMIT ?",
            [platform] + params + [k]).fetchall()
        for r in rows:
            if r["ad_name"] not in seen and len(picked) < k:
                seen.add(r["ad_name"])
                picked.append(dict(r))

    if archetype:
        grab("archetype = ?", [archetype])
    if avatar:
        grab("avatar = ?", [avatar])
    if product:
        grab("product = ?", [product])
    return picked


def bank_context(conn, archetype=None, avatar=None, product=None,
                 platform="Meta"):
    """The structured bank block that goes into the autopsy payload."""
    stats = bank_stats(conn)
    thin = stats["qualified"] < THIN_BANK_ROWS
    ctx = {
        "bank_qualified_rows": stats["qualified"],
        "bank_thin": thin,
        "spend_floor": SPEND_FLOOR,
        "thumbstop_reference": {
            "editor_floor_pct": THUMBSTOP_FLOOR,
            "strong_pct": THUMBSTOP_STRONG,
            "note": "Meta video reference points",
        },
    }
    if thin:
        ctx["instruction"] = (
            "The bank has fewer than 10 qualified rows. Label ALL comparisons "
            "UNGROUNDED. Do not invent account history."
        )
        ctx["benchmarks"] = None
        ctx["nearest_neighbors"] = []
    else:
        ctx["benchmarks"] = benchmarks(conn, platform)
        ctx["nearest_neighbors"] = nearest_neighbors(
            conn, archetype=archetype, avatar=avatar, product=product,
            platform=platform)
    return ctx


def link_fingerprint(conn, ad_name, hook_transcript, first_cut, archetype,
                     fingerprint_path):
    """Fill autopsy-derived columns on any bank row matching this ad name."""
    cur = conn.execute(
        "UPDATE creatives SET hook_transcript=?, first_cut=?, archetype=?, "
        "fingerprint_path=? WHERE ad_name=?",
        (hook_transcript, first_cut, archetype, fingerprint_path, ad_name))
    return cur.rowcount


def _window_where(days):
    """Rows inside the window. ad_date (from the name) is preferred; fall back
    to period_end, then ingested_at, so undated rows are not silently lost."""
    return (
        f"COALESCE("
        f" CASE WHEN ad_date IS NOT NULL THEN "
        f"  substr(ad_date,1,4)||'-'||substr(ad_date,5,2)||'-'||substr(ad_date,7,2)"
        f" END,"
        f" NULLIF(period_end,''), substr(ingested_at,1,10)"
        f") >= date('now', '-{int(days)} day')"
    )


def patterns_aggregate(conn, days=90, platform="Meta"):
    """Deterministic aggregation: thumbstop by archetype x funnel x avatar,
    qualified rows only, prospecting/remarketing split, over the window."""
    rows = conn.execute(
        f"SELECT COALESCE(archetype,'(no autopsy)') archetype, "
        f"COALESCE(funnel_label,'?') funnel, COALESCE(avatar,'?') avatar, "
        f"CASE is_prospecting WHEN 1 THEN 'prospecting' WHEN 0 THEN 'remarketing' "
        f"ELSE 'unknown' END split, "
        f"COUNT(*) n, ROUND(AVG(thumbstop),1) avg_thumbstop, "
        f"ROUND(AVG(hold_rate),1) avg_hold, ROUND(SUM(spend),0) spend "
        f"FROM creatives WHERE {qualified_where()} AND platform=? "
        f"AND {_window_where(days)} "
        f"GROUP BY archetype, funnel, avatar, split "
        f"ORDER BY archetype, split, avg_thumbstop DESC",
        (platform,)).fetchall()
    return [dict(r) for r in rows]


def fatigue_buckets(conn, days=90, platform="Meta"):
    """Descriptive fatigue only: archetype-level thumbstop by 30-day buckets
    (0 = most recent). Flags archetypes down more than 5pts bucket-over-bucket.
    NO predictive fatigue in v1."""
    date_expr = (
        "COALESCE(CASE WHEN ad_date IS NOT NULL THEN "
        "substr(ad_date,1,4)||'-'||substr(ad_date,5,2)||'-'||substr(ad_date,7,2) END,"
        " NULLIF(period_end,''), substr(ingested_at,1,10))")
    rows = conn.execute(
        f"SELECT COALESCE(archetype,'(no autopsy)') archetype, "
        f"CAST(julianday('now') - julianday({date_expr}) AS INT) / 30 bucket, "
        f"COUNT(*) n, ROUND(AVG(thumbstop),1) avg_thumbstop "
        f"FROM creatives WHERE {qualified_where()} AND platform=? "
        f"AND {_window_where(days)} "
        f"GROUP BY archetype, bucket ORDER BY archetype, bucket",
        (platform,)).fetchall()
    by_arch = {}
    for r in rows:
        by_arch.setdefault(r["archetype"], []).append(
            {"bucket": r["bucket"], "n": r["n"],
             "avg_thumbstop": r["avg_thumbstop"]})
    flags = []
    for arch, buckets in by_arch.items():
        buckets.sort(key=lambda b: b["bucket"])  # 0 = most recent 30 days
        for newer, older in zip(buckets, buckets[1:]):
            if (newer["avg_thumbstop"] is not None
                    and older["avg_thumbstop"] is not None
                    and older["avg_thumbstop"] - newer["avg_thumbstop"] > 5):
                flags.append({
                    "archetype": arch,
                    "drop_pts": round(older["avg_thumbstop"] - newer["avg_thumbstop"], 1),
                    "from_bucket": older, "to_bucket": newer,
                })
    return {"buckets": by_arch, "flags": flags}


def top_hooks(conn, top=20):
    return [dict(r) for r in conn.execute(
        f"SELECT ad_name, platform, spend, thumbstop, hold_rate, roas, "
        f"avatar, editor, archetype, is_prospecting, hook_transcript "
        f"FROM creatives WHERE {qualified_where()} "
        f"ORDER BY thumbstop DESC LIMIT ?", (top,)).fetchall()]
