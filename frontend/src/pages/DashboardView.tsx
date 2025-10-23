import { useEffect, useState } from 'react'
import { CoverageTimeline } from '../components/CoverageTimeline'
import DaySchedule from '../components/DaySchedule'
import { format12, hhmmToMin } from '../lib/time'
import { api } from '../utils/api';

const hoursBetween = (start: string, end: string) =>
  Math.max(0, hhmmToMin(end) - hhmmToMin(start)) / 60;

type Shift = {
  employee_id: number
  employee_name: string
  weekday: number
  weekday_name: string
  start: string
  end: string
}
type EmployeeHours = { employee_id: number; employee_name: string; hours: number }
type CoverageSegment = { start: string; end: string; count: number }
type CoverageDay = {
  weekday: number
  weekday_name: string
  open: string | null
  close: string | null
  segments: CoverageSegment[]
}
type Diagnostic = {
  severity: 'error' | 'warning' | 'info' | string
  code: string
  message: string
  day?: number
  time?: string
  employee_id?: number
  employee_name?: string
}
type ScheduleResult = {
  status: string
  week_start: string
  slot_minutes: number
  min_staff_default: number
  shifts: Shift[]
  employee_hours: EmployeeHours[]
  coverage: CoverageDay[]
  diagnostics?: Diagnostic[]
}

const LS_KEY_RESULT = 'schedule:lastResult'
const LS_KEY_WEEK = 'schedule:lastWeekStart'

function formatDate_mmddyyyy(iso: string) {
  // iso = "YYYY-MM-DD"
  const [year, month, day] = iso.split("-");
  return `${month}/${day}/${year}`;
}

