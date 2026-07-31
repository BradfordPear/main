# PV-Hooks

Deconstructs the first 3 seconds of PV / Wild Pastures paid social videos, grounded in our own Motion performance data. The model only pays for judgment: frames, cuts, transcription, CSV parsing, and DB joins are all deterministic Python.

## Install

```
# system: ffmpeg on PATH (brew install ffmpeg / apt install ffmpeg)
pip install --break-system-packages faster-whisper anthropic pillow
export ANTHROPIC_API_KEY=sk-ant-...
```

Python 3.11+. First `analyze` downloads the whisper base.en model (~75MB).

## The 5 commands

```
./hooks analyze <video> [--competitor] [--archetype ID] [--funnel TOF|MOF|BOF] [--avatar NAME] [--product NAME]
./hooks ingest                # parse everything new in data/motion_drop/
./hooks patterns [--days 90]  # what wins by archetype/avatar/funnel + descriptive fatigue
./hooks calibrate             # predicted vs actual thumbstop bands
./hooks bank [--top 20]       # ranked hook bank sanity check
```

Every command writes a markdown report to `data/reports/` and prints it.

- `analyze` fingerprints the video (frames at 0-5s, scene cuts, word-timestamped transcript), pulls account benchmarks and nearest neighbors from the bank, and returns a structured autopsy. Non-competitor runs log a thumbstop-band prediction to `data/predictions.jsonl`.
- `--competitor` skips the performance join and prediction and returns a transplant spec instead.
- Re-running `analyze` on the same file reuses the cached fingerprint.
- Benchmarks split prospecting (NC campaigns) vs remarketing (RC), never blended. Spend floor for anything benchmark-facing is $2,500.

## Motion CSV export steps

1. In Motion, open the creative report for the period you want (Meta; TikTok/YouTube exports work too).
2. Include at least: Ad Name, Campaign Name, Spend, Thumbstop, Hold Rate, CTR, ROAS. Extra columns are ignored; header names are matched loosely.
3. Export as CSV and drop the file into `data/motion_drop/`. Put "tiktok" or "youtube" in the filename for non-Meta exports.
4. Run `./hooks ingest`. Already-ingested files are skipped; re-ingesting the same CSV adds zero duplicate rows.

Malformed ad names never crash anything; they are stored with the raw name intact and listed in the ingest report.
