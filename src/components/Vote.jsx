import { useState } from 'react'

// Full-screen vote. Each player taps their name onto the champion's side (👑)
// or the challenger's side (⚡). Live tally. Ties go to the champion.
export default function Vote({ state, dispatch }) {
  const { config, champion, challenger } = state
  const players = config.players
  const [votes, setVotes] = useState({}) // playerId -> 'champ' | 'chall'

  const champVotes = Object.values(votes).filter((v) => v === 'champ').length
  const challVotes = Object.values(votes).filter((v) => v === 'chall').length
  const allIn = players.every((p) => votes[p.id])

  function cast(id, side) {
    setVotes((v) => ({ ...v, [id]: v[id] === side ? undefined : side }))
  }

  function reveal() {
    if (!allIn) return
    dispatch({ type: 'COMMIT_VOTE', championVotes: champVotes, challengerVotes: challVotes })
  }

  return (
    <div className="screen">
      <div className="topbar">
        <span className="pill sel">🗳️ Vote</span>
        <span className="pill">
          {Object.keys(votes).filter((k) => votes[k]).length}/{players.length} in
        </span>
      </div>

      <div className="vote-cols">
        <div className="vote-col champ">
          <h3>👑 {truncate(champion.name)}</h3>
          <div className="tally">{champVotes}</div>
        </div>
        <div className="vote-col chall">
          <h3>⚡ {truncate(challenger.name)}</h3>
          <div className="tally">{challVotes}</div>
        </div>
      </div>

      <div className="section-title">Tap your verdict</div>
      <div className="players">
        {players.map((p) => (
          <div className="player-row" key={p.id}>
            <span className="grow" style={{ fontWeight: 700 }}>
              {p.name}
            </span>
            <button
              className={`pill ${votes[p.id] === 'champ' ? 'on' : ''}`}
              onClick={() => cast(p.id, 'champ')}
              aria-label={`${p.name} votes champion`}
            >
              👑
            </button>
            <button
              className={`pill ${votes[p.id] === 'chall' ? 'sel' : ''}`}
              onClick={() => cast(p.id, 'chall')}
              aria-label={`${p.name} votes challenger`}
            >
              ⚡
            </button>
          </div>
        ))}
      </div>

      <div className="sticky-cta">
        <button className="btn primary big block" onClick={reveal} disabled={!allIn}>
          {allIn ? 'Reveal the verdict ⚖️' : `Everyone must vote (${players.length - Object.keys(votes).filter((k) => votes[k]).length} left)`}
        </button>
        <div className="hint">Ties go to the champion. Incumbency advantage, always.</div>
      </div>
    </div>
  )
}

function truncate(s, n = 18) {
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}
