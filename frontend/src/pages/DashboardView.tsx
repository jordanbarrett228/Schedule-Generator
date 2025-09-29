import { useEffect, useState } from 'react'
import { CoverageTimeline } from '../components/CoverageTimeline'
import DaySchedule from '../components/DaySchedule'
import { format12 } from '../lib/time'

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
type ScheduleResult = {
  status: string
  week_start: string
  slot_minutes: number
  min_staff_default: number
  shifts: Shift[]
  employee_hours: EmployeeHours[]
  coverage: CoverageDay[]
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
      if (cachedWeek) {
        setWeekStart(cachedWeek)
      }
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
    } catch { // ignore 
        }
  }

  return (
    <div className="section">
      <h2>Dashboard</h2>
      <div className="row" style={{ gap: 12, marginBottom: 12 }}>
        <label className="row" style={{ gap: 8 }}>
          Week start (Mon)
          <input
            className="input"
            type="date"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
          />
        </label>
        <button className="button primary" onClick={generate}>Generate Week</button>
        <button className="button" onClick={clearSaved}>Clear</button>
      </div>

      {result && (
        <>
          <div className="dash-grid">
            {/* Left: Hours/week */}
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>Hours (week)</h3>
              {result.employee_hours?.length ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Hours</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.employee_hours.map((eh) => (
                      <tr key={eh.employee_id}>
                        <td>{eh.employee_name}</td>
                        <td>{eh.hours.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="label">No hours.</div>
              )}
            </div>

            {/* Middle: Shifts list */}
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>Shifts</h3>
              <div className="row" style={{ gap: 16, marginBottom: 8 }}>
                <div>
                  <b>Status:</b> {result.status}
                </div>
                <div>
                  <b>Week Start:</b> {result.week_start}
                </div>
              </div>
              <table className="table">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Day</th>
                    <th>Start</th>
                    <th>End</th>
                  </tr>
                </thead>
                <tbody>
                  {result.shifts?.map((s: Shift, idx: number) => (
                    <tr key={idx}>
                      <td>{s.employee_name}</td>
                      <td>{s.weekday_name}</td>
                      <td>{format12(s.start)}</td>
                      <td>{format12(s.end)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Right: Coverage timeline */}
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>Coverage by Day</h3>
              <CoverageTimeline
                data={result.coverage}
                minStaffDefault={result.min_staff_default}
              />
            </div>
          </div>

          {/* NEW: Daily schedule (grouped by day, sorted by start time) */}
          <div className="panel" style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>Daily Schedule</h3>
            <DaySchedule shifts={result.shifts} />
          </div>
        </>
      )}
    </div>
  )
}
