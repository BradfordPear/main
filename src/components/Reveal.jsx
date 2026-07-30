import { useEffect, useState } from 'react'
import ItemCard from './ItemCard.jsx'
import RingTimer from './RingTimer.jsx'
import { useCountdown } from '../hooks/useCountdown.js'

// Champion holds the top; challenger slides in below with a silence ring.
// If the ring hits zero or someone taps Pass, the challenger is swept away and
// the next one appears. Silence is a verdict.
export default function Reveal({ state, dispatch, sound }) {
  const { champion, challenger, round, config, isWildcard } = state
  const [dismissing, setDismissing] = useState(false)

  // Reset the swept-away flag whenever a new challenger arrives.
  useEffect(() => {
    setDismissing(false)
  }, [challenger?.id])

  const { fraction, secondsLeft } = useCountdown(config.silenceSeconds, {
    running: !dismissing,
    resetKey: challenger?.id ?? 0,
    onExpire: () => dismiss(),
    onTick: (s) => {
      if (!dismissing && s > 0) sound.tick(s)
    },
  })

  function dismiss() {
    if (dismissing) return
    setDismissing(true)
    sound.sweep()
    setTimeout(() => dispatch({ type: 'DISMISS_CHALLENGER' }), 380)
  }

  function object() {
    if (dismissing) return
    dispatch({ type: 'OBJECT' })
  }

  const endlessTag = config.totalRounds === Infinity ? '∞' : config.totalRounds
  return (
    <div className="screen">
      <div className="topbar">
        <span className="pill">
          Round {round}
          {' / '}
          {endlessTag}
        </span>
        <span className="pill on">👑 Champion holds</span>
      </div>

      {isWildcard && <div className="wildcard-banner">⚡ Wildcard Round ⚡</div>}

      <div className="stage">
        <ItemCard item={champion} variant="champion" />
        <div className="vs">▼ challenged by ▼</div>
        <div
          key={challenger?.id}
          className={dismissing ? 'sweep-away' : 'slide-in'}
        >
          <ItemCard item={challenger} variant="challenger" wildcard={isWildcard} />
        </div>
      </div>

      <div className="ring-wrap">
        <RingTimer fraction={fraction} secondsLeft={secondsLeft} />
      </div>

      <div className="reveal-actions">
        <button className="btn danger big" onClick={object} disabled={dismissing}>
          OBJECTION!
        </button>
        <button className="btn ghost big" onClick={dismiss} disabled={dismissing}>
          Pass
        </button>
      </div>
      <div className="hint">Nobody speaks up? The challenger is dismissed. Keep it moving.</div>
    </div>
  )
}
