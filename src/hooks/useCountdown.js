import { useEffect, useRef, useState } from 'react'

// A wall-clock-accurate countdown. Give it a duration (seconds); it returns the
// remaining time and a progress fraction (1 → 0). Fires onExpire once at zero.
// Re-arm by changing `resetKey`. Set `running` false to pause.
export function useCountdown(durationSec, { running = true, resetKey = 0, onExpire, onTick } = {}) {
  const [remaining, setRemaining] = useState(durationSec)
  const endRef = useRef(0)
  const firedRef = useRef(false)
  const onExpireRef = useRef(onExpire)
  const onTickRef = useRef(onTick)
  onExpireRef.current = onExpire
  onTickRef.current = onTick

  // Re-arm whenever the key or duration changes.
  useEffect(() => {
    firedRef.current = false
    endRef.current = Date.now() + durationSec * 1000
    setRemaining(durationSec)
  }, [durationSec, resetKey])

  useEffect(() => {
    if (!running) return
    // Keep the target end moving forward while paused-then-resumed.
    if (endRef.current < Date.now()) endRef.current = Date.now() + remaining * 1000

    let lastWhole = Math.ceil(remaining)
    const id = setInterval(() => {
      const msLeft = Math.max(0, endRef.current - Date.now())
      const secLeft = msLeft / 1000
      setRemaining(secLeft)
      const whole = Math.ceil(secLeft)
      if (whole !== lastWhole) {
        lastWhole = whole
        onTickRef.current?.(whole)
      }
      if (msLeft <= 0 && !firedRef.current) {
        firedRef.current = true
        clearInterval(id)
        onExpireRef.current?.()
      }
    }, 100)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, resetKey, durationSec])

  const fraction = durationSec > 0 ? Math.max(0, Math.min(1, remaining / durationSec)) : 0
  return { remaining, secondsLeft: Math.ceil(remaining), fraction }
}
