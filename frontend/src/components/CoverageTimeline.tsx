import React, { useEffect, useState } from 'react'
import { hhmmToMin, format12 } from '../lib/time'

type CoverageSegment = { start: string; end: string; count: number }
type CoverageDay = {
  weekday: number
  weekday_name: string
  open: string | null
  close: string | null
  segments: CoverageSegment[]
}

function computeDefaultProbe(data: CoverageDay[]): number {
  const first = data.find((d) => d.open && d.close)
  if (!first) return 12 * 60
  return Math.floor((hhmmToMin(first.open!) + hhmmToMin(first.close!)) / 2)
}

type Props = {
  data: CoverageDay[]
  minStaffDefault: number
  maxEmployees?: number
  showProbe?: boolean
}

export function CoverageTimeline({
  data,
  minStaffDefault,
  showProbe = true,
}: Props) {
  const [probeMin, setProbeMin] = useState<number>(() => computeDefaultProbe(data))
  useEffect(() => {
    setProbeMin(computeDefaultProbe(data))
  }, [data])

  const countAt = (day: CoverageDay, minute: number) => {
    if (!day.open || !day.close) return 0
    const o = hhmmToMin(day.open)
    const c = hhmmToMin(day.close)
    if (minute < o || minute >= c) return 0
    for (const seg of day.segments) {
      const s = hhmmToMin(seg.start)
      const e = hhmmToMin(seg.end)
      if (minute >= s && minute < e) return seg.count
    }
    return 0
  }

  const colorFor = (count: number) => {
    if (count <= 0) return '#fee2e2' // red-100: under 1
    if (count < minStaffDefault) return '#fde68a' // amber-200: below target
    if (count === minStaffDefault) return '#bbf7d0' // green-200: meets target
    return '#bfdbfe' // blue-200: exceeds target
  }

  return (
    <div className="timeline grid" style={{ gap: 8 }}>
      <div className="legend">
        <span className="legend-swatch" style={{ background: '#fee2e2' }} /> 0
        <span className="legend-swatch" style={{ background: '#fde68a' }} /> &lt; {minStaffDefault}
        <span className="legend-swatch" style={{ background: '#bbf7d0' }} /> = {minStaffDefault}
        <span className="legend-swatch" style={{ background: '#bfdbfe' }} /> &gt; {minStaffDefault}
      </div>

      {showProbe && (
        <div className="timeline-controls row" style={{ gap: 8 }}>
          <span className="label">Quick check</span>
          <input
            className="input"
            type="time"
            step={900}
            value={`${String(Math.floor(probeMin / 60)).padStart(2, '0')}:${String(
              probeMin % 60
            ).padStart(2, '0')}`}
            onChange={(e) => {
              const [h, m] = e.target.value.split(':').map(Number)
              setProbeMin(h * 60 + m)
            }}
          />
          <span style={{ fontSize: 12, color: 'var(--muted)' }}>
            {format12(
              `${String(Math.floor(probeMin / 60)).padStart(2, '0')}:${String(
                probeMin % 60
              ).padStart(2, '0')}`
            )}
          </span>
        </div>
      )}

      {data.map((day) => {
        if (!day.open || !day.close) {
          return (
            <div key={day.weekday} className="timeline-row">
              <div className="label">{day.weekday_name}</div>
              <div className="timeline-bar" style={{ justifyContent: 'center' }}>
                <span className="label">Closed</span>
              </div>
            </div>
          )
        }

        const openM = hhmmToMin(day.open)
        const closeM = hhmmToMin(day.close)
        const spanM = Math.max(1, closeM - openM)

        return (
          <div key={day.weekday} className="timeline-row">
            <div className="label" style={{ width: 80 }}>
              {day.weekday_name}
            </div>
            <div className="timeline-bar" style={{ position: 'relative' }}>
              {day.segments.map((seg, idx) => {
                const s = hhmmToMin(seg.start)
                const e = hhmmToMin(seg.end)
                const wPct = ((e - s) / spanM) * 100
                const border = idx === day.segments.length - 1 ? 'none' : '1px solid var(--border)'
                return (
                  <div
                    key={idx}
                    className="seg"
                    title={`${format12(seg.start)}–${format12(seg.end)} • ${seg.count} scheduled`}
                    style={{
                      width: `${wPct}%`,
                      background: colorFor(seg.count),
                      borderRight: border,
                    }}
                  >
                    <span className="seg-label">{seg.count}</span>
                  </div>
                )
              })}

              {/* Hour ticks */}
              {(() => {
                const nodes = []
                let h = Math.ceil(openM / 60) * 60
                for (; h < closeM; h += 60) {
                  const left = ((h - openM) / spanM) * 100
                  nodes.push(<div key={h} className="tick-hour" style={{ left: `${left}%` }} />)
                }
                return nodes
              })()}

              {/* Probe line */}
              {probeMin >= openM && probeMin <= closeM && (
                <div
                  className="probe-line"
                  style={{ left: `${((probeMin - openM) / spanM) * 100}%` }}
                />
              )}
            </div>

            <div className="count-pill">{countAt(day, probeMin)}</div>

            <div
              className="row"
              style={{ justifyContent: 'space-between', fontSize: 12, color: 'var(--muted)' }}
            >
              <span>{format12(day.open)}</span>
              <span>{format12(day.close)}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
