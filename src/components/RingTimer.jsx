// The 7-second silence ring. Pure SVG stroke-dashoffset animation driven by
// the `fraction` (1 → 0) from useCountdown.
export default function RingTimer({ fraction, secondsLeft, size = 92, stroke = 8 }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const urgent = secondsLeft <= 3
  const color = urgent ? '#ff5470' : '#7cf5ff'
  return (
    <div className={`ring ${urgent ? 'urgent' : ''}`} style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#23232f" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - fraction)}
          style={{ transition: 'stroke-dashoffset 0.1s linear, stroke 0.3s' }}
        />
      </svg>
      <div className="count">{secondsLeft}</div>
    </div>
  )
}
