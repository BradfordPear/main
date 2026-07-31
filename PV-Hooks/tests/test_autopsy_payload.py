import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import bank as bankmod
import autopsy


def make_fingerprint(tmp_path, n_frames=7):
    """Fingerprint with 7 frame files on disk; only the six 0-3s frames may
    reach the model."""
    frames = []
    times = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0][:n_frames]
    for t in times:
        p = tmp_path / f"frame_{t:.1f}s.jpg"
        p.write_bytes(b"\xff\xd8\xff\xe0fakejpeg")
        frames.append({"t": t, "path": str(p)})
    return {
        "file": {"name": "test.mp4", "hash": "abc123", "stored_path": str(tmp_path / "test.mp4")},
        "duration": 8.0, "width": 720, "height": 1280, "low_res": False,
        "cuts": [1.2], "first_cut": 1.2,
        "transcript": {"text": "hello world", "words": []},
        "transcript_0_3": {"words": [{"w": "hello", "start": 0.1, "end": 0.4}]},
        "frames": frames,
    }


def valid_result():
    return {
        "archetype": "talking_head_ugc",
        "beat_map": [{"t": 0.0, "channel": "spoken", "event": "line opens", "ok": True}],
        "load_bearing": {"primary_channel": "spoken", "mute_test": "no",
                         "cover_test": "yes", "protect_in_recut": "the line"},
        "tactic": "curiosity open",
        "why_it_works_or_doesnt": "mechanism.",
        "bank_comparison": {"nearest": [], "read": "UNGROUNDED", "distinct_or_duplicate": "new"},
        "prediction": {"thumbstop_band": "floor-to-strong", "confidence": "low", "basis": "thin bank"},
        "fix": "tighten the first cut",
        "editor_moves": ["cut at 1.2s", "text on at 0.5s"],
        "compliance_flag": "",
        "caveat": "could be wrong",
    }


class FakeResponse:
    def __init__(self, text):
        block = types.SimpleNamespace(type="text", text=text)
        self.content = [block]


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

        outer = self

        class Messages:
            def create(self, **kwargs):
                outer.calls.append(kwargs)
                return FakeResponse(outer.replies.pop(0))

        self.messages = Messages()


def install_fake_anthropic(monkeypatch, client):
    fake_mod = types.ModuleType("anthropic")
    fake_mod.Anthropic = lambda: client
    monkeypatch.setitem(sys.modules, "anthropic", fake_mod)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_payload_never_exceeds_seven_images(tmp_path):
    fp = make_fingerprint(tmp_path)
    conn = bankmod.connect(tmp_path / "bank.db")
    ctx = bankmod.bank_context(conn)
    parts = autopsy.build_payload(fp, ctx, {"product": None})
    n_images = sum(1 for p in parts if p.get("type") == "image")
    assert n_images == 6          # only the 0-3s frames, 5.0s excluded
    assert n_images <= autopsy.MAX_IMAGES
    # no raw video anywhere in the payload
    assert not any("stored_path" in json.dumps(p) for p in parts)


def test_empty_bank_payload_says_ungrounded(tmp_path):
    conn = bankmod.connect(tmp_path / "bank.db")
    ctx = bankmod.bank_context(conn)
    assert ctx["bank_thin"] is True
    assert "UNGROUNDED" in ctx["instruction"]


def test_run_autopsy_valid_first_try(tmp_path, monkeypatch):
    fp = make_fingerprint(tmp_path)
    conn = bankmod.connect(tmp_path / "bank.db")
    ctx = bankmod.bank_context(conn)
    client = FakeClient([json.dumps(valid_result())])
    install_fake_anthropic(monkeypatch, client)
    result = autopsy.run_autopsy(fp, ctx, {"funnel": "TOF"})
    assert result["archetype"] == "talking_head_ugc"
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == "claude-sonnet-4-6"


def test_run_autopsy_retries_once_on_bad_json(tmp_path, monkeypatch):
    fp = make_fingerprint(tmp_path)
    conn = bankmod.connect(tmp_path / "bank.db")
    ctx = bankmod.bank_context(conn)
    client = FakeClient(["not json at all",
                         "```json\n" + json.dumps(valid_result()) + "\n```"])
    install_fake_anthropic(monkeypatch, client)
    result = autopsy.run_autopsy(fp, ctx, {})
    assert result["fix"] == "tighten the first cut"
    assert len(client.calls) == 2


def test_run_autopsy_fails_after_two_bad(tmp_path, monkeypatch):
    fp = make_fingerprint(tmp_path)
    conn = bankmod.connect(tmp_path / "bank.db")
    ctx = bankmod.bank_context(conn)
    client = FakeClient(["nope", "still nope"])
    install_fake_anthropic(monkeypatch, client)
    try:
        autopsy.run_autopsy(fp, ctx, {})
        raise AssertionError("expected RuntimeError")
    except RuntimeError as e:
        assert "twice" in str(e)


def test_competitor_mode_requires_transplant_spec(tmp_path, monkeypatch):
    fp = make_fingerprint(tmp_path)
    conn = bankmod.connect(tmp_path / "bank.db")
    ctx = bankmod.bank_context(conn)
    comp = valid_result()
    del comp["bank_comparison"], comp["prediction"]
    comp["pattern_in_our_bank"] = "no, new to us"
    comp["transplant_spec"] = {"product": "BS", "avatar": "a-NAC",
                               "what_survives": "x", "what_changes": "y",
                               "footage_needed": "z", "entity_id_note": "new"}
    client = FakeClient([json.dumps(comp)])
    install_fake_anthropic(monkeypatch, client)
    result = autopsy.run_autopsy(fp, ctx, {}, competitor=True)
    assert result["transplant_spec"]["product"] == "BS"


def test_prediction_logging(tmp_path):
    fp = make_fingerprint(tmp_path)
    entry = autopsy.log_prediction(tmp_path / "predictions.jsonl", fp,
                                   valid_result(), ad_name="some_ad")
    assert entry["predicted_band"] == "floor-to-strong"
    lines = (tmp_path / "predictions.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["video_hash"] == "abc123"
