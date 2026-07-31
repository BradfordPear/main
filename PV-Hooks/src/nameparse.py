"""Parser for the PV/WP 14-position underscore-delimited ad naming convention.

Format_YYYYMMDD_ConceptName_Product_Offer_Format_Style_Objective_Funnel_a-AVATAR_Platform_cr-XX_v#_...

Real names drift, so this anchors on the reliable tokens (date, a-AVATAR,
cr-XX, funnel, lp*, v#, platform) instead of strict position counting.
Never raises on a bad name: unparseable fields come back as None and the
raw name is preserved so malformed rows stay searchable.
"""

import re
from datetime import datetime

KNOWN_AVATARS = {
    # Paleovalley
    "a-NAC", "a-SUS", "a-LIS", "a-MIK", "a-JNF", "a-SAR", "a-CLR", "a-MAY", "a-DISC",
    # Wild Pastures
    "a-AVA", "a-EVA", "a-CRN", "a-MIA", "a-JCP",
}
FUNNELS = {"TOF", "MOF", "BOF", "NoDisc", "SA"}
PLATFORMS = {"Meta", "TikTok", "YouTube", "YT", "AppLovin"}

DATE_RE = re.compile(r"^\d{8}$")
AVATAR_RE = re.compile(r"^a-[A-Z]{2,5}$")
EDITOR_RE = re.compile(r"^cr-[A-Za-z]{2}$")
VERSION_RE = re.compile(r"^v\d+$")

FIELDS = (
    "fmt", "ad_date", "concept", "product", "offer", "style", "objective",
    "funnel", "avatar", "platform", "editor", "version", "landing_page",
)


def _valid_date(token):
    try:
        datetime.strptime(token, "%Y%m%d")
        return True
    except ValueError:
        return False


def parse_name(name):
    """Parse an ad name. Returns a dict with None for anything unparseable,
    the raw name intact, and a parse_warnings list. Never raises."""
    result = {f: None for f in FIELDS}
    result["raw_name"] = name
    result["parse_warnings"] = []
    warnings = result["parse_warnings"]

    if not isinstance(name, str) or not name.strip():
        warnings.append("empty or non-string name")
        return result

    tokens = name.strip().split("_")
    if len(tokens) < 3:
        warnings.append(f"only {len(tokens)} tokens, expected ~14")

    claimed = set()  # indices consumed by anchor tokens

    # Anchor pass: reliable, position-independent tokens.
    for i, tok in enumerate(tokens):
        if result["ad_date"] is None and DATE_RE.match(tok) and _valid_date(tok):
            result["ad_date"] = tok
            claimed.add(i)
        elif result["avatar"] is None and AVATAR_RE.match(tok):
            result["avatar"] = tok
            claimed.add(i)
            if tok not in KNOWN_AVATARS:
                warnings.append(f"unknown avatar token {tok}")
        elif result["editor"] is None and EDITOR_RE.match(tok):
            result["editor"] = tok
            claimed.add(i)
        elif result["funnel"] is None and tok in FUNNELS:
            result["funnel"] = tok
            claimed.add(i)
        elif result["version"] is None and VERSION_RE.match(tok):
            result["version"] = tok
            claimed.add(i)
        elif result["platform"] is None and tok in PLATFORMS:
            result["platform"] = tok
            claimed.add(i)
        elif result["landing_page"] is None and tok.startswith("lp") and len(tok) > 2:
            result["landing_page"] = tok
            claimed.add(i)

    if result["ad_date"] is None:
        warnings.append("no YYYYMMDD date token found")
    if result["avatar"] is None:
        warnings.append("no a-AVATAR token found")

    # Positional pass, relative to the date anchor: the tokens right around
    # the date are the most stable positions in practice.
    date_idx = None
    for i, tok in enumerate(tokens):
        if tokens[i] == result["ad_date"] and i in claimed:
            date_idx = i
            break

    def take(idx, field):
        if idx is not None and 0 <= idx < len(tokens) and idx not in claimed:
            result[field] = tokens[idx]
            claimed.add(idx)

    if date_idx is not None:
        take(date_idx - 1, "fmt")       # Format precedes the date
        take(date_idx + 1, "concept")   # ConceptName follows it
        take(date_idx + 2, "product")
        take(date_idx + 3, "offer")
        # date_idx + 4 is the second Format slot; skip it (redundant with fmt)
        take(date_idx + 5, "style")
        take(date_idx + 6, "objective")
    else:
        # No date anchor: best effort on leading tokens only.
        take(0, "fmt")
        take(1, "concept")
        take(2, "product")

    return result
