import { hhmmToMin, format12 } from '../lib/time'
import type { JSX } from 'react/jsx-runtime';

type CoverageSegment = { start: string; end: string; count: number }
type CoverageDay = {
  weekday: number
  weekday_name: string
  open: string | null
  close: string | null
  segments: CoverageSegment[] | undefined
}

type Props = {
  data: CoverageDay[] | undefined | null
  minStaffDefault: number
}

export function CoverageTimeline({ data, minStaffDefault }: Props) {
  const colorFor = (count: number) => {
    if (count <= 0) return '#fee2e2'            // under 1
    if (count < minStaffDefault) return '#fde68a' // below target
    if (count === minStaffDefault) return '#bbf7d0' // meets target
    return '#bfdbfe'                             // exceeds target
  }

  const days = Array.isArray(data) ? data : []
  if (days.length === 0) {
    return <div className="label">No coverage to display.</div>
  }

  return (
    <div className="timeline grid" style={{ gap: 16 }}>
      <div className="legend" style={{ marginBottom: 18 }}>
        <span className="legend-swatch" style={{ background: '#fee2e2' }} /> 0
        <span className="legend-swatch" style={{ background: '#fde68a' }} /> &lt; {minStaffDefault}
        <span className="legend-swatch" style={{ background: '#bbf7d0' }} /> = {minStaffDefault}
        <span className="legend-swatch" style={{ background: '#bfdbfe' }} /> &gt; {minStaffDefault}
      </div>

      {days.map((day) => {
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

        // Fallback: if segments are missing/empty, show a single 0-coverage segment
        const segments: CoverageSegment[] =
          day.segments && day.segments.length
            ? day.segments
            : [{ start: day.open, end: day.close, count: 0 }]

        return (
          <div key={day.weekday} className="timeline-row">
            <div className="label" style={{ width: 130 }}>{day.weekday_name}</div>
            <div className="timeline-bar">
              {/* Colored segments with counts */}
              {segments.map((seg, idx) => {
                const s = hhmmToMin(seg.start)
                const e = hhmmToMin(seg.end)
                const wPct = ((e - s) / spanM) * 100
                const border = idx === segments.length - 1 ? 'none' : '1px solid var(--border)'
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

              {/* Hour ticks + labels (above the bar) */}
              {(() => {
                const nodes: JSX.Element[] = []
                let h = Math.ceil(openM / 60) * 60
                for (; h < closeM; h += 60) {
                  const left = ((h - openM) / spanM) * 100
                  const hhmm = `${String(Math.floor(h / 60)).padStart(2, '0')}:${String(h % 60).padStart(2, '0')}`
                  nodes.push(<div key={`t-${h}`} className="tick-hour" style={{ left: `${left}%` }} />)
                  nodes.push(
                    <div key={`tl-${h}`} className="tick-label" style={{ left: `${left}%` }}>
                      {format12(hhmm)}
                    </div>
                  )
                }
                return nodes
              })()}

              {/* Change lines + labels (below bar) with overlap culling */}
              {(() => {
                const nodes: JSX.Element[] = []
                let lastLeftPct = -999
                const minGapPct = 8  // require 8% of bar width between labels

                for (let i = 1; i < segments.length; i++) {
                  const cpMin = hhmmToMin(segments[i].start)
                  const leftPct = ((cpMin - openM) / spanM) * 100

                  // Cull if too close to previous label
                  if (leftPct - lastLeftPct < minGapPct) {
                    nodes.push(<div key={`cl-${i}`} className="change-line" style={{ left: `${leftPct}%` }} />)
                    continue
                  }

                  nodes.push(<div key={`cl-${i}`} className="change-line" style={{ left: `${leftPct}%` }} />)
                  nodes.push(
                    <div key={`lbl-${i}`} className="change-label" style={{ left: `${leftPct}%` }}>
                      {format12(segments[i].start)}
                    </div>
                  )
                  lastLeftPct = leftPct
                }

                // Edge labels (bottom corners)
                nodes.push(<div key="edgeL" className="edge-label left">{format12(day.open)}</div>)
                nodes.push(<div key="edgeR" className="edge-label right">{format12(day.close)}</div>)
                return nodes
              })()}
            </div>
          </div>
        )
      })}
    </div>
  )
}
