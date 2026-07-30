import { useMemo } from 'react'

// A quick screen flash used on Chaos dethrones.
export function Flash() {
  return <div className="flash" />
}

// Lightweight CSS confetti — no library. Renders once and cleans itself up via
// the caller unmounting it after the animation.
export function Confetti({ count = 80 }) {
  const bits = useMemo(() => {
    const colors = ['#f5c451', '#7cf5ff', '#c792ff', '#ff6b9d', '#58e08a']
    return Array.from({ length: count }, () => ({
      left: Math.random() * 100,
      delay: Math.random() * 0.5,
      dur: 1.6 + Math.random() * 1.4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rot: Math.random() * 360,
    }))
  }, [count])
  return (
    <div className="confetti" aria-hidden="true">
      {bits.map((b, i) => (
        <i
          key={i}
          style={{
            left: `${b.left}%`,
            background: b.color,
            transform: `rotate(${b.rot}deg)`,
            animationDelay: `${b.delay}s`,
            animationDuration: `${b.dur}s`,
          }}
        />
      ))}
    </div>
  )
}
