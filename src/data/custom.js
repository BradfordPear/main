// Custom List mode — powers "Rank My Friends", Couples mode, or a list of
// literally anything. All entries are Tier 2 (Strong) except ~15% randomly
// promoted to Tier 3 so wildcard rounds have something spicy to pull, giving
// the deck some built-in drama. Optionally persisted to localStorage.

const LS_KEY = 'dethrone.customLists.v1'
const PROMOTE_RATE = 0.15

export function parseLines(text) {
  return text
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    // de-dupe case-insensitively, keep first spelling
    .filter((line, i, arr) => arr.findIndex((o) => o.toLowerCase() === line.toLowerCase()) === i)
}

export function buildCustomCategory(label, text, rng = Math.random) {
  const lines = parseLines(text)
  const items = lines.map((name, i) => {
    const promoted = rng() < PROMOTE_RATE
    return {
      id: `c${i}`,
      name,
      tier: promoted ? 3 : 2,
      tags: promoted ? ['wildcard'] : [],
      year: null,
      note: null,
    }
  })
  // Guarantee at least one spicy pick when the list is big enough.
  if (items.length >= 8 && !items.some((i) => i.tier === 3)) {
    items[Math.floor(rng() * items.length)].tier = 3
  }
  return {
    id: `custom:${label.toLowerCase().replace(/\s+/g, '-')}`,
    label: label.trim() || 'Custom List',
    emoji: '✍️',
    description: `Your custom list · ${items.length} entries`,
    items,
    custom: true,
  }
}

// ---- localStorage persistence ----
export function loadSavedLists() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function saveList(label, text) {
  try {
    const lists = loadSavedLists()
    const entry = { label: label.trim() || 'Custom List', text, savedAt: Date.now() }
    const next = [entry, ...lists.filter((l) => l.label !== entry.label)].slice(0, 20)
    localStorage.setItem(LS_KEY, JSON.stringify(next))
    return next
  } catch {
    return loadSavedLists()
  }
}

export function deleteSavedList(label) {
  try {
    const next = loadSavedLists().filter((l) => l.label !== label)
    localStorage.setItem(LS_KEY, JSON.stringify(next))
    return next
  } catch {
    return loadSavedLists()
  }
}
