"""PV-Hooks web app: a private upload-and-report page for the editor team.

Wraps the exact same deterministic pipeline + single model call the CLI uses,
so editors never touch a terminal. Run locally with:
    streamlit run app.py
Deployed, editors just open the URL. See DEPLOY.md.

Access is gated by the HOOKS_PASSWORD env var (a shared team password).
The Anthropic key stays server-side in ANTHROPIC_API_KEY and is never shown.
"""

import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data"
DB_PATH = DATA / "bank.db"
VIDEOS_DIR = DATA / "videos"
REPORTS_DIR = DATA / "reports"
DROP_DIR = DATA / "motion_drop"
PREDICTIONS = DATA / "predictions.jsonl"

DEFAULT_MODEL = "claude-sonnet-4-6"
ARCHETYPES = [
    "(let the model classify)", "talking_head_ugc", "screen_record",
    "broll_vo", "text_card", "founder_location", "podcast_interview",
]

st.set_page_config(page_title="PV-Hooks", page_icon="🎬", layout="centered")


# --------------------------------------------------------------------------
# Access gate
# --------------------------------------------------------------------------
def check_password():
    expected = os.environ.get("HOOKS_PASSWORD")
    if not expected:
        # No password configured: allow, but warn the operator loudly.
        st.warning("HOOKS_PASSWORD is not set. This page is currently open to "
                   "anyone with the link. Set the password before sharing.")
        return True
    if st.session_state.get("authed"):
        return True
    st.title("PV-Hooks")
    pw = st.text_input("Team password", type="password")
    if st.button("Enter"):
        if pw == expected:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False


if not check_password():
    st.stop()

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error("ANTHROPIC_API_KEY is not set on the server. Analyze and Patterns "
             "will not work until it is. See DEPLOY.md.")


# --------------------------------------------------------------------------
# Lazy imports (after the gate, so the login screen loads fast)
# --------------------------------------------------------------------------
import bank as bankmod          # noqa: E402
import ingest_video             # noqa: E402
import ingest_motion            # noqa: E402
import autopsy                  # noqa: E402
import calibrate as calmod      # noqa: E402
import report as reportmod      # noqa: E402
from nameparse import parse_name  # noqa: E402


st.sidebar.title("🎬 PV-Hooks")
page = st.sidebar.radio(
    "What do you want to do?",
    ["Analyze a video", "Import Motion data", "Patterns", "Calibration",
     "Hook bank"],
)
st.sidebar.caption("First-3-seconds autopsies, grounded in our own account data.")


# --------------------------------------------------------------------------
# Analyze
# --------------------------------------------------------------------------
if page == "Analyze a video":
    st.header("Analyze a video")
    st.write("Drop in an ad video and get the first-3-seconds breakdown.")

    up = st.file_uploader("Video file", type=["mp4", "mov", "m4v", "webm"])
    col1, col2 = st.columns(2)
    with col1:
        competitor = st.checkbox(
            "Competitor / inspo (no performance join, no prediction)")
        archetype = st.selectbox("Archetype", ARCHETYPES)
    with col2:
        funnel = st.selectbox("Funnel", ["(auto)", "TOF", "MOF", "BOF"])
        product = st.text_input("Product (optional)")
        avatar = st.text_input("Avatar code (optional, e.g. a-NAC)")

    if st.button("Run analysis", type="primary", disabled=up is None):
        arch = None if archetype.startswith("(") else archetype
        fnl = None if funnel.startswith("(") else funnel

        with tempfile.NamedTemporaryFile(
                suffix="_" + up.name, delete=False) as tf:
            tf.write(up.getbuffer())
            tmp_path = tf.name

        try:
            with st.spinner("Extracting frames, cuts, and transcript..."):
                fp = ingest_video.ingest(tmp_path, VIDEOS_DIR)

            parsed = parse_name(Path(up.name).stem)
            context = {
                "product": product or parsed["product"],
                "funnel": fnl or parsed["funnel"],
                "avatar": avatar or parsed["avatar"],
                "competitor": bool(competitor),
            }
            ad_name = None if competitor else Path(up.name).stem

            conn = bankmod.connect(DB_PATH)
            bank_ctx = bankmod.bank_context(
                conn, archetype=arch, avatar=context["avatar"],
                product=context["product"])

            with st.spinner("Asking the model for the autopsy..."):
                result = autopsy.run_autopsy(
                    fp, bank_ctx, context, competitor=competitor,
                    archetype=arch, model=DEFAULT_MODEL)

            if not competitor:
                autopsy.log_prediction(PREDICTIONS, fp, result, ad_name=ad_name)
                hook_words = fp.get("transcript_0_3", {}).get("words", [])
                hook_text = " ".join(w["w"] for w in hook_words)
                if ad_name:
                    bankmod.link_fingerprint(
                        conn, ad_name, hook_text, fp.get("first_cut"),
                        result.get("archetype"),
                        str(Path(fp["file"]["stored_path"]).parent
                            / "fingerprint.json"))
                    conn.commit()

            body = reportmod.render_autopsy(
                result, fp["file"]["name"], context, competitor=competitor)
            reportmod.write_report(REPORTS_DIR, "autopsy", body, echo=False)

            if fp.get("transcript", {}).get("error"):
                st.info("Note: transcription was unavailable for this run, so "
                        "beat timing leaned on the frames and scene cuts.")
            st.success("Done.")
            st.markdown(body)
            st.download_button("Download report (.md)", body,
                               file_name=f"autopsy_{Path(up.name).stem}.md")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
        finally:
            os.unlink(tmp_path)


