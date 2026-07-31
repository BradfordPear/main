// The introductory "How to Play" screen. Shown on first visit and reachable
// anytime from the setup screen.
export default function Rules({ onClose, firstTime }) {
  return (
    <div className="screen">
      <div className="brand">
        Dethrone
        <small>how to play</small>
      </div>

      <div className="rules">
        <p className="rules-lead">
          One phone. One group. A running argument about what's actually the best. The app keeps
          score — <b>you</b> do the yelling.
        </p>

        <Rule n="1" title="A champion holds the throne">
          One item — a movie, an album, a bar — sits on the throne. Challengers step up one at a
          time to try and knock it off.
        </Rule>
        <Rule n="2" title="Object, or let it pass">
          When a challenger appears you get a few seconds. Think it's better than the champion? Hit{' '}
          <b>OBJECTION!</b> Nobody cares? Hit <b>Pass</b> — silence is a verdict and it's swept away.
        </Rule>
        <Rule n="3" title="Whoever objects argues for it">
          The objector becomes the <b>Advocate</b> and makes the case out loud. Someone can tap in to{' '}
          <b>Defend</b> the champion, or the whole room defends by default.
        </Rule>
        <Rule n="4" title="The room votes">
          Everyone taps 👑 (keep the champion) or ⚡ (crown the challenger). <b>Ties keep the
          champion</b> — incumbency wins.
        </Rule>
        <Rule n="5" title="Points reward boldness">
          Win a dethrone as the Advocate: <b>+2</b>. Successfully defend: <b>+1</b>. Losing a
          challenge costs nothing — so swing away. Top scorer is crowned <b>Chief Prosecutor</b>.
        </Rule>

        <div className="rules-modes">
          <div className="rules-mode">
            <b>💪 Chad mode</b> — every challenger is a big, everyone's-seen-it pick, so the room
            always knows both and the debates actually happen.
          </div>
          <div className="rules-mode">
            <b>🌀 Chaos mode</b> — the opposite energy: absurd, so-bad-they're-good curveballs show
            up late to bait one passionate defender.
          </div>
        </div>
      </div>

      <div className="sticky-cta">
        <button className="btn primary big block" onClick={onClose}>
          {firstTime ? "Let's play 👑" : 'Back to setup'}
        </button>
      </div>
    </div>
  )
}

function Rule({ n, title, children }) {
  return (
    <div className="rule">
      <div className="rule-n">{n}</div>
      <div className="rule-body">
        <div className="rule-title">{title}</div>
        <div className="rule-text">{children}</div>
      </div>
    </div>
  )
}