export default function DashboardView() {
  const [weekStart, setWeekStart] = useState<string>('')
  const [result, setResult] = useState<ScheduleResult | null>(null)

  // Restore last generated schedule on mount
  useEffect(() => {
    try {
      const cached = localStorage.getItem(LS_KEY_RESULT)
      const cachedWeek = localStorage.getItem(LS_KEY_WEEK)
      if (cached) {
        const parsed: ScheduleResult = JSON.parse(cached)
        setResult(parsed)
      }
      if (cachedWeek) setWeekStart(cachedWeek)
    } catch {
      // ignore parse/storage errors
    }
  }, [])

  const generate = async () => {
    const body = weekStart ? { week_start: weekStart } : {}
    const json: ScheduleResult = await api.post('/api/schedule/generate', body)
    setResult(json)

    // Persist to localStorage so it survives route changes/page reloads
    try {
      localStorage.setItem(LS_KEY_RESULT, JSON.stringify(json))
      if (weekStart) localStorage.setItem(LS_KEY_WEEK, weekStart)
    } catch {
      // storage may be unavailable; fail silently
    }
  }

  const clearSaved = () => {
    setResult(null)
    try {
      localStorage.removeItem(LS_KEY_RESULT)
      // localStorage.removeItem(LS_KEY_WEEK) // keep or remove as you prefer
    } catch {
      // ignore
    }
  }

  const exportWhenToWork = async () => {
    if (!result) return

    // 1) Build a map of employee positions (id -> position)
    type EmpRecord = { id: number; name: string; position?: string }
    const empMap = new Map<number, string>()
    try {
      const emps: EmpRecord[] = await api.get('/api/employees')
      for (const e of emps) {
        empMap.set(e.id, e.position && e.position.trim() ? e.position.trim() : 'Guest Services Specialist')
      }
    } catch {
      // fallback: if fetch fails, all default to GSS
    }

    // 2) Turn week_start + weekday into actual dates
    //    result.week_start is ISO "YYYY-MM-DD" (Monday)
    const base = new Date(result.week_start + 'T00:00:00')  // local
    const y = base.getFullYear(), m = base.getMonth(), d = base.getDate()

    // 3) CSV header
    const rows: string[][] = [
      ['Position', 'Date', 'Begin time', 'End time', 'Employee name']
    ]

    // 4) Fill rows
    // WhenToWork expects: Date = dd/mm/yyyy; times as "hh:mm am/pm"
    for (const s of result.shifts) {
      const dayDate = new Date(y, m, d + s.weekday)
      const dateStr = formatDate_mmddyyyy(dayDate.toISOString().slice(0,10))
      const begin = format12(s.start)  // your helper returns "h:mm AM/PM"
      const end   = format12(s.end)
      const position = empMap.get(s.employee_id) ?? 'Guest Services Specialist'

      rows.push([position, dateStr, begin, end, s.employee_name])
    }

    // 5) Serialize CSV
    const escaped = rows.map(cols =>
      cols.map(c => /[",\n]/.test(c) ? `"${c.replace(/"/g,'""')}"` : c).join(',')
    ).join('\r\n')

    const blob = new Blob([escaped], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `schedule_whentowork_${result.week_start}.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }


  return (
    <div className="section">
      <h2>Dashboard</h2>

      {/* Controls */}
      <div className="row" style={{ gap: 12, marginBottom: 12 }}>
        <label className="row" style={{ gap: 8 }}>
          Week start (Sun)
          <input
            className="input"
            type="date"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
          />
        </label>
        <button className="button primary" onClick={generate}>Generate Week</button>
        <button className="button" onClick={clearSaved}>Clear</button>
        <button className="button" onClick={exportWhenToWork} disabled={!result || result.shifts.length === 0}>Export WhenToWork CSV</button>
      </div>

      {/* Diagnostics */}
      {result?.diagnostics && result.diagnostics.length > 0 && (
        <div className="panel" style={{ marginTop: 12 }}>
          <h3 style={{ marginTop: 0 }}>
            Diagnostics <span className="label">({result.diagnostics.length})</span>
          </h3>
          <ul style={{ margin: 0, paddingLeft: 18, maxHeight: 200, overflowY: 'auto' }}>
            {result.diagnostics.map((d, i) => (
              <li key={i}>
                <span
                  style={{
                    fontWeight: d.severity === 'error' ? 700 : 500,
                    color: d.severity === 'error' ? '#b91c1c' : undefined,
                  }}
                >
                  [{d.code}] {d.message}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result && (
        <>
          {/* 1) Daily schedule at the TOP */}
          <div className="panel" style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>Daily Schedule</h3>
            <DaySchedule shifts={result.shifts} weekStart={result.week_start} />
          </div>

          {/* Coverage timeline */}
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Coverage by Day</h3>
            <CoverageTimeline
              data={result.coverage ?? []}
              minStaffDefault={result.min_staff_default}
            />
          </div>
          {/* Shifts by employee (columns) with days-off + weekly hours */}
          <div className="panel" style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>Shifts</h3>
            <div className="row" style={{ gap: 16, marginBottom: 8 }}>
              <div><b>Status:</b> {result.status}</div>
              <div><b>Week Start:</b> {result.week_start}</div>
            </div>

            <div className="shifts-grid">
              {Object.values(
                result.shifts.reduce((acc, s) => {
                  if (!acc[s.employee_id]) {
                    acc[s.employee_id] = {
                      id: s.employee_id,
                      name: s.employee_name,
                      shifts: [] as Shift[],
                      weekdays: new Set<number>(),
                      totalHours: 0,
                    };
                  }
                  acc[s.employee_id].shifts.push(s);
                  acc[s.employee_id].weekdays.add(s.weekday);
                  acc[s.employee_id].totalHours += hoursBetween(s.start, s.end);
                  return acc;
                }, {} as Record<number, { id:number; name:string; shifts:Shift[]; weekdays:Set<number>; totalHours:number }>)
              )
                // optional: sort employees by name
                .sort((a, b) => a.name.localeCompare(b.name))
                .map(emp => {
                  const daysWorked = emp.weekdays.size;
                  const daysOff = 7 - daysWorked;
                  return (
                    <div key={emp.id} className="shift-col">
                      <h4>
                        {emp.name}{' '}
                        <span style={{ color: '#666', fontSize: '0.9em' }}>
                          ({daysOff} days off, {emp.totalHours.toFixed(2).replace(/\.?0+$/, '')} h)
                        </span>
                      </h4>
                      <ul>
                        {emp.shifts
                          .slice()
                          .sort((a, b) =>
                            a.weekday === b.weekday
                              ? hhmmToMin(a.start) - hhmmToMin(b.start)
                              : a.weekday - b.weekday
                          )
                          .map((s, idx) => {
                            const dur = hoursBetween(s.start, s.end);
                            const durFixed = dur.toFixed(2).replace(/\.?0+$/, '');
                            return (
                              <li key={idx} className="shift-row">
                                <span className="shift-row__day">{s.weekday_name}</span>
                                <span className="shift-row__time">
                                  {format12(s.start)}–{format12(s.end)}
                                </span>
                                <span className="shift-row__pill" title={`${durFixed} hours`}>{durFixed} h</span>
                              </li>
                            );
                          })}
                      </ul>
                    </div>
                  );
                })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
