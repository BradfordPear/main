# Dethrone data

Every category is a plain JSON file in this folder. They're bundled at build time —
there is no server, no fetching, nothing to configure. Edit a file, rebuild, done.

## Item schema

```json
{
  "id": "string, unique within the file",
  "name": "string, the display name",
  "tier": 1,          // 1 | 2 | 3 | 4  (see tiers below)
  "tags": ["sci-fi", "90s"],   // free-form; display-only in v1
  "year": 1999,       // number or null
  "note": "A spicy one-liner shown under the card, or null"
}
```

A category file looks like:

```json
{
  "id": "movies",
  "label": "Movies",
  "emoji": "🎬",
  "description": "One-line description shown on the setup card.",
  "items": [ /* items */ ]
}
```

## The tiers (this is the whole game)

| Tier | Name     | Meaning                                                        |
|------|----------|---------------------------------------------------------------|
| 1    | Canon    | Near-universally beloved. Should be defensible as "objectively great." Opening thrones are drawn from here. |
| 2    | Strong   | Excellent and well-known, but not untouchable.                |
| 3    | Divisive | Genuinely splits the room. Cult favorites, love-it-or-hate-it. |
| 4    | Chaos    | Absurd, mid, or so-bad-it's-good. Bait for one passionate defender. Only appears late game with Chaos mode on. |

**Target mix per category:** ~25% T1, ~35% T2, ~25% T3, ~15% T4. The verifier warns if a
deck drifts more than 10 points off these.

## How the draw uses tiers

- Early rounds pull mostly Tier 1, escalating to Tier 2/3 and finally Tier 4 as the game goes on.
- Every 6th round is a **wildcard** that forces a Tier 3 (or Tier 4 with Chaos mode) pull.
- Items never repeat within a game.

So: put your genuinely great, no-argument picks at Tier 1; your bangers at Tier 2; your
"fight me" picks at Tier 3; and your chaos gremlins at Tier 4.

## Adding items or a whole category

1. Add items to an existing file, or create a new `my-category.json` with the shape above.
2. If it's a new file, register it in `index.js` (import it and add it to `RAW`).
3. Run `npm run verify:data` — it checks for duplicate ids/names, bad tiers, missing fields,
   minimum counts, and tier balance.
4. Rebuild.

## Verifier

`npm run verify:data` also runs in CI (see `.github/workflows/deploy.yml`) so a broken or
duplicated database can't ship.
