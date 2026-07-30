// Database verification pass. Run: node scripts/verify-data.mjs
// Checks every category JSON for: valid schema, unique ids, unique names,
// valid tiers, minimum counts, and a tier-distribution smell test.
// Exits non-zero on any hard error so CI blocks a broken database.
import { readdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const dataDir = join(__dirname, '..', 'src', 'data')

// Minimum item counts required per category id.
const MIN_COUNTS = {
  movies: 120,
  albums: 80,
  videogames: 80,
  tvshows: 80,
  anime: 60,
  'denver-bars': 40,
  'denver-venues': 25,
  'denver-restaurants': 40,
  'front-range-hikes': 30,
}

// Target tier distribution (share of deck) with a tolerance band.
const TARGET = { 1: 0.25, 2: 0.35, 3: 0.25, 4: 0.15 }
const TOLERANCE = 0.1

let hardErrors = 0
let warnings = 0
const err = (m) => {
  hardErrors++
  console.error('  ✗ ' + m)
}
const warn = (m) => {
  warnings++
  console.warn('  ⚠ ' + m)
}

const files = readdirSync(dataDir).filter((f) => f.endsWith('.json'))

for (const file of files) {
  const cat = JSON.parse(readFileSync(join(dataDir, file), 'utf8'))
  const isTest = cat.id === '_test'
  console.log(`\n${cat.emoji ?? '•'} ${cat.label} (${file}) — ${cat.items?.length ?? 0} items`)

  if (!cat.id || !cat.label || !Array.isArray(cat.items)) {
    err(`${file}: missing id/label/items`)
    continue
  }

  const ids = new Set()
  const names = new Map()
  const tierCounts = { 1: 0, 2: 0, 3: 0, 4: 0 }

  for (const [i, item] of cat.items.entries()) {
    const where = `${cat.id}[${i}] "${item?.name ?? '?'}"`
    if (typeof item.id !== 'string' || !item.id) err(`${where}: bad id`)
    if (typeof item.name !== 'string' || !item.name.trim()) err(`${where}: bad name`)
    if (![1, 2, 3, 4].includes(item.tier)) err(`${where}: tier must be 1-4, got ${item.tier}`)
    if (!Array.isArray(item.tags)) err(`${where}: tags must be an array`)
    if (!(typeof item.year === 'number' || item.year === null)) err(`${where}: year must be number|null`)
    if (!(typeof item.note === 'string' || item.note === null)) err(`${where}: note must be string|null`)

    if (ids.has(item.id)) err(`${where}: duplicate id "${item.id}"`)
    ids.add(item.id)

    const key = item.name.trim().toLowerCase()
    if (names.has(key)) err(`${where}: duplicate name (also at index ${names.get(key)})`)
    else names.set(key, i)

    if (tierCounts[item.tier] != null) tierCounts[item.tier]++
  }

  // Minimum count
  const min = MIN_COUNTS[cat.id]
  if (min && cat.items.length < min) err(`${cat.id}: needs ≥${min} items, has ${cat.items.length}`)

  // Tier distribution smell test (skip test deck)
  if (!isTest && cat.items.length >= 20) {
    const total = cat.items.length
    for (const t of [1, 2, 3, 4]) {
      const share = tierCounts[t] / total
      const target = TARGET[t]
      if (Math.abs(share - target) > TOLERANCE) {
        warn(
          `${cat.id}: Tier ${t} is ${(share * 100).toFixed(0)}% (target ~${(target * 100).toFixed(0)}%, ±${TOLERANCE * 100}%)`
        )
      }
    }
    if (tierCounts[1] === 0) err(`${cat.id}: no Tier 1 items — opening throne would be illegitimate`)
  }
  console.log(
    `  tiers → T1:${tierCounts[1]} T2:${tierCounts[2]} T3:${tierCounts[3]} T4:${tierCounts[4]}`
  )
}

console.log(`\n${'─'.repeat(40)}`)
if (hardErrors) {
  console.error(`FAILED: ${hardErrors} error(s), ${warnings} warning(s).`)
  process.exit(1)
}
console.log(`PASSED: 0 errors, ${warnings} warning(s).`)
