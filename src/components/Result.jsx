import { useEffect, useState } from 'react'
import ItemCard from './ItemCard.jsx'
import { Confetti, Flash } from './Effects.jsx'

export default function Result({ state, dispatch, sound }) {
  const r = state.lastResult
  const { config } = state
  const [showFx, setShowFx] = useState(true)

  const advocate = config.players.find((p) => p.id === r.advocateId)
  const nameOf = (id) => config.players.find((p) => p.id === id)?.name ?? '—'

  useEffect(() => {
    if (r.dethroned) {
      r.chaosBonus ? sound.chaos() : sound.sting()
    } else {
      sound.sweep()
    }
    const t = setTimeout(() => setShowFx(false), 2600)
    return () => clearTimeout(t)
  }, [])

  const awardLines = Object.entries(r.deltas)
    .filter(([, pts]) => pts > 0)
    .map(([id, pts]) => ({ name: nameOf(id), pts }))

  const isLast = config.totalRounds !== Infinity && state.round >= config.totalRounds
  const nextChamp = r.dethroned ? r.challenger : r.oldChampion

  return (
    <div className="screen">
      {showFx && r.dethroned && <Confetti count={r.chaosBonus ? 120 : 70} />}
      {showFx && r.chaosBonus && <Flash />}

      <div className="result-hero">
        {r.dethroned ? (
          <>
            <div className="crown-fly">👑</div>
            <div className="result-verdict dethroned">DETHRONED!</div>
          </>
        ) : (
          <>
            <div className="crown-fly">🛡️</div>
            <div className="result-verdict survived">THRONE HELD</div>
          </>
        )}
        <div className="result-votes">
          👑 {r.championVotes} &nbsp;·&nbsp; ⚡ {r.challengerVotes}
        </div>
        {r.chaosBonus && (
          <div className="wildcard-banner" style={{ marginTop: 12, color: 'var(--chaos)', borderColor: 'var(--chaos)' }}>
            🤯 Chaos Dethrone
          </div>
        )}
      </div>

      <div className="stage" style={{ flex: '0 0 auto' }}>
        <ItemCard item={nextChamp} variant="champion" />
      </div>

      <div className="award">
        {awardLines.length > 0 ? (
          awardLines.map((a, i) => (
            <div className="line" key={i}>
              <span>{a.name}</span>
              <span className="pts">+{a.pts}</span>
            </div>
          ))
        ) : (
          <div className="hint">
            {r.dethroned ? '' : `The room holds the line. ${advocate?.name ?? 'The challenger'} gets nothing but respect.`}
          </div>
        )}
      </div>

      <div className="spacer" />
      <button className="btn primary big block" onClick={() => dispatch({ type: 'NEXT_ROUND' })}>
        {isLast ? 'See the final results 🏁' : 'Next challenger →'}
      </button>
    </div>
  )
}
