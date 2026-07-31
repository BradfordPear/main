# 👑 Dethrone

A single-phone, pass-around social debate party game. One device, one screen, played
out loud in a group. A champion holds the throne; challengers appear one at a time; the
room argues and votes. The app is the instigator and the scorekeeper — the real game is
the argument in the room.

**No backend. No accounts. No networking. Fully offline. Installable as a PWA.**

## How it plays

1. **Setup** — pick a category, add 2–10 players, choose length (10 / 15 / 20 / Endless),
   toggle the debate timer and Chaos mode.
2. **The throne** opens with a legitimate, top-tier champion.
3. **A challenger appears** with a 7-second silence ring. Tap **OBJECTION!** to fight for
   it, or **Pass** — silence is a verdict and the challenger is swept away.
4. **Objection** — whoever objects becomes the Advocate. A Defender can optionally tap in.
5. **Debate** out loud (with an optional 75s clock), then **Skip to vote**.
6. **Vote** — everyone taps 👑 (champion) or ⚡ (challenger). Ties go to the champion.
7. **Result** — dethrone or hold, points awarded, crown transfers.
8. **End** — the surviving champion with its full lineage (every throne-holder and the
   votes that toppled each), plus the leaderboard crowning a **Chief Prosecutor**.

### Scoring

- Successful dethrone: **+2** to the Advocate
- Chaos bonus: **+1** more if the challenger was a Tier-4 (Chaos) pick
- Successful defense: **+1** to the Defender (only if someone claimed the role)
- Failed challenge / voting: **nothing** — challenging is free, so stick your neck out

## The database

555 hand-curated items across nine categories (Movies, Albums, Video Games, TV Shows,
Anime, plus a Denver pack: Bars, Music Venues, Restaurants, Front Range Hikes), each
tiered Canon / Strong / Divisive / Chaos so the game escalates as it goes. Bring your own
with **Custom List** mode (saved to your device). See [`src/data/README.md`](src/data/README.md)
for the schema and how to add items, and [`DECISIONS.md`](DECISIONS.md) for design calls.

```bash
npm run verify:data   # checks schema, duplicates, tiers, counts, balance
```

## Develop

```bash
npm install
npm run dev           # http://localhost:5173/main/
npm run build         # production build to dist/
npm run preview       # serve the production build
```

## Deploy to GitHub Pages

The repo auto-deploys on every push to `main` via
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). The Vite `base` is `/main/`
because this repo is `bradfordpear/main` (Pages serves it at
`https://bradfordpear.github.io/main/`). If you rename the repo, set `DETHRONE_BASE`
accordingly (see `vite.config.js`).

### First-time setup

**With the `gh` CLI:**

```bash
gh repo create bradfordpear/main --public --source=. --remote=origin --push
gh api -X POST repos/bradfordpear/main/pages -f build_type=workflow   # enable Pages via Actions
git push -u origin main
```

Then open **Settings → Pages** and confirm the source is **GitHub Actions**. The site goes
live at `https://bradfordpear.github.io/main/` after the workflow runs.

**Manual fallback (no `gh`):**

1. Create a new repository named `main` under your account on github.com.
2. ```bash
   git remote add origin https://github.com/bradfordpear/main.git
   git push -u origin main
   ```
3. In the repo, go to **Settings → Pages** and set **Source: GitHub Actions**.
4. Push to `main` (or re-run the workflow from the **Actions** tab). Done.

### Install on your phone

Open the Pages URL in mobile Safari/Chrome → **Share → Add to Home Screen**. It runs
fully offline after the first load — perfect for a bar with no signal.
