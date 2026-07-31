"""Deterministic video ingestion: ffmpeg + faster-whisper -> fingerprint JSON.

Everything here is mechanical. The model never sees raw video; it gets the
fingerprint this module produces plus a handful of frames.
"""

import hashlib
import json
import shutil
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path

FRAME_TIMES = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
SCENE_THRESHOLD = 0.3
SCENE_WINDOW_S = 6.0
MAX_FRAME_WIDTH = 720
LOW_RES_HEIGHT = 480


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _run(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def probe(path):
    """Duration, width, height via ffprobe."""
    r = _run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "json", str(path),
    ])
    info = json.loads(r.stdout or "{}")
    stream = (info.get("streams") or [{}])[0]
    duration = float((info.get("format") or {}).get("duration") or 0.0)
    return duration, int(stream.get("width") or 0), int(stream.get("height") or 0)


def extract_frames(path, out_dir, duration):
    """JPEG frames at the fixed timestamps, max width 720px."""
    frames = []
    for t in FRAME_TIMES:
        if duration and t > duration:
            continue
        out = out_dir / f"frame_{t:.1f}s.jpg"
        r = _run([
            "ffmpeg", "-y", "-ss", str(t), "-i", str(path),
            "-frames:v", "1",
            "-vf", f"scale='min({MAX_FRAME_WIDTH},iw)':-2",
            "-q:v", "4", str(out),
        ])
        if r.returncode == 0 and out.exists():
            frames.append({"t": t, "path": str(out)})
    return frames


def detect_cuts(path):
    """Scene cut timestamps in the first 6 seconds, parsed from showinfo
    stderr. Measured fact, never model-inferred."""
    r = _run([
        "ffmpeg", "-t", str(SCENE_WINDOW_S), "-i", str(path),
        "-vf", f"select='gt(scene,{SCENE_THRESHOLD})',showinfo",
        "-f", "null", "-",
    ])
    cuts = []
    for m in re.finditer(r"pts_time:(\d+(?:\.\d+)?)", r.stderr):
        t = float(m.group(1))
        if t <= SCENE_WINDOW_S:
            cuts.append(round(t, 3))
    return sorted(set(cuts))


def extract_audio(path, out_dir):
    wav = out_dir / "audio.wav"
    r = _run([
        "ffmpeg", "-y", "-i", str(path), "-vn",
        "-ac", "1", "-ar", "16000", str(wav),
    ])
    return wav if r.returncode == 0 and wav.exists() else None


def transcribe(wav_path):
    """faster-whisper base.en, int8, VAD, word timestamps."""
    from faster_whisper import WhisperModel
    model = WhisperModel("base.en", compute_type="int8")
    segments, _info = model.transcribe(
        str(wav_path), vad_filter=True, word_timestamps=True,
    )
    words = []
    text_parts = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        for w in seg.words or []:
            words.append({"w": w.word.strip(), "start": round(w.start, 2),
                          "end": round(w.end, 2)})
    return {"text": " ".join(text_parts).strip(), "words": words}


def slice_words(words, start, end):
    return [w for w in words if w["start"] < end and w["end"] > start]


def ingest(video_path, videos_dir):
    """Full ingestion. Caches on file hash: if a fingerprint already exists
    for this hash, return it without re-processing."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"no such video: {video_path}")

    vhash = file_hash(video_path)
    out_dir = Path(videos_dir) / vhash
    fp_path = out_dir / "fingerprint.json"

    if fp_path.exists():
        with open(fp_path) as f:
            fp = json.load(f)
        # A cached fingerprint with a failed transcription (e.g. the whisper
        # model download failed last time) gets one more shot at the audio;
        # everything else stays cached.
        if "error" in fp.get("transcript", {}):
            wav = extract_audio(fp["file"]["stored_path"], out_dir)
            if wav is not None:
                try:
                    fp["transcript"] = transcribe(wav)
                    fp["transcript_0_3"]["words"] = slice_words(
                        fp["transcript"]["words"], 0.0, 3.0)
                    with open(fp_path, "w") as f:
                        json.dump(fp, f, indent=2)
                except Exception as e:
                    fp["transcript"]["error"] = str(e)
                finally:
                    wav.unlink(missing_ok=True)
        fp["cached"] = True
        return fp

    out_dir.mkdir(parents=True, exist_ok=True)
    local_copy = out_dir / video_path.name
    if not local_copy.exists():
        shutil.copy2(video_path, local_copy)

    duration, width, height = probe(local_copy)
    frames = extract_frames(local_copy, out_dir, duration)
    cuts = detect_cuts(local_copy)

    transcript = {"text": "", "words": []}
    wav = extract_audio(local_copy, out_dir)
    if wav is not None:
        try:
            transcript = transcribe(wav)
        except Exception as e:
            transcript = {"text": "", "words": [], "error": str(e)}
        finally:
            wav.unlink(missing_ok=True)

    fingerprint = {
        "file": {
            "name": video_path.name,
            "source_path": str(video_path),
            "stored_path": str(local_copy),
            "hash": vhash,
            "size_bytes": video_path.stat().st_size,
        },
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "low_res": bool(height and height < LOW_RES_HEIGHT),
        "cuts": cuts,
        "first_cut": cuts[0] if cuts else None,
        "transcript": transcript,
        "transcript_0_3": {
            "note": "0-3s slice, the hook window",
            "words": slice_words(transcript.get("words", []), 0.0, 3.0),
        },
        "frames": frames,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
    }

    with open(fp_path, "w") as f:
        json.dump(fingerprint, f, indent=2)
    return fingerprint
