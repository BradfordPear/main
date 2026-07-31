// Dethrone game state machine.
//
// Phases: setup → reveal → objection → debate → vote → result → end
// A single useReducer drives the whole loop. State is kept in memory only
// (no backend); the pool of items for the chosen category lives in state so
// the draw engine can pull from it without any fetching.

import { drawOpeningChampion, drawChallenger, isWildcardRound } from './engine.js'
import { computeAward, applyAward } from './scoring.js'

export const PHASES = ['setup', 'reveal', 'objection', 'debate', 'vote', 'result', 'end']

export const initialState = {
  phase: 'setup',
  config: null, // { categoryId, categoryLabel, players:[{id,name,score}], totalRounds, timerEnabled, timerSeconds, chaosMode, silenceSeconds }
  pool: [],
  usedIds: new Set(),
  round: 0,
  champion: null,
  challenger: null,
  isWildcard: false,
  advocateId: null,
  defenderId: null,
  lineage: [], // reign records — see advance()/dethrone below
  lastResult: null,
}

let pid = 0
export function makePlayer(name) {
  return { id: `p${++pid}`, name: name.trim(), score: 0 }
}

// Move to the next challenger (or end the game if we're out of rounds / deck).
function advanceToNextChallenger(state) {
  const nextRound = state.round + 1
  if (nextRound > state.config.totalRounds) {
    return { ...state, phase: 'end' }
  }
  const challenger = drawChallenger(state.pool, state.usedIds, {
    round: nextRound,
    championId: state.champion?.id,
    chaosMode: state.config.chaosMode,
    chadMode: state.config.chadMode,
  })
  if (!challenger) {
    // Deck exhausted — the champion survives by attrition.
    return { ...state, phase: 'end' }
  }
  const usedIds = new Set(state.usedIds)
  usedIds.add(challenger.id)
  return {
    ...state,
    phase: 'reveal',
    round: nextRound,
    challenger,
    isWildcard: isWildcardRound(nextRound),
    advocateId: null,
    defenderId: null,
    usedIds,
  }
}

export function reducer(state, action) {
  switch (action.type) {
    case 'START_GAME': {
      const { config, pool } = action
      const usedIds = new Set()
      const champion = drawOpeningChampion(pool, usedIds)
      if (!champion) return state
      usedIds.add(champion.id)

      const round = 1
      const challenger = drawChallenger(pool, usedIds, {
        round,
        championId: champion.id,
        chaosMode: config.chaosMode,
        chadMode: config.chadMode,
      })
      if (challenger) usedIds.add(challenger.id)

      return {
        ...initialState,
        phase: challenger ? 'reveal' : 'end',
        config,
        pool,
        usedIds,
        round,
        champion,
        challenger,
        isWildcard: isWildcardRound(round),
        lineage: [{ item: champion, round: 0, advocateId: null, toppled: null }],
      }
    }

    // Challenger dismissed by Pass or by the silence timer expiring.
    case 'DISMISS_CHALLENGER':
      return advanceToNextChallenger(state)

    case 'OBJECT':
      return { ...state, phase: 'objection' }

    case 'SET_ADVOCATE':
      return { ...state, advocateId: action.playerId }

    // Move from objection into the debate. Defender is optional (null = room defends).
    case 'BEGIN_DEBATE':
      return { ...state, phase: 'debate', defenderId: action.defenderId ?? null }

    case 'GO_TO_VOTE':
      return { ...state, phase: 'vote' }

    case 'COMMIT_VOTE': {
      const { championVotes, challengerVotes } = action
      // Ties go to the champion — incumbency advantage, always.
      const dethroned = challengerVotes > championVotes
      const deltas = computeAward({
        dethroned,
        challengerTier: state.challenger.tier,
        advocateId: state.advocateId,
        defenderId: state.defenderId,
      })
      const players = applyAward(state.config.players, deltas)

      const lineage = state.lineage.map((r) => ({ ...r }))
      let champion = state.champion
      if (dethroned) {
        lineage[lineage.length - 1].toppled = {
          round: state.round,
          championVotes,
          challengerVotes,
          byAdvocateId: state.advocateId,
        }
        lineage.push({
          item: state.challenger,
          round: state.round,
          advocateId: state.advocateId,
          toppled: null,
        })
        champion = state.challenger
      }

      const chaosBonus = dethroned && state.challenger.tier === 4

      return {
        ...state,
        phase: 'result',
        champion,
        config: { ...state.config, players },
        lineage,
        lastResult: {
          dethroned,
          championVotes,
          challengerVotes,
          oldChampion: state.champion,
          challenger: state.challenger,
          advocateId: state.advocateId,
          defenderId: state.defenderId,
          deltas,
          chaosBonus,
          wildcard: state.isWildcard,
        },
      }
    }

    case 'NEXT_ROUND':
      return advanceToNextChallenger(state)

    case 'QUIT_TO_END':
      return { ...state, phase: 'end' }

    // Restart with the same crew (names kept, scores reset). Returns to setup
    // pre-filled; App handles re-seeding player names.
    case 'PLAY_AGAIN':
      return { ...initialState, usedIds: new Set() }

    case 'RESET':
      return { ...initialState, usedIds: new Set() }

    default:
      return state
  }
}

// Helper for the leaderboard: players sorted high → low, ties broken by name.
export function rankedPlayers(players) {
  return [...players].sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
}
