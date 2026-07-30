import { useState } from 'react'
import { CATEGORIES, DENVER_IDS } from '../data/index.js'
import {
  buildCustomCategory,
  parseLines,
  loadSavedLists,
  saveList,
  deleteSavedList,
} from '../data/custom.js'

const LENGTHS = [
  { label: '10', value: 10 },
  { label: '15', value: 15 },
  { label: '20', value: 20 },
  { label: 'Endless', value: Infinity },
]

export default function Setup({ onStart, initialPlayers }) {
  const [categoryId, setCategoryId] = useState(null)
  const [customMode, setCustomMode] = useState(false)
  const [customLabel, setCustomLabel] = useState('')
  const [customText, setCustomText] = useState('')
  const [saved, setSaved] = useState(() => loadSavedLists())

  const [players, setPlayers] = useState(
    initialPlayers && initialPlayers.length
      ? initialPlayers.map((n) => n)
      : ['', '']
  )
  const [totalRounds, setTotalRounds] = useState(10)
  const [timerEnabled, setTimerEnabled] = useState(true)
  const [chaosMode, setChaosMode] = useState(true)

  const builtins = CATEGORIES.filter((c) => !DENVER_IDS.has(c.id))
  const denver = CATEGORIES.filter((c) => DENVER_IDS.has(c.id))

  const named = players.map((p) => p.trim()).filter(Boolean)
  const customLines = parseLines(customText)
  const customValid = customMode && customLabel.trim() && customLines.length >= 8
  const catValid = customMode ? customValid : !!categoryId
  const canStart = named.length >= 2 && catValid

  function setPlayer(i, val) {
    setPlayers((ps) => ps.map((p, idx) => (idx === i ? val : p)))
  }
  function addPlayer() {
    if (players.length < 10) setPlayers((ps) => [...ps, ''])
  }
  function removePlayer(i) {
    if (players.length > 2) setPlayers((ps) => ps.filter((_, idx) => idx !== i))
  }

  function pickCategory(id) {
    setCustomMode(false)
    setCategoryId(id)
  }
  function pickCustom() {
    setCategoryId(null)
    setCustomMode(true)
  }

  function loadSaved(entry) {
    setCustomMode(true)
    setCategoryId(null)
    setCustomLabel(entry.label)
    setCustomText(entry.text)
  }
  function doSaveList() {
    if (!customLabel.trim() || customLines.length < 8) return
    setSaved(saveList(customLabel, customText))
  }
  function doDeleteSaved(label) {
    setSaved(deleteSavedList(label))
  }

  function start() {
    if (!canStart) return
    let category
    if (customMode) {
      category = buildCustomCategory(customLabel, customText)
    } else {
      category = CATEGORIES.find((c) => c.id === categoryId)
    }
    const config = {
      categoryId: category.id,
      categoryLabel: category.label,
      players: named.map((name, i) => ({ id: `p${i + 1}_${Date.now()}`, name, score: 0 })),
      totalRounds,
      timerEnabled,
      timerSeconds: 75,
      silenceSeconds: 7,
      chaosMode,
    }
    onStart(config, category.items)
  }

  return (
    <div className="screen">
      <div className="brand">
        Dethrone
        <small>the throne is a lie · defend it anyway</small>
      </div>

      <div className="section-title">Category</div>
      <div className="cat-grid">
        {builtins.map((c) => (
          <button
            key={c.id}
            className={`cat ${!customMode && categoryId === c.id ? 'sel' : ''}`}
            onClick={() => pickCategory(c.id)}
          >
            <span className="emoji">{c.emoji}</span>
            <span className="name">{c.label}</span>
            <span className="cnt">{c.count} items</span>
          </button>
        ))}
      </div>

      {denver.length > 0 && (
        <>
          <div className="section-title">Denver Pack 🏔️</div>
          <div className="cat-grid">
            {denver.map((c) => (
              <button
                key={c.id}
                className={`cat ${!customMode && categoryId === c.id ? 'sel' : ''}`}
                onClick={() => pickCategory(c.id)}
              >
                <span className="emoji">{c.emoji}</span>
                <span className="name">{c.label}</span>
                <span className="cnt">{c.count} items</span>
              </button>
            ))}
          </div>
        </>
      )}

      <div className="section-title">Bring your own</div>
      <button className={`cat ${customMode ? 'sel' : ''}`} style={{ width: '100%' }} onClick={pickCustom}>
        <span className="emoji">✍️</span>
        <span className="name">Custom List</span>
        <span className="cnt">Friends, couples, anything — 8+ entries</span>
      </button>

      {customMode && (
        <div style={{ marginTop: 12 }}>
          <div className="field">
            <label>List name</label>
            <input
              className="input"
              placeholder="Rank My Friends"
              value={customLabel}
              onChange={(e) => setCustomLabel(e.target.value)}
            />
          </div>
          <div className="field">
            <label>One entry per line ({customLines.length} valid · need 8+)</label>
            <textarea
              className="textarea"
              placeholder={'Dave\nPriya\nMarcus\n...'}
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
            />
          </div>
          <div className="row">
            <button className="btn ghost grow" onClick={doSaveList} disabled={!customValid}>
              💾 Save this list
            </button>
          </div>
          {saved.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div className="tiny muted">Saved lists</div>
              {saved.map((s) => (
                <div className="row" key={s.label} style={{ marginTop: 6 }}>
                  <button className="btn ghost grow" onClick={() => loadSaved(s)}>
                    {s.label}
                  </button>
                  <button className="icon-btn" onClick={() => doDeleteSaved(s.label)} aria-label="Delete">
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="section-title">Players ({named.length})</div>
      <div className="players">
        {players.map((p, i) => (
          <div className="player-row" key={i}>
            <span className="idx">{i + 1}</span>
            <input
              className="input grow"
              placeholder={`Player ${i + 1}`}
              value={p}
              maxLength={18}
              onChange={(e) => setPlayer(i, e.target.value)}
            />
            {players.length > 2 && (
              <button className="icon-btn" onClick={() => removePlayer(i)} aria-label="Remove player">
                ✕
              </button>
            )}
          </div>
        ))}
      </div>
      {players.length < 10 && (
        <button className="btn ghost block" style={{ marginTop: 8 }} onClick={addPlayer}>
          + Add player
        </button>
      )}

      <div className="section-title">Game length</div>
      <div className="seg">
        {LENGTHS.map((l) => (
          <button
            key={l.label}
            className={totalRounds === l.value ? 'on' : ''}
            onClick={() => setTotalRounds(l.value)}
          >
            {l.label}
          </button>
        ))}
      </div>

      <div style={{ marginTop: 12 }}>
        <Toggle
          label="Debate timer"
          sub={timerEnabled ? '75 seconds per debate' : 'No clock — argue forever'}
          on={timerEnabled}
          onChange={() => setTimerEnabled((v) => !v)}
        />
        <Toggle
          label="Chaos mode"
          sub={chaosMode ? 'Absurd Tier-4 curveballs appear late game' : 'Serious business only'}
          on={chaosMode}
          onChange={() => setChaosMode((v) => !v)}
        />
      </div>

      <div className="sticky-cta">
        <button className="btn primary big block" disabled={!canStart} onClick={start}>
          {canStart ? 'Take the throne 👑' : hint(named.length, catValid)}
        </button>
      </div>
    </div>
  )
}

function hint(playerCount, catValid) {
  if (playerCount < 2) return 'Add at least 2 players'
  if (!catValid) return 'Pick a category'
  return 'Take the throne 👑'
}

function Toggle({ label, sub, on, onChange }) {
  return (
    <div className="toggle-row" onClick={onChange} role="switch" aria-checked={on}>
      <div>
        <div className="lbl">{label}</div>
        <div className="sub">{sub}</div>
      </div>
      <div className={`switch ${on ? 'on' : ''}`}>
        <div className="knob" />
      </div>
    </div>
  )
}
