# PV-Hooks web app. Includes ffmpeg (needed for frames, cuts, audio).
FROM python:3.11-slim

# ffmpeg is a system dependency, not a pip package.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-cache the whisper model into the image so the first analysis is fast.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base.en', compute_type='int8')" || true

# The shared bank and reports live under /app/data. On a host with a
# persistent disk, mount it at /app/data so nothing is lost on redeploy.
ENV STREAMLIT_SERVER_HEADLESS=true

EXPOSE 8501
# $PORT is provided by most hosts (Render, Railway); default to 8501 locally.
CMD streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
