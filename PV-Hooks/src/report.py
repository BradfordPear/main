"""Markdown report rendering. Every command writes one file to data/reports/
and prints it. Style: tight, human, no corporate filler, no em dashes."""

from datetime import datetime, timezone
from pathlib import Path


def write_report(reports_dir, kind, body, echo=True):
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"{stamp}_{kind}.md"
    path.write_text(body)
    if echo:
        print(body)
        print(f"\n[report written to {path}]")
    return path


def _beat_map_table(beats):
    lines = ["| t | channel | event | ok |", "|---|---------|-------|----|"]
    for b in beats or []:
        ok = "yes" if b.get("ok") else "NO"
        lines.append(f"| {b.get('t', '?')}s | {b.get('channel', '?')} "
                     f"| {b.get('event', '')} | {ok} |")
    return "\n".join(lines)


def _verdict_line(result, competitor):
    arch = result.get("archetype", "?")
    if competitor:
        return f"**Competitor read. Archetype: {arch}.** {result.get('tactic', '')}"
    pred = result.get("prediction") or {}
    return (f"**Archetype: {arch}. Predicted: "
            f"{pred.get('thumbstop_band', '?')} "
            f"({pred.get('confidence', '?')} confidence).** "
            f"{result.get('tactic', '')}")


def render_autopsy(result, video_name, context, competitor=False):
    """Order: verdict, beat map, load-bearing, bank read, fix, editor moves,
    compliance, caveat. Editor moves stay in editor language."""
    lb = result.get("load_bearing") or {}
    lines = [
        f"# Hook autopsy: {video_name}",
        "",
        _verdict_line(result, competitor),
        "",
        f"Context: {', '.join(f'{k}={v}' for k, v in context.items() if v) or 'none supplied'}",
        "",
        "## Beat map (0-3s)",
        "",
        _beat_map_table(result.get("beat_map")),
        "",
        "## Load-bearing analysis",
        "",
        f"- Primary channel: **{lb.get('primary_channel', '?')}**",
        f"- Mute test: {lb.get('mute_test', '')}",
        f"- Cover test: {lb.get('cover_test', '')}",
        f"- Protect in recut: {lb.get('protect_in_recut', '')}",
        "",
        "## Why it works or doesn't",
        "",
        result.get("why_it_works_or_doesnt", ""),
        "",
    ]

    if competitor:
        ts = result.get("transplant_spec") or {}
        lines += [
            "## Pattern in our bank",
            "",
            result.get("pattern_in_our_bank", ""),
            "",
            "## Transplant spec",
            "",
            f"- Product: {ts.get('product', '')}",
            f"- Avatar: {ts.get('avatar', '')}",
            f"- What survives: {ts.get('what_survives', '')}",
            f"- What changes: {ts.get('what_changes', '')}",
            f"- Footage needed: {ts.get('footage_needed', '')}",
            f"- Entity ID note: {ts.get('entity_id_note', '')}",
            "",
        ]
    else:
        bc = result.get("bank_comparison") or {}
        lines += ["## Bank read", ""]
        for nb in bc.get("nearest") or []:
            lines.append(f"- `{nb.get('ad_name', '?')}` "
                         f"(thumbstop {nb.get('thumbstop', '?')}): "
                         f"{nb.get('structural_match', '')}")
        lines += [
            "",
            bc.get("read", ""),
            "",
            f"Distinct or duplicate: {bc.get('distinct_or_duplicate', '')}",
            "",
        ]
        pred = result.get("prediction") or {}
        lines += [
            "## Prediction",
            "",
            f"Thumbstop band **{pred.get('thumbstop_band', '?')}**, "
            f"confidence {pred.get('confidence', '?')}. "
            f"Basis: {pred.get('basis', '')}",
            "",
        ]

    lines += [
        "## Fix",
        "",
        result.get("fix", ""),
        "",
        "## Editor moves",
        "",
    ]
    for mv in result.get("editor_moves") or []:
        lines.append(f"- {mv}")
    compliance = result.get("compliance_flag") or ""
    lines += [
        "",
        "## Compliance",
        "",
        "Clean." if not compliance.strip() else f"FLAG: {compliance}",
        "",
        "## Caveat",
        "",
        result.get("caveat", ""),
        "",
    ]
    return "\n".join(lines)


