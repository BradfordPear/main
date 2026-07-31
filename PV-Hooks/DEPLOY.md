# Putting PV-Hooks online for the team

Goal: a private web page your 8 editors open in a browser, drop a video onto,
and get the report back. No installs for them. This is a one-time setup of
about an hour. After it's done, you never touch it again unless you want to.

You (or whoever does this) will need two things first:
1. An **Anthropic API key** (from console.anthropic.com). This is what pays for
   the AI. Keep it secret.
2. A **hosting account**. The steps below use **Render** because it's simple,
   keeps the shared data safe, and is about $7/month. Railway or Fly.io work
   the same way if you prefer them.

You do NOT need to understand the code. You're just filling in two secret
boxes and clicking deploy.

---

## Steps (Render)

1. **Get the code onto GitHub.** If you're reading this, it's already in your
   repo. Make sure the `PV-Hooks` folder is on your main branch (open a pull
   request and merge it, or ask whoever set this up).

2. **Make a Render account** at render.com and connect it to your GitHub.

3. In Render, click **New → Blueprint**. Pick your repository. Render finds the
   `render.yaml` file in the `PV-Hooks` folder and reads the whole setup from
   it automatically.

4. Render will ask you to fill in two secret values (it will not let anyone see
   them afterward):
   - `ANTHROPIC_API_KEY` → paste your Anthropic key.
   - `HOOKS_PASSWORD` → make up a shared password for the team (e.g. a couple
     of words). This is what keeps the page private.

5. Click **Apply / Deploy**. Render builds it. First build takes a few minutes
   (it's installing the video tools and the transcription model). When it's
   done, Render gives you a URL like `https://pv-hooks.onrender.com`.

6. **Test it yourself:** open the URL, type the team password, upload one real
   ad video, and confirm a report comes back.

7. **Share with the team:** send the 8 editors the URL and the password. Done.

---

## What each person does day to day

- Open the URL, enter the shared password once.
- **Analyze a video:** drag an ad in, click Run, read the report, download it.
- **Import Motion data:** whoever pulls the Motion CSV export drops it in under
  "Import Motion data" so everyone's reports stay grounded in current numbers.
- **Patterns / Calibration / Hook bank:** the same reports the strategist side
  uses, on tabs in the sidebar.

Everyone shares one data bank and one AI key, both living safely on the server.

---

## The two things worth knowing

- **Cost.** Hosting is about $7/month (the "starter" plan, always on). The AI
  itself is a few cents per video analyzed. For 8 editors at normal volume,
  expect low tens of dollars a month total. You can watch usage in the
  Anthropic console.

- **The shared data is on a saved disk.** The `render.yaml` sets up a 5GB disk
  mounted at `/app/data`, so the bank, your imported Motion history, and past
  reports survive updates and restarts. Don't remove that disk setting, or the
  bank would reset each time the app updates.

---

## If you'd rather run it on your own laptop first (optional)

Before paying for hosting, anyone comfortable with a terminal can try it locally:

```
cd PV-Hooks
pip install --break-system-packages -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export HOOKS_PASSWORD=whatever-you-like
streamlit run app.py
```

It opens in your browser at `http://localhost:8501`. Same page the team would
see, just running on that one computer instead of the cloud.
