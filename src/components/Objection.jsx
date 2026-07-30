import { useState } from 'react'
import ItemCard from './ItemCard.jsx'

// "Who's objecting?" → that player becomes the Advocate for the challenger.
// Optionally a second player taps in as Defender of the champion (skippable —
// the room defends by default).
export default function Objection({ state, dispatch }) {
  const { config, challenger, champion, advocateId } = state
  const players = config.players
  const [step, setStep] = useState('advocate') // 'advocate' | 'defender'
  const [chosenAdvocate, setChosenAdvocate] = useState(advocateId)

  function pickAdvocate(id) {
    setChosenAdvocate(id)
    dispatch({ type: 'SET_ADVOCATE', playerId: id })
    setStep('defender')
  }

  function pickDefender(id) {
    dispatch({ type: 'BEGIN_DEBATE', defenderId: id })
  }

  return (
    <div className="screen">
      <div className="topbar">
        <span className="pill sel">⚖️ Objection raised</span>
      </div>

      <div className="stage" style={{ flex: '0 0 auto', marginBottom: 8 }}>
        <ItemCard item={challenger} variant="challenger" wildcard={state.isWildcard} />
      </div>

      {step === 'advocate' ? (
        <>
          <div className="section-title">Who's objecting?</div>
          <div className="hint" style={{ marginTop: 0 }}>
            You become the Advocate — you argue this challenger onto the throne.
          </div>
          <div className="voter-bank">
            {players.map((p) => (
              <button key={p.id} className="voter" onClick={() => pickAdvocate(p.id)}>
                {p.name}
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <div className="section-title">Anyone defending the champion?</div>
          <div className="hint" style={{ marginTop: 0 }}>
            Optional. A Defender earns +1 on a successful defense. Skip and the whole room defends.
          </div>
          <div className="voter-bank">
            {players
              .filter((p) => p.id !== chosenAdvocate)
              .map((p) => (
                <button key={p.id} className="voter" onClick={() => pickDefender(p.id)}>
                  {p.name}
                </button>
              ))}
          </div>
          <div className="spacer" />
          <button className="btn primary big block" onClick={() => pickDefender(null)}>
            The room defends — to the debate ⚔️
          </button>
        </>
      )}
    </div>
  )
}
