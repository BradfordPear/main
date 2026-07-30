// Category registry. Each built-in category is a static JSON file bundled at
// build time — no fetching, fully offline. To add a category: drop a JSON file
// in this folder (same schema) and register it here. See README.md.

import testDeck from './_test.json'
// Real category files are added below once the database is built.

const RAW = [
  testDeck, // kept last; hidden from the picker unless SHOW_TEST is on
]

// Flip to true to expose the tiny smoke-test deck in the category picker.
// TEMP: true during loop bring-up before the full database exists.
const SHOW_TEST = true

export const CATEGORIES = RAW.filter((c) => SHOW_TEST || c.id !== '_test').map((c) => ({
  id: c.id,
  label: c.label,
  emoji: c.emoji ?? '🎴',
  description: c.description ?? '',
  items: c.items,
  count: c.items.length,
}))

export function getCategory(id) {
  return CATEGORIES.find((c) => c.id === id) ?? RAW.find((c) => c.id === id)
}

// Denver-pack grouping so the setup screen can cluster the local categories.
export const DENVER_IDS = new Set([
  'denver-bars',
  'denver-venues',
  'denver-restaurants',
  'front-range-hikes',
])
