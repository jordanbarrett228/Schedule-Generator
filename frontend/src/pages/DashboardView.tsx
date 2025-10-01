import { useEffect, useState } from 'react'
import { CoverageTimeline } from '../components/CoverageTimeline'
import DaySchedule from '../components/DaySchedule'
import { format12, hhmmToMin } from '../lib/time'

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
    const res = await fetch('/api/schedule/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const json: ScheduleResult = await res.json()
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

  return (
    <div className="section">
      <h2>Dashboard</h2>

      {/* Controls */}
      <div className="row" style={{ gap: 12, marginBottom: 12 }}>
        {/* <label className="row" style={{ gap: 8 }}>
          Week start (Mon)
          <input
            className="input"
            type="date"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
          />
        </label> */}
        <button className="button primary" onClick={generate}>Generate Week</button>
        <button className="button" onClick={clearSaved}>Clear</button>
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
            <DaySchedule shifts={result.shifts} />
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
                          ({daysOff} days off, {emp.totalHours.toFixed(1)} h)
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
                            const dur = hoursBetween(s.start, s.end).toFixed(1);
                            return (
                              <li key={idx} className="shift-row">
                                <span className="shift-row__day">{s.weekday_name}</span>
                                <span className="shift-row__time">
                                  {format12(s.start)}–{format12(s.end)}
                                </span>
                                <span className="shift-row__pill" title={`${dur} hours`}>{dur} h</span>
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
