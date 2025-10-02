import { hhmmToMin, format12 } from '../lib/time'

type DayShift = {
  employee_name: string
  weekday: number     // 0=Mon .. 6=Sun
  weekday_name: string
  start: string       // "HH:MM"
  end: string         // "HH:MM"
}

export function DaySchedule({ shifts, weekStart }: { shifts: DayShift[], weekStart?: string }) {
  // Labels by internal weekday indexing (0=Mon..6=Sun)
  const labels: Record<number, string> = {
    0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'
  }
  // Display order: Sunday first, then Mon..Sat
  const order: number[] = [6, 0, 1, 2, 3, 4, 5]

  // Group by weekday
  const byDay: Record<number, DayShift[]> = { 0:[],1:[],2:[],3:[],4:[],5:[],6:[] }
  for (const s of shifts) {
    byDay[s.weekday] = byDay[s.weekday] || []
    byDay[s.weekday].push(s)
  }
  // Sort each day by start time
  for (const d of Object.keys(byDay)) {
    byDay[Number(d)].sort((a, b) => hhmmToMin(a.start) - hhmmToMin(b.start))
  }

  // --- Date helpers (local, timezone-safe) ---
  const parseYmdLocal = (ymd: string): Date => {
    const [Y, M, D] = ymd.split('-').map(n => parseInt(n, 10))
    return new Date(Y, (M ?? 1) - 1, D ?? 1) // local time constructor avoids TZ shifts
  }
  const formatMDY = (dt: Date): string => {
    const mm = dt.getMonth() + 1
    const dd = dt.getDate()
    const yyyy = dt.getFullYear()
    return `${mm}/${dd}/${yyyy}`
  }
  // Given any date, get the Sunday of that week (local). JS Date.getDay(): Sun=0..Sat=6.
  const startDate = weekStart ? parseYmdLocal(weekStart) : null
  const sundayBase: Date | null = startDate
    ? new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() - startDate.getDay())
    : null

  // Our internal weekday indexing is Mon=0..Sun=6.
  // Map that to an offset from Sunday (Sun=0..Sat=6).
  const offsetFromSunday = (weekdayMon0: number): number => (weekdayMon0 === 6 ? 0 : weekdayMon0 + 1)

  const dateForWeekday = (weekdayMon0: number): string | null => {
    if (!sundayBase) return null
    const off = offsetFromSunday(weekdayMon0)
    const d = new Date(sundayBase.getFullYear(), sundayBase.getMonth(), sundayBase.getDate() + off)
    return formatMDY(d)
  }

  return (
    <div className="day-grid">
      {order.map((w) => {
        const rows = byDay[w] || []
        const dateText = dateForWeekday(w)
        return (
          <div className="day-card" key={w}>
            <div className="day-card-head">
              <h4>
                {labels[w]}{dateText ? ` ${dateText}` : ''}
              </h4>
              <span className="label">{rows.length} shift{rows.length === 1 ? '' : 's'}</span>
            </div>
            {rows.length === 0 ? (
              <div className="label">— No shifts —</div>
            ) : (
              <ul className="shift-list">
                {rows.map((s, i) => (
                  <li
                    className="shift-item"
                    key={i}
                    title={`${format12(s.start)}–${format12(s.end)} • ${s.employee_name.trim().split(/\s+/)[0]}`}
                  >
                    <span className="shift-time">{format12(s.start)}–{format12(s.end)}</span>
                    <span className="shift-employee">{s.employee_name.trim().split(/\s+/)[0]}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default DaySchedule
