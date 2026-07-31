import { useReducer, useState, useEffect, useRef } from 'react'
import { reducer, initialState } from './game/machine.js'
import { useSound } from './hooks/useSound.js'
import Setup from './components/Setup.jsx'
import Rules from './components/Rules.jsx'
import Reveal from './components/Reveal.jsx'
import Objection from './components/Objection.jsx'
import Debate from './components/Debate.jsx'
import Vote from './components/Vote.jsx'
import Result from './components/Result.jsx'
import End from './components/End.jsx'

const MUTE_KEY = 'dethrone.muted'
const RULES_KEY = 'dethrone.seenRules'

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const [muted, setMuted] = useState(() => localStorage.getItem(MUTE_KEY) === '1')
  const [keepCrew, setKeepCrew] = useState(null)
  // Show the how-to-play screen on first ever visit; reachable from setup after.
  const [showRules, setShowRules] = useState(() => localStorage.getItem(RULES_KEY) !== '1')
  const firstTimeRules = useRef(localStorage.getItem(RULES_KEY) !== '1')
  const sound = useSound(muted)

  function closeRules() {
    localStorage.setItem(RULES_KEY, '1')
    firstTimeRules.current = false
    setShowRules(false)
  }

  useEffect(() => {
    localStorage.setItem(MUTE_KEY, muted ? '1' : '0')
  }, [muted])

  function startGame(config, pool) {
    dispatch({ type: 'START_GAME', config, pool })
  }

  function playAgain() {
    setKeepCrew(state.config.players.map((p) => p.name))
    dispatch({ type: 'PLAY_AGAIN' })
  }

  function newGame() {
    setKeepCrew(null)
    dispatch({ type: 'RESET' })
  }

  function quit() {
    if (confirm('Quit this game and see the results so far?')) dispatch({ type: 'QUIT_TO_END' })
  }

  const inGame = state.phase !== 'setup' && state.phase !== 'end'

  return (
    <div className="app">
      <div className="floating-controls">
        <button className="icon-btn" onClick={() => setMuted((m) => !m)} aria-label="Toggle sound">
          {muted ? '🔇' : '🔊'}
        </button>
        {inGame && (
          <button className="icon-btn" onClick={quit} aria-label="Quit game" title="Quit game">
            ⏹️
          </button>
        )}
      </div>

      {showRules && state.phase === 'setup' ? (
        <Rules onClose={closeRules} firstTime={firstTimeRules.current} />
      ) : (
        state.phase === 'setup' && (
          <Setup onStart={startGame} initialPlayers={keepCrew} onHowToPlay={() => setShowRules(true)} />
        )
      )}
      {state.phase === 'reveal' && <Reveal state={state} dispatch={dispatch} sound={sound} />}
      {state.phase === 'objection' && <Objection state={state} dispatch={dispatch} />}
      {state.phase === 'debate' && <Debate state={state} dispatch={dispatch} sound={sound} />}
      {state.phase === 'vote' && <Vote state={state} dispatch={dispatch} />}
      {state.phase === 'result' && <Result state={state} dispatch={dispatch} sound={sound} />}
      {state.phase === 'end' && <End state={state} onPlayAgain={playAgain} onNewGame={newGame} />}
    </div>
  )
}