def render_ingest(summary):
    lines = ["# Ingest", ""]
    if summary["files"]:
        lines.append("Files parsed: " + ", ".join(summary["files"]))
    if summary["skipped"]:
        lines.append("Skipped (already ingested): " + ", ".join(summary["skipped"]))
    if not summary["files"] and not summary["skipped"]:
        lines.append("Nothing in data/motion_drop/.")
    b = summary["bank"]
    lines += [
        "",
        f"- Rows added: {summary['added']}",
        f"- Rows updated: {summary['updated']}",
        f"- Unparseable names: {len(summary['unparseable'])}",
        f"- Bank size: {b['total']} rows, {b['qualified']} over the $2,500 floor",
        f"- Coverage: {b['coverage_pct']}% of qualified rows have a linked fingerprint",
    ]
    if summary["unparseable"]:
        lines += ["", "## Unparseable names", ""]
        for u in summary["unparseable"][:50]:
            lines.append(f"- {u}")
        if len(summary["unparseable"]) > 50:
            lines.append(f"- ...and {len(summary['unparseable']) - 50} more")
    return "\n".join(lines) + "\n"


def render_patterns(aggregate, fatigue, stats, findings, days):
    lines = [
        f"# Patterns, last {days} days",
        "",
        f"Bank coverage: {stats['qualified']} qualified rows "
        f"({stats['total']} total), {stats['coverage_pct']}% with a linked "
        "fingerprint. Thin cells are noted below; do not read them as signal.",
        "",
        "## Thumbstop by archetype x funnel x avatar (qualified only)",
        "",
        "| archetype | split | funnel | avatar | n | thumbstop | hold | spend |",
        "|-----------|-------|--------|--------|---|-----------|------|-------|",
    ]
    for r in aggregate:
        lines.append(
            f"| {r['archetype']} | {r['split']} | {r['funnel']} | {r['avatar']} "
            f"| {r['n']} | {r['avg_thumbstop']} | {r['avg_hold']} | ${r['spend']:,.0f} |")
    if not aggregate:
        lines.append("| (no qualified rows in window) | | | | | | | |")

    lines += ["", "## Descriptive fatigue (30-day buckets)", ""]
    flags = fatigue["flags"]
    if flags:
        for fl in flags:
            lines.append(
                f"- **{fl['archetype']}** down {fl['drop_pts']}pts: "
                f"{fl['from_bucket']['avg_thumbstop']} "
                f"(n={fl['from_bucket']['n']}) to "
                f"{fl['to_bucket']['avg_thumbstop']} "
                f"(n={fl['to_bucket']['n']}) bucket-over-bucket.")
    else:
        lines.append("No archetype down more than 5pts bucket-over-bucket.")

    lines += ["", "## Findings", "", findings or "(no model synthesis)", ""]
    return "\n".join(lines)


def render_calibrate(result):
    n = result["n_matched"]
    lines = [
        "# Calibration",
        "",
        f"**{n} matched predictions. Below 20, treat everything here as anecdote.**",
        "",
        f"- Predictions logged: {result['n_predictions_total']}",
        f"- Matched to actuals (spend >= $2,500): {n}",
        f"- Exact-band hit rate: {result['exact_rate']}%" if n else "- Exact-band hit rate: n/a",
        f"- Adjacent-band rate: {result['adjacent_rate']}%" if n else "- Adjacent-band rate: n/a",
        "",
        "## Per archetype",
        "",
        "| archetype | n | exact | adjacent |",
        "|-----------|---|-------|----------|",
    ]
    for arch, a in sorted(result["per_archetype"].items()):
        lines.append(f"| {arch} | {a['n']} | {a['exact']} | {a['adjacent']} |")
    if not result["per_archetype"]:
        lines.append("| (none) | | | |")

    lines += ["", "## Worst misses", ""]
    if result["worst_misses"]:
        for m in result["worst_misses"]:
            lines.append(
                f"- `{m['ad_name']}`: predicted {m['predicted_band']}, actual "
                f"{m['actual_band']} ({m['actual_thumbstop']}%), "
                f"confidence {m['confidence']}")
    else:
        lines.append("No misses among matched predictions.")
    return "\n".join(lines) + "\n"


def render_bank(rows, stats):
    lines = [
        "# Hook bank",
        "",
        f"{stats['qualified']} qualified rows of {stats['total']} total. "
        f"{stats['coverage_pct']}% linked to a fingerprint.",
        "",
        "| # | ad_name | platform | split | thumbstop | hold | spend | roas | avatar | editor | archetype |",
        "|---|---------|----------|-------|-----------|------|-------|------|--------|--------|-----------|",
    ]
    for i, r in enumerate(rows, 1):
        split = {1: "NC", 0: "RC"}.get(r["is_prospecting"], "?")
        lines.append(
            f"| {i} | `{r['ad_name'][:60]}` | {r['platform']} | {split} "
            f"| {r['thumbstop']} | {r['hold_rate']} | ${r['spend']:,.0f} "
            f"| {r['roas'] if r['roas'] is not None else ''} | {r['avatar'] or ''} "
            f"| {r['editor'] or ''} | {r['archetype'] or ''} |")
    if not rows:
        lines.append("| (empty: nothing over the $2,500 floor) | | | | | | | | | | |")
    return "\n".join(lines) + "\n"
