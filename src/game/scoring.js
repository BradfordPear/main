// Dethrone scoring — points reward sticking your neck out, not voting.
//
//   Successful dethrone:  +2 to the Advocate
//   Failed challenge:      0 (no punishment — challenging is free)
//   Successful defense:   +1 to the Defender, only if someone claimed the role
//   Chaos bonus:          +1 extra on a successful dethrone of a Tier-4 item
//   Voting:                nothing

export function computeAward({ dethroned, challengerTier, advocateId, defenderId }) {
  const deltas = {} // playerId -> points to add
  const add = (id, n) => {
    if (id == null) return
    deltas[id] = (deltas[id] || 0) + n
  }

  if (dethroned) {
    add(advocateId, 2)
    if (challengerTier === 4) add(advocateId, 1) // chaos bonus
  } else {
    add(defenderId, 1) // successful defense, only if a defender claimed in
  }

  return deltas
}

export function applyAward(players, deltas) {
  return players.map((p) => (deltas[p.id] ? { ...p, score: p.score + deltas[p.id] } : p))
}
