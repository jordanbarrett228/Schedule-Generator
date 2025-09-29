import { hhmmToMin, format12 } from '../lib/time'

type DayShift = {
  employee_name: string
  weekday: number
  weekday_name: string
  start: string // "HH:MM"
  end: string   // "HH:MM"
}

export function DaySchedule({ shifts }: { shifts: DayShift[] }) {
  const days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

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

  return (
    <div className="day-grid">
      {days.map((label, d) => {
        const rows = byDay[d] || []
        return (
          <div className="day-card" key={d}>
            <div className="day-card-head">
              <h4>{label}</h4>
              <span className="label">{rows.length} shift{rows.length === 1 ? '' : 's'}</span>
            </div>
            {rows.length === 0 ? (
              <div className="label">— No shifts —</div>
            ) : (
              <ul className="shift-list">
                {rows.map((s, i) => (
                  <li className="shift-item" key={i} title={`${format12(s.start)}–${format12(s.end)} • ${s.employee_name}`}>
                    <span className="shift-time">{format12(s.start)}–{format12(s.end)}</span>
                    <span className="shift-employee">{s.employee_name}</span>
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
