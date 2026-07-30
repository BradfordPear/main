import { rankedPlayers } from '../game/machine.js'
import { TIER_META } from '../game/engine.js'

// Final screen: the surviving champion + full lineage (every throne-holder and
// the votes that toppled each), and the leaderboard crowning a Chief Prosecutor.
export default function End({ state, onPlayAgain, onNewGame }) {
  const { config, lineage } = state
  const players = rankedPlayers(config.players)
  const champ = lineage[lineage.length - 1]
  const nameOf = (id) => config.players.find((p) => p.id === id)?.name ?? 'the room'
  const topScore = players[0]?.score ?? 0
  const hasProsecutor = topScore > 0

  return (
    <div className="screen">
      <div className="brand">
        Final Verdict
        <small>{config.categoryLabel}</small>
      </div>

      <div className="stage" style={{ flex: '0 0 auto', margin: '10px 0' }}>
        <div className="card champion">
          <span className="tier-badge" style={{ color: TIER_META[champ.item.tier].accent }}>
            {TIER_META[champ.item.tier].label}
          </span>
          <div className="role">
            <span className="crown">👑</span> Reigning champion
          </div>
          <div className="name">{champ.item.name}</div>
          <div className="meta">
            Survived {lineage.length > 1 ? `${lineage.length - 1} dethronings` : 'unchallenged'} ·
            reigned since round {champ.round === 0 ? '1' : champ.round}
          </div>
        </div>
      </div>

      <div className="section-title">The Lineage 👑</div>
      <div className="lineage">
        {lineage.map((reign, i) => {
          const survivor = i === lineage.length - 1
          return (
            <div className={`reign ${survivor ? 'survivor' : ''}`} key={i}>
              <div className="spine">
                <div className="dot" />
                {i < lineage.length - 1 && <div className="bar" />}
              </div>
              <div className="body">
                <div className="rname">
                  {reign.item.name} {survivor && '👑'}
                </div>
                <div className="rmeta">
                  {reign.round === 0
                    ? 'Opened on the throne'
                    : `Took the throne round ${reign.round} — won by ${nameOf(reign.advocateId)}`}
                </div>
                {reign.toppled && (
                  <div className="toppled">
                    ⚔️ Toppled round {reign.toppled.round} · 👑 {reign.toppled.championVotes} — ⚡{' '}
                    {reign.toppled.challengerVotes}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="section-title">Leaderboard 🏆</div>
      <div className="leaderboard">
        {players.map((p, i) => (
          <div className={`lb-row ${i === 0 && hasProsecutor ? 'top' : ''}`} key={p.id}>
            <span className="rank">{i === 0 && hasProsecutor ? '👑' : i + 1}</span>
            <div className="grow">
              <div className="pname">{p.name}</div>
              {i === 0 && hasProsecutor && <div className="title">Chief Prosecutor</div>}
            </div>
            <span className="pscore">{p.score}</span>
          </div>
        ))}
      </div>
      {!hasProsecutor && (
        <div className="hint">Nobody scored — a game of pure cowardice. No prosecutor crowned.</div>
      )}

      <div style={{ height: 16 }} />
      <button className="btn primary big block" onClick={onPlayAgain}>
        Play again, same crew 🔁
      </button>
      <button className="btn ghost block" style={{ marginTop: 10 }} onClick={onNewGame}>
        New game
      </button>
    </div>
  )
}
