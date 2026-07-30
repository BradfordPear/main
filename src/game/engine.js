// Dethrone draw engine — the escalation logic that decides which item challenges next.
//
// Tiers:
//   1 Canon     — near-universally beloved, top of the pantheon
//   2 Strong    — excellent and well-known, but not untouchable
//   3 Divisive  — genuinely split opinion, cult / love-it-or-hate-it
//   4 Chaos     — absurd, mid, or so-bad-it's-good bait for one passionate defender
//
// Draw weights shift as the game escalates (see WEIGHTS). Every 6th round is a
// forced WILDCARD that guarantees a Tier 3 or Tier 4 pull. Tier 4 only appears
// when Chaos mode is on. Items never repeat within a game and a challenger is
// never identical to the current champion.

export const TIER_META = {
  1: { label: 'Canon', accent: '#f5c451' },
  2: { label: 'Strong', accent: '#8ad0ff' },
  3: { label: 'Divisive', accent: '#c792ff' },
  4: { label: 'Chaos', accent: '#ff6b9d' },
}

export const WILDCARD_INTERVAL = 6

// Weight tables keyed by tier. Values are relative weights, not percentages.
function weightsForRound(round) {
  if (round <= 3) return { 1: 80, 2: 20, 3: 0, 4: 0 }
  if (round <= 7) return { 1: 40, 2: 40, 3: 20, 4: 0 }
  return { 1: 20, 2: 35, 3: 30, 4: 15 }
}

export function isWildcardRound(round) {
  return round > 0 && round % WILDCARD_INTERVAL === 0
}

// Deterministic-ish RNG hook so tests / future replays can seed. Defaults to Math.random.
function pickWeighted(weights, rng) {
  const total = Object.values(weights).reduce((a, b) => a + b, 0)
  if (total <= 0) return null
  let r = rng() * total
  for (const tier of Object.keys(weights)) {
    r -= weights[tier]
    if (r < 0) return Number(tier)
  }
  return Number(Object.keys(weights).pop())
}

function availableByTier(pool, usedIds, excludeId) {
  const map = { 1: [], 2: [], 3: [], 4: [] }
  for (const item of pool) {
    if (usedIds.has(item.id) || item.id === excludeId) continue
    if (map[item.tier]) map[item.tier].push(item)
  }
  return map
}

// Choose the opening champion: always the top tier so the throne starts legitimate.
export function drawOpeningChampion(pool, usedIds, rng = Math.random) {
  const byTier = availableByTier(pool, usedIds, null)
  const order = [1, 2, 3, 4]
  for (const tier of order) {
    if (byTier[tier].length) {
      const list = byTier[tier]
      return list[Math.floor(rng() * list.length)]
    }
  }
  return null
}

// Draw the next challenger given the current round, champion and mode toggles.
export function drawChallenger(pool, usedIds, { round, championId, chaosMode }, rng = Math.random) {
  const byTier = availableByTier(pool, usedIds, championId)
  const wildcard = isWildcardRound(round)

  // Build the effective weight table for this round.
  let weights
  if (wildcard) {
    // Wildcard guarantees a spicy pull: Tier 3, plus Tier 4 when chaos is on.
    weights = { 1: 0, 2: 0, 3: 60, 4: chaosMode ? 40 : 0 }
  } else {
    weights = { ...weightsForRound(round) }
    if (!chaosMode) weights[4] = 0
  }

  // Zero-out tiers that have no remaining items so weighting stays honest.
  for (const tier of [1, 2, 3, 4]) {
    if (!byTier[tier].length) weights[tier] = 0
  }

  let tier = pickWeighted(weights, rng)

  // Fallbacks: if the chosen tier / whole table is empty, widen the search.
  if (tier == null || !byTier[tier].length) {
    const fallbackOrder = wildcard ? [3, 4, 2, 1] : [2, 1, 3, 4]
    tier = fallbackOrder.find((t) => byTier[t].length) ?? null
  }
  if (tier == null) return null // deck exhausted

  const list = byTier[tier]
  const item = list[Math.floor(rng() * list.length)]
  return item
}

// Convenience: is there anything left to draw at all?
export function hasRemaining(pool, usedIds, excludeId) {
  return pool.some((i) => !usedIds.has(i.id) && i.id !== excludeId)
}