# --------------------------------------------------------------------------
# Import Motion data
# --------------------------------------------------------------------------
elif page == "Import Motion data":
    st.header("Import Motion data")
    st.write("Drop in one or more Motion CSV exports to update the shared bank. "
             "Put 'tiktok' or 'youtube' in the filename for non-Meta exports.")

    ups = st.file_uploader("Motion CSV export(s)", type=["csv"],
                           accept_multiple_files=True)
    if st.button("Import", type="primary", disabled=not ups):
        DROP_DIR.mkdir(parents=True, exist_ok=True)
        for up in ups:
            (DROP_DIR / up.name).write_bytes(up.getbuffer())
        with st.spinner("Parsing and updating the bank..."):
            conn = bankmod.connect(DB_PATH)
            summary = ingest_motion.ingest_drop(conn, DROP_DIR)
        body = reportmod.render_ingest(summary)
        reportmod.write_report(REPORTS_DIR, "ingest", body, echo=False)
        st.success(f"Added {summary['added']}, updated {summary['updated']}.")
        st.markdown(body)


# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------
elif page == "Patterns":
    st.header("Patterns")
    st.write("What wins by archetype, avatar, and funnel, plus descriptive "
             "fatigue. Reads the shared bank.")
    days = st.slider("Window (days)", 30, 365, 90, step=30)
    if st.button("Build patterns", type="primary"):
        conn = bankmod.connect(DB_PATH)
        stats = bankmod.bank_stats(conn)
        aggregate = bankmod.patterns_aggregate(conn, days=days)
        fatigue = bankmod.fatigue_buckets(conn, days=days)
        if aggregate:
            with st.spinner("Synthesizing findings..."):
                findings = autopsy.synthesize_patterns(
                    aggregate, fatigue, stats, days, model=DEFAULT_MODEL)
        else:
            findings = ("Bank is empty for this window. Import Motion data "
                        "first.")
        body = reportmod.render_patterns(aggregate, fatigue, stats, findings, days)
        reportmod.write_report(REPORTS_DIR, "patterns", body, echo=False)
        st.markdown(body)


# --------------------------------------------------------------------------
# Calibration
# --------------------------------------------------------------------------
elif page == "Calibration":
    st.header("Calibration")
    st.write("How the tool's thumbstop-band predictions held up against actuals.")
    if st.button("Run calibration", type="primary"):
        conn = bankmod.connect(DB_PATH)
        result = calmod.calibrate(conn, PREDICTIONS)
        body = reportmod.render_calibrate(result)
        reportmod.write_report(REPORTS_DIR, "calibrate", body, echo=False)
        st.markdown(body)


# --------------------------------------------------------------------------
# Hook bank
# --------------------------------------------------------------------------
elif page == "Hook bank":
    st.header("Hook bank")
    st.write("The ranked bank, qualified rows only (spend over $2,500).")
    top = st.slider("Show top", 5, 100, 20, step=5)
    if st.button("Show bank", type="primary"):
        conn = bankmod.connect(DB_PATH)
        rows = bankmod.top_hooks(conn, top=top)
        stats = bankmod.bank_stats(conn)
        body = reportmod.render_bank(rows, stats)
        reportmod.write_report(REPORTS_DIR, "bank", body, echo=False)
        st.markdown(body)
