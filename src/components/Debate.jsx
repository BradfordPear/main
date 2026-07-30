import ItemCard from './ItemCard.jsx'
import { useCountdown } from '../hooks/useCountdown.js'

// Both items side by side, the Advocate's name, and (optionally) the debate
// countdown. "Skip to vote" ends it early when the argument resolves.
export default function Debate({ state, dispatch, sound }) {
  const { champion, challenger, config, advocateId, defenderId, isWildcard } = state
  const advocate = config.players.find((p) => p.id === advocateId)
  const defender = config.players.find((p) => p.id === defenderId)

  const { secondsLeft, fraction } = useCountdown(config.timerSeconds, {
    running: config.timerEnabled,
    resetKey: challenger?.id ?? 0,
    onExpire: () => config.timerEnabled && toVote(),
    onTick: (s) => {
      if (config.timerEnabled && s <= 5 && s > 0) sound.tick(s)
    },
  })

  function toVote() {
    dispatch({ type: 'GO_TO_VOTE' })
  }

  const urgent = config.timerEnabled && secondsLeft <= 10
  return (
    <div className="screen">
      <div className="topbar">
        <span className="pill sel">⚔️ Debate</span>
        {isWildcard && <span className="pill">⚡ Wildcard</span>}
      </div>

      <div className="advocate-tag">
        <b>{advocate ? advocate.name : 'Someone'}</b> is prosecuting the throne
        {defender && (
          <>
            {' · '}
            <b style={{ color: 'var(--gold)' }}>{defender.name}</b> defends
          </>
        )}
      </div>

      {config.timerEnabled ? (
        <>
          <div className={`debate-timer ${urgent ? 'urgent' : ''}`}>
            {String(Math.floor(secondsLeft / 60)).padStart(1, '0')}:
            {String(secondsLeft % 60).padStart(2, '0')}
          </div>
          <div className="progress">
            <i style={{ width: `${fraction * 100}%` }} />
          </div>
        </>
      ) : (
        <div className="debate-timer" style={{ fontSize: '1.4rem', color: 'var(--muted)' }}>
          No clock — argue it out
        </div>
      )}

      <div className="stage">
        <ItemCard item={champion} variant="champion" />
        <div className="vs">— VERSUS —</div>
        <ItemCard item={challenger} variant="challenger" wildcard={isWildcard} />
      </div>

      <button className="btn electric big block" onClick={toVote}>
        Skip to vote 🗳️
      </button>
      <div className="hint">Make your case out loud. The room decides.</div>
    </div>
  )
}
