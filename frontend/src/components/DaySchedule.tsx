import { hhmmToMin, format12 } from '../lib/time'

type DayShift = {
  employee_name: string
  weekday: number     // 0=Sun .. 6=Sat
  weekday_name: string
  start: string       // "HH:MM"
  end: string         // "HH:MM"
}

export function DaySchedule({ shifts, weekStart }: { shifts: DayShift[], weekStart?: string }) {
  // Labels by grid indexing (0=Sun..6=Sat) - matches backend's WEEKDAYS array
  const labels: Record<number, string> = {
    0:'Sun', 1:'Mon', 2:'Tue', 3:'Wed', 4:'Thu', 5:'Fri', 6:'Sat'
  }
  // Display order: Sunday first (0), then Mon..Sat (1..6)
  const order: number[] = [0, 1, 2, 3, 4, 5, 6]

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
  
  // week_start from backend is already the Sunday of the week (0=Sun in our system)
  const sundayBase: Date | null = weekStart ? parseYmdLocal(weekStart) : null

  // Our grid indexing is Sun=0..Sat=6, so add the weekday index as days offset from Sunday
  const dateForWeekday = (weekdayGridIndex: number): string | null => {
    if (!sundayBase) return null
    // Create a new date by adding days to the Sunday base
    const targetDate = new Date(sundayBase)
    targetDate.setDate(sundayBase.getDate() + weekdayGridIndex)
    return formatMDY(targetDate)
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
