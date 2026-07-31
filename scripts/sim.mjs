// Headless full-game simulation to exercise the reducer + engine + scoring
// without a browser. Verifies core invariants over many random playthroughs.
import { readFileSync } from 'node:fs'
import { reducer, initialState } from '../src/game/machine.js'

// Build a synthetic pool big enough to run 20 rounds with all tiers present.
function makePool(n) {
  const items = []
  const tierFor = (i) => (i % 7 === 0 ? 4 : i % 3 === 0 ? 3 : i % 2 === 0 ? 2 : 1)
  for (let i = 0; i < n; i++) {
    items.push({ id: `x${i}`, name: `Item ${i}`, tier: tierFor(i), tags: [], year: null, note: null })
  }
  return items
}

function play(seedPlayers, totalRounds, chaosMode, timerEnabled, chadMode = false) {
  const pool = makePool(60)
  const config = {
    categoryId: 'sim',
    categoryLabel: 'Sim',
    players: seedPlayers.map((name, i) => ({ id: `p${i}`, name, score: 0 })),
    totalRounds,
    timerEnabled,
    timerSeconds: 75,
    silenceSeconds: 10,
    chaosMode,
    chadMode,
  }
  let s = reducer(initialState, { type: 'START_GAME', config, pool })

  const seen = new Set()
  seen.add(s.champion.id)
  let guard = 0

  while (s.phase !== 'end' && guard++ < 1000) {
    // Invariant: challenger never equals champion, never repeats.
    if (s.phase === 'reveal') {
      if (s.challenger.id === s.champion.id) throw new Error('challenger == champion')
      if (seen.has(s.challenger.id)) throw new Error('repeat challenger ' + s.challenger.id)
      seen.add(s.challenger.id)

      // Randomly object (60%) or pass.
      if (Math.random() < 0.6) {
        s = reducer(s, { type: 'OBJECT' })
        const adv = config.players[Math.floor(Math.random() * config.players.length)]
        s = reducer(s, { type: 'SET_ADVOCATE', playerId: adv.id })
        const def = Math.random() < 0.4 ? config.players.find((p) => p.id !== adv.id) : null
        s = reducer(s, { type: 'BEGIN_DEBATE', defenderId: def?.id ?? null })
        s = reducer(s, { type: 'GO_TO_VOTE' })
        const nP = config.players.length
        const champV = Math.floor(Math.random() * (nP + 1))
        const challV = nP - champV
        s = reducer(s, { type: 'COMMIT_VOTE', championVotes: champV, challengerVotes: challV })
        // Result -> next
        s = reducer(s, { type: 'NEXT_ROUND' })
      } else {
        s = reducer(s, { type: 'DISMISS_CHALLENGER' })
      }
    } else {
      throw new Error('unexpected phase ' + s.phase)
    }
  }

  // Invariants on end state.
  if (s.lineage.length < 1) throw new Error('empty lineage')
  const survivor = s.lineage[s.lineage.length - 1]
  if (survivor.item.id !== s.champion.id) throw new Error('survivor mismatch')
  // ties go to champion: every toppled entry must have challenger > champion votes
  for (const r of s.lineage) {
    if (r.toppled && !(r.toppled.challengerVotes > r.toppled.championVotes)) {
      throw new Error('toppled without majority (tie should hold)')
    }
  }
  // total scores non-negative
  for (const p of s.config.players) if (p.score < 0) throw new Error('negative score')

  return {
    rounds: s.round,
    lineageLen: s.lineage.length,
    scores: s.config.players.map((p) => `${p.name}:${p.score}`).join(' '),
  }
}

let runs = 0
for (let i = 0; i < 300; i++) {
  const n = 2 + Math.floor(Math.random() * 9)
  const players = Array.from({ length: n }, (_, k) => `P${k + 1}`)
  const lengths = [10, 15, 20]
  const total = lengths[Math.floor(Math.random() * lengths.length)]
  const chad = Math.random() < 0.4
  play(players, total, Math.random() < 0.5, Math.random() < 0.5, chad)
  runs++
}
console.log(`OK — ${runs} random games completed, all invariants held.`)

// Chad mode should never surface Tier 3/4 challengers when higher tiers remain.
{
  const pool = makePool(60)
  let s = reducer(initialState, {
    type: 'START_GAME',
    config: {
      categoryId: 'sim', categoryLabel: 'Sim',
      players: [{ id: 'p0', name: 'A', score: 0 }, { id: 'p1', name: 'B', score: 0 }],
      totalRounds: 20, timerEnabled: false, timerSeconds: 75, silenceSeconds: 10,
      chaosMode: true, chadMode: true,
    },
    pool,
  })
  const tiers = new Set()
  let guard = 0
  while (s.phase !== 'end' && guard++ < 100) {
    if (s.challenger) tiers.add(s.challenger.tier)
    s = reducer(s, { type: 'DISMISS_CHALLENGER' })
  }
  const obscure = [...tiers].filter((t) => t >= 3)
  if (obscure.length) throw new Error('Chad mode surfaced obscure tiers: ' + obscure)
  console.log('Chad mode: only tiers', [...tiers].sort().join(','), '(no 3/4) ✓')
}
const sample = play(['Alice', 'Bob', 'Cara'], 15, true, true)
console.log('sample:', JSON.stringify(sample))
