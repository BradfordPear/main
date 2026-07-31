"""Autopsy: build the model payload, call the Anthropic API, validate JSON.

The model only ever pays for judgment. It receives the system rubric, the
0-3s fingerprint slice, up to 6 frames, context, and the bank block. Never
raw video, never more than 7 images (enforced here).
"""

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_IMAGES = 7
MAX_TOKENS = 8000

REQUIRED_KEYS = [
    "archetype", "beat_map", "load_bearing", "tactic",
    "why_it_works_or_doesnt", "prediction", "fix", "editor_moves",
    "compliance_flag", "caveat", "bank_comparison",
]
COMPETITOR_KEYS = [
    "archetype", "beat_map", "load_bearing", "tactic",
    "why_it_works_or_doesnt", "fix", "editor_moves", "compliance_flag",
    "caveat", "pattern_in_our_bank", "transplant_spec",
]

OUTPUT_SCHEMA = """{
  "archetype": "",
  "beat_map": [{"t": 0.0, "channel": "spoken|text|visual", "event": "", "ok": true}],
  "load_bearing": {
    "primary_channel": "spoken|text|visual",
    "mute_test": "does it still stop with sound off - why",
    "cover_test": "does it still stop with banner covered - why",
    "protect_in_recut": "the one element an editor must not lose"
  },
  "tactic": "",
  "why_it_works_or_doesnt": "3-4 sentences, mechanism not vibes",
  "bank_comparison": {
    "nearest": [{"ad_name": "", "thumbstop": 0, "structural_match": ""}],
    "read": "what our account history says about this structure. UNGROUNDED if bank thin.",
    "distinct_or_duplicate": "new structure for us or a re-skin - Andromeda framing: cosmetic swaps share an Entity ID"
  },
  "prediction": {"thumbstop_band": "sub-floor|floor-to-strong|strong-plus", "confidence": "low|med|high", "basis": ""},
  "fix": "single highest-leverage change, concrete",
  "editor_moves": ["2-3 timeline-level actions: cut points, text timing, audio entry, frame choice"],
  "compliance_flag": "empty if clean; else the risky phrase",
  "caveat": "one line on where this read could be wrong"
}"""

COMPETITOR_SCHEMA_NOTE = """This is COMPETITOR MODE. There is no performance join and no prediction.
Replace "bank_comparison" and "prediction" in the schema with exactly these two fields:

"pattern_in_our_bank": "do we already run this structure - cite nearest ad names + thumbstop if yes",
"transplant_spec": {"product": "", "avatar": "", "what_survives": "", "what_changes": "", "footage_needed": "", "entity_id_note": "genuinely new footage/format/emotion or a re-skin?"}

The transplant spec must be handoff-ready for the pv-format-transplant workflow:
copy direction in plain human language, no marketing speak, no em dashes."""


def load_rubric(rubric_dir):
    return (Path(rubric_dir) / "autopsy_system.md").read_text()


def _frame_blocks(fingerprint):
    """Up to 6 base64 JPEG blocks from the 0-3s window."""
    blocks = []
    for fr in fingerprint.get("frames", []):
        if fr["t"] > 3.0:
            continue
        p = Path(fr["path"])
        if not p.exists():
            continue
        data = base64.standard_b64encode(p.read_bytes()).decode()
        blocks.append({"type": "text", "text": f"Frame at t={fr['t']}s:"})
        blocks.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg",
                       "data": data},
        })
    n_images = sum(1 for b in blocks if b["type"] == "image")
    assert n_images <= MAX_IMAGES, f"{n_images} images exceeds cap of {MAX_IMAGES}"
    return blocks


def _fingerprint_slice(fingerprint):
    """The small structured slice the model sees. Never the raw video."""
    return {
        "duration_s": fingerprint.get("duration"),
        "resolution": f"{fingerprint.get('width')}x{fingerprint.get('height')}",
        "low_res": fingerprint.get("low_res", False),
        "scene_cuts_0_6s": fingerprint.get("cuts", []),
        "first_cut_s": fingerprint.get("first_cut"),
        "transcript_0_3s_words": fingerprint.get("transcript_0_3", {}).get("words", []),
        "full_transcript": fingerprint.get("transcript", {}).get("text", ""),
    }


