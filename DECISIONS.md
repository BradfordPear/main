# DECISIONS

Reasonable calls made while building Dethrone, so nothing is a surprise.

## Tech / toolchain

- **Vite + React 18**, plain global CSS (one `src/styles/index.css`). No Tailwind, no
  CSS-in-JS — keeps the toolchain to one build step as requested.
- **PWA via `vite-plugin-pwa`** (Workbox `generateSW`, `registerType: autoUpdate`).
  Manifest + service worker are generated at build time; the app precaches all assets
  so it runs fully offline after first load. Icons are generated (see below).
- **`base` path**: set to `/main/` in `vite.config.js` because this repo is
  `bradfordpear/main`, so Pages serves it at `https://bradfordpear.github.io/main/`.
  Override with the `DETHRONE_BASE` env var if you rename the repo or add a custom domain.
- **Icons are generated, not hand-drawn binaries.** `scripts/gen-icons.mjs` rasterizes the
  gold-crown-on-charcoal icon to `public/icons/icon-{192,512}.png` using only Node's `zlib`
  (no image libraries). Re-run with `node scripts/gen-icons.mjs` if you change the design.

## Game rules (implemented exactly as specified, with these clarifications)

- **A "round" = one challenger.** Passing/timing out a challenger still consumes that round
  and advances the draw weights, so "silence is a verdict" keeps the pace fast.
- **Opening champion** is drawn from the top available tier (Tier 1) so the throne starts
  legitimate; if a deck somehow has no Tier 1 it falls back to the next tier down.
- **Ties go to the champion** everywhere (incumbency advantage). A challenger needs a strict
  majority to dethrone.
- **Draw fallbacks**: if the weighted tier for a round has no unused items left, the engine
  widens to neighboring tiers rather than repeating an item. Items never repeat within a game
  and a challenger is never the current champion.
- **Wildcard rounds** (every 6th) force a Tier 3 pull, adding Tier 4 only when Chaos mode is on.
  They get a distinct purple card, screen-shake, and a banner.
- **Scoring**: successful dethrone +2 advocate; +1 chaos bonus if the challenger was Tier 4;
  successful defense +1 only if a Defender explicitly claimed in; failed challenge and voting
  score nothing.

## UX calls

- **Voting** is tap-to-toggle (not drag): each player taps 👑 (champion) or ⚡ (challenger).
  Chosen fastest-to-build-reliably per the brief. Live tally; "Reveal" unlocks once everyone
  has voted.
- **Defender step is skippable** with a prominent "The room defends" button, as specified.
- **Sound** is synthesized via Web Audio (no files): a rising tick on the silence ring, a
  sting on dethrone, a chaotic arpeggio on a Chaos dethrone. Fully guarded — if the
  AudioContext can't start it degrades to silence. Global 🔊/🔇 toggle, persisted.
- **Quit** (⏹️) during a game jumps to the results-so-far screen.
- **Custom List mode**: entries are Tier 2, ~15% randomly promoted to Tier 3 for wildcard
  drama (with a guarantee of at least one spicy pick on lists of 8+). Lists can be saved to
  `localStorage` and reloaded.
- **Reduced motion** is respected (`prefers-reduced-motion`).

## Data

- Every category is a static JSON file in `src/data/` (schema in `src/data/README.md`).
- `scripts/verify-data.mjs` runs in CI and locally (`npm run verify:data`): it checks schema,
  duplicate ids/names, tier validity, minimum counts, and a tier-distribution smell test.

## Out of scope for v1 (structured to add later)

- AI "Verdict mode" — the result screen is a self-contained component; a judge ruling would
  slot in between vote and result.
- Tag-based adaptive draws — every item already carries `tags`; the draw engine takes a single
  options object so a tag bias is an additive change.
- Multi-device play — all state is in one `useReducer`; nothing assumes a single device beyond
  the UI.
