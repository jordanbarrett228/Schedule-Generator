import { useEffect, useState, useRef } from 'react'
import { CoverageTimeline } from '../components/CoverageTimeline'
import DaySchedule from '../components/DaySchedule'
import { format12, hhmmToMin } from '../lib/time'
import { api } from '../utils/api'
import { useSchedule } from '../context/ScheduleContext'

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
  const { isGenerating, progress, setIsGenerating, setProgress } = useSchedule()
  const pollingRef = useRef(false)

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

  // Poll for results when generation is active (even if navigated away)
  useEffect(() => {
    if (!isGenerating || pollingRef.current) return

    pollingRef.current = true
    console.log('[Dashboard] Starting result polling')

    const pollResult = async () => {
      if (!pollingRef.current) {
        console.log('[Dashboard] Polling stopped')
        return
      }

      try {
        const json = await api.get('/api/schedule/result')
        console.log('[Dashboard] Poll result:', json)

        if (json.status === 'generating') {
          // Still running, poll again
          setTimeout(pollResult, 500)
        } else if (json.status === 'error') {
          console.error('Schedule generation error:', json.error)
          setIsGenerating(false)
          setProgress({ count: 0, elapsed: 0 })
          pollingRef.current = false
        } else if (json.status === 'no_result') {
          // No result yet, might have just started
          setTimeout(pollResult, 500)
        } else if (json.status === 'optimal' || json.status === 'feasible' || json.status === 'feasible_relaxed' || json.status === 'infeasible') {
          // Got a valid schedule result!
          console.log('[Dashboard] Setting result:', json)
          setResult(json)
          setIsGenerating(false)
          setProgress({ count: 0, elapsed: 0 })
          pollingRef.current = false

          // Persist to localStorage
          try {
            localStorage.setItem(LS_KEY_RESULT, JSON.stringify(json))
            if (weekStart) localStorage.setItem(LS_KEY_WEEK, weekStart)
          } catch (err) {
            console.error('Failed to save to localStorage:', err)
          }
        } else {
          // Unexpected status
          console.warn('[Dashboard] Unexpected status:', json.status)
          setTimeout(pollResult, 500)
        }
      } catch (error) {
        console.error('[Dashboard] Poll error:', error)
        setTimeout(pollResult, 1000) // Retry on error
      }
    }

    // Start polling
    setTimeout(pollResult, 500)

    // Cleanup on unmount
    return () => {
      console.log('[Dashboard] Component unmounting, stopping polling')
      pollingRef.current = false
    }
  }, [isGenerating, weekStart, setIsGenerating, setProgress])

  const generate = async () => {
    setIsGenerating(true)
    setProgress({ count: 0, elapsed: 0 })
    pollingRef.current = false // Reset polling flag

    try {
      const body = weekStart ? { week_start: weekStart } : {}
      // Start the solver (returns immediately)
      await api.post('/api/schedule/generate', body)
      // Polling will start via useEffect
    } catch (error) {
      console.error('Failed to start schedule generation:', error)
      setIsGenerating(false)
      setProgress({ count: 0, elapsed: 0 })
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
    //    result.week_start is ISO "YYYY-MM-DD" (Sunday - backend guarantees this)
    const sundayBase = new Date(result.week_start + 'T00:00:00')  // local

    // 3) CSV header
    const rows: string[][] = [
      ['Position', 'Date', 'Begin time', 'End time', 'Employee name']
    ]

    // 4) Fill rows
    // WhenToWork expects: Date = mm/dd/yyyy; times as "hh:mm am/pm"
    for (const s of result.shifts) {
      // Add weekday offset (0=Sun..6=Sat) to Sunday base using proper date arithmetic
      const dayDate = new Date(sundayBase)
      dayDate.setDate(sundayBase.getDate() + s.weekday)
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
            disabled={isGenerating}
          />
        </label>
        <button className="button primary" onClick={generate} disabled={isGenerating}>
          {isGenerating ? 'Generating...' : 'Generate Week'}
        </button>
        <button className="button" onClick={clearSaved} disabled={isGenerating}>Clear</button>
        <button className="button" onClick={exportWhenToWork} disabled={!result || result.shifts.length === 0 || isGenerating}>Export WhenToWork CSV</button>
      </div>

      {/* Progress Bar */}
      {isGenerating && (
        <div className="panel" style={{ marginBottom: 12, padding: 16 }}>
          <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong>Optimizing schedule...</strong>
            <span style={{ fontSize: '0.9em', color: '#666' }}>
              {progress.count > 0 ? `${progress.count} solution${progress.count > 1 ? 's' : ''} found (${progress.elapsed}s)` : 'Starting...'}
            </span>
          </div>
          <div style={{
            width: '100%',
            height: 8,
            backgroundColor: '#e5e7eb',
            borderRadius: 4,
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div style={{
              height: '100%',
              backgroundColor: '#3b82f6',
              animation: 'progress-slide 2s ease-in-out infinite',
              width: '30%',
            }} />
          </div>
          <style>{`
            @keyframes progress-slide {
              0% { transform: translateX(-100%); }
              100% { transform: translateX(400%); }
            }
          `}</style>
        </div>
      )}

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