def build_payload(fingerprint, bank_ctx, context, competitor=False,
                  archetype=None):
    """Returns the user-content block list for the API call."""
    parts = []
    task = ["Deconstruct the first 3 seconds of this paid social ad."]
    if archetype:
        task.append(f"Archetype is pre-selected: {archetype}. Judge against it.")
    else:
        task.append("Classify the archetype first, then judge against it.")
    task.append(f"Context: {json.dumps(context)}")
    task.append("Fingerprint (0-3s slice, measured facts):")
    task.append(json.dumps(_fingerprint_slice(fingerprint), indent=1))
    if competitor:
        parts.append({"type": "text", "text": "\n".join(task)})
        parts.extend(_frame_blocks(fingerprint))
        parts.append({"type": "text", "text": (
            "Bank context (for pattern_in_our_bank only):\n"
            + json.dumps(bank_ctx, indent=1)
            + "\n\n" + COMPETITOR_SCHEMA_NOTE
            + "\n\nRespond with strict JSON matching this base schema, with the "
              "two competitor-mode replacements applied:\n" + OUTPUT_SCHEMA)})
    else:
        parts.append({"type": "text", "text": "\n".join(task)})
        parts.extend(_frame_blocks(fingerprint))
        parts.append({"type": "text", "text": (
            "Bank context:\n" + json.dumps(bank_ctx, indent=1)
            + "\n\nRespond with strict JSON matching exactly this schema:\n"
            + OUTPUT_SCHEMA)})
    return parts


def _extract_json(text):
    """Parse a JSON object out of model text, tolerating code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in response")
    return json.loads(text[start:end + 1])


def _validate(result, competitor):
    keys = COMPETITOR_KEYS if competitor else REQUIRED_KEYS
    missing = [k for k in keys if k not in result]
    if missing:
        raise ValueError(f"missing keys: {missing}")
    return result


def run_autopsy(fingerprint, bank_ctx, context, competitor=False,
                archetype=None, model=DEFAULT_MODEL):
    """One model call, validate JSON, retry once on parse/validation failure."""
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it before running analyze.")

    client = anthropic.Anthropic()
    system = load_rubric(Path(__file__).resolve().parent.parent / "rubric")
    content = build_payload(fingerprint, bank_ctx, context,
                            competitor=competitor, archetype=archetype)
    messages = [{"role": "user", "content": content}]

    last_err = None
    for attempt in range(2):
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            thinking={"type": "adaptive"},
            messages=messages,
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        try:
            return _validate(_extract_json(text), competitor)
        except (ValueError, json.JSONDecodeError) as e:
            last_err = e
            if attempt == 0:
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": (
                    f"That response failed JSON validation ({e}). Respond again "
                    "with ONLY the strict JSON object, no fences, no prose, "
                    "every required field present.")})
    raise RuntimeError(f"model output failed validation twice: {last_err}")


def synthesize_patterns(aggregate, fatigue, stats, days, model=DEFAULT_MODEL):
    """One model call: turn the deterministic patterns tables into
    strategist-facing findings. Text out, not JSON."""
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it before running patterns.")

    client = anthropic.Anthropic()
    prompt = (
        "You are a senior performance creative strategist for Paleovalley and "
        "Wild Pastures. Below are deterministic aggregates from our own ad "
        "account bank (Motion exports), qualified rows only (spend >= $2,500), "
        f"last {days} days, prospecting and remarketing never blended. "
        "Thumbstop reference: editor floor 23%, strong 33% (Meta video).\n\n"
        "Write 4-8 tight strategist-facing findings: what wins by archetype, "
        "avatar, and funnel, and what the descriptive fatigue flags mean. "
        "Cite the numbers you use. If a cell has n < 5, say the sample is too "
        "small to act on rather than reading it as signal. No corporate "
        "filler, no em dashes, no invented data.\n\n"
        f"Bank coverage: {json.dumps(stats)}\n\n"
        f"Thumbstop by archetype x funnel x avatar:\n{json.dumps(aggregate, indent=1)}\n\n"
        f"Fatigue (30-day buckets, bucket 0 = most recent; flags are drops "
        f">5pts bucket-over-bucket):\n{json.dumps(fatigue, indent=1)}"
    )
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def log_prediction(predictions_path, fingerprint, result, ad_name=None):
    """Append to predictions.jsonl. Non-competitor runs only. Feeds calibrate."""
    pred = result.get("prediction") or {}
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "video_hash": fingerprint["file"]["hash"],
        "ad_name": ad_name,
        "archetype": result.get("archetype"),
        "predicted_band": pred.get("thumbstop_band"),
        "confidence": pred.get("confidence"),
    }
    path = Path(predictions_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
