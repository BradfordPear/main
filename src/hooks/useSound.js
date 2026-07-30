import { useCallback, useEffect, useRef } from 'react'

// Tiny Web Audio synth — no audio files. Provides a silence-timer tick and a
// dramatic dethrone sting. Fully guarded: if the AudioContext can't start
// (autoplay policy, unsupported browser) it degrades to silence, never crashes.
export function useSound(muted) {
  const ctxRef = useRef(null)

  const ctx = useCallback(() => {
    if (muted) return null
    try {
      if (!ctxRef.current) {
        const AC = window.AudioContext || window.webkitAudioContext
        if (!AC) return null
        ctxRef.current = new AC()
      }
      if (ctxRef.current.state === 'suspended') ctxRef.current.resume()
      return ctxRef.current
    } catch {
      return null
    }
  }, [muted])

  const blip = useCallback(
    (freq, dur, type = 'sine', gain = 0.06) => {
      const ac = ctx()
      if (!ac) return
      try {
        const osc = ac.createOscillator()
        const g = ac.createGain()
        osc.type = type
        osc.frequency.value = freq
        g.gain.setValueAtTime(0, ac.currentTime)
        g.gain.linearRampToValueAtTime(gain, ac.currentTime + 0.01)
        g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + dur)
        osc.connect(g).connect(ac.destination)
        osc.start()
        osc.stop(ac.currentTime + dur + 0.02)
      } catch {
        /* ignore */
      }
    },
    [ctx]
  )

  const tick = useCallback(
    (secondsLeft) => {
      // Rising urgency: pitch climbs as the silence timer runs out.
      const freq = 520 + (7 - Math.min(7, secondsLeft)) * 40
      blip(freq, 0.06, 'square', 0.035)
    },
    [blip]
  )

  const sweep = useCallback(() => blip(220, 0.18, 'triangle', 0.04), [blip])

  const sting = useCallback(() => {
    const ac = ctx()
    if (!ac) return
    // A little fanfare: three quick ascending notes.
    ;[392, 523, 784].forEach((f, i) => setTimeout(() => blip(f, 0.28, 'sawtooth', 0.05), i * 90))
  }, [ctx, blip])

  const chaos = useCallback(() => {
    const ac = ctx()
    if (!ac) return
    ;[660, 880, 660, 1046].forEach((f, i) =>
      setTimeout(() => blip(f, 0.16, 'square', 0.05), i * 70)
    )
  }, [ctx, blip])

  // Best-effort cleanup.
  useEffect(() => () => {
    try {
      ctxRef.current?.close()
    } catch {
      /* ignore */
    }
  }, [])

  return { tick, sweep, sting, chaos }
}
