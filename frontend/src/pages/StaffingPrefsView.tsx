import { useEffect, useState } from 'react'

type StaffingWindow = {
  id: number
  weekday: number
  start_time: string
  end_time: string
  min_staff?: number | null
  max_staff?: number | null
  prefer_full_length: boolean
}

type GlobalSettings = {
  coordinator_opening_mon: boolean
  coordinator_opening_tue: boolean
  coordinator_opening_wed: boolean
  coordinator_opening_thu: boolean
  coordinator_opening_fri: boolean
  coordinator_opening_sat: boolean
  coordinator_opening_sun: boolean
  coordinator_open_window_minutes: number
}

const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const dayKeyOrder: (keyof GlobalSettings)[] = [
  'coordinator_opening_mon',
  'coordinator_opening_tue',
  'coordinator_opening_wed',
  'coordinator_opening_thu',
  'coordinator_opening_fri',
  'coordinator_opening_sat',
  'coordinator_opening_sun',
]
function openingKey(idx: number): keyof GlobalSettings {
  return dayKeyOrder[idx]
}

export default function StaffingPrefsView() {
  const [rows, setRows] = useState<StaffingWindow[]>([])
  const [gs, setGs] = useState<GlobalSettings | null>(null)

  const [weekday, setWeekday] = useState(0)
  const [start, setStart] = useState('07:00')
  const [end, setEnd] = useState('09:00')
  const [minStaff, setMinStaff] = useState<string>('')
  const [maxStaff, setMaxStaff] = useState<string>('')
  const [prefFull, setPrefFull] = useState(false)

  useEffect(() => {
    ;(async () => {
      const r1 = await fetch('/api/staffing-windows')
      setRows(await r1.json())
      const r2 = await fetch('/api/settings/global')
      setGs(await r2.json())
    })()
  }, [])

  const addWindow = async () => {
    const payload = {
      weekday,
      start_time: start,
      end_time: end,
      min_staff: minStaff ? Number(minStaff) : null,
      max_staff: maxStaff ? Number(maxStaff) : null,
      prefer_full_length: prefFull,
    }
    const r = await fetch('/api/staffing-windows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const rec: StaffingWindow = await r.json()
    setRows((prev) => [...prev, rec])
  }

  const delWindow = async (id: number) => {
    await fetch(`/api/staffing-windows/${id}`, { method: 'DELETE' })
    setRows((prev) => prev.filter((x) => x.id !== id))
  }

  const saveGs = async (patch: Partial<GlobalSettings>) => {
    if (!gs) return
    const next: GlobalSettings = { ...gs, ...patch }
    setGs(next)
    await fetch('/api/settings/global', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(next),
    })
  }

  const quickWeekdayCapBefore = async () => {
    // Creates windows Mon..Fri 00:00–07:00 with max_staff=2
    for (let d = 0; d <= 4; d++) {
      const payload = {
        weekday: d,
        start_time: '00:00',
        end_time: '07:00',
        min_staff: null as number | null,
        max_staff: 2,
        prefer_full_length: false,
      }
      const r = await fetch('/api/staffing-windows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const rec: StaffingWindow = await r.json()
      setRows((prev) => [...prev, rec])
    }
  }

  return (
    <div className="section">
      <h2>Staffing Preferences</h2>

      <div className="panel" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>Coordinator Opening</h3>
        {gs && (
          <div
            className="grid"
            style={{ gap: 8, gridTemplateColumns: 'repeat(7, minmax(120px,1fr))' }}
          >
            {dayLabels.map((label, idx) => {
              const key = openingKey(idx)
              return (
                <label key={key} className="row" style={{ gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={Boolean(gs[key])}
                    onChange={(e) => saveGs({ [key]: e.target.checked })}
                  />
                  {label}
                </label>
              )
            })}
          </div>
        )}
        {gs && (
          <div className="row" style={{ gap: 8, marginTop: 8 }}>
            <div className="label">Opening window (mins)</div>
            <input
              className="input"
              type="number"
              min={15}
              step={15}
              value={gs.coordinator_open_window_minutes}
              onChange={(e) =>
                saveGs({ coordinator_open_window_minutes: Number(e.target.value) })
              }
            />
          </div>
        )}
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>Windows</h3>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
          <select className="input" value={weekday} onChange={(e) => setWeekday(Number(e.target.value))}>
            {dayLabels.map((d, i) => (
              <option value={i} key={i}>
                {d}
              </option>
            ))}
          </select>
          <input className="input" type="time" value={start} onChange={(e) => setStart(e.target.value)} />
          <input className="input" type="time" value={end} onChange={(e) => setEnd(e.target.value)} />
          <input
            className="input"
            type="number"
            min={0}
            placeholder="Soft min (optional)"
            value={minStaff}
            onChange={(e) => setMinStaff(e.target.value)}
          />
          <input
            className="input"
            type="number"
            min={0}
            placeholder="Hard max (optional)"
            value={maxStaff}
            onChange={(e) => setMaxStaff(e.target.value)}
          />
          <label className="row" style={{ gap: 6 }}>
            <input type="checkbox" checked={prefFull} onChange={(e) => setPrefFull(e.target.checked)} />
            Prefer full-length shifts
          </label>
          <button className="button" onClick={addWindow}>
            Add
          </button>
          <button className="button" onClick={quickWeekdayCapBefore}>
            Quick add: Weekday ≤2 before 7:00
          </button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Day</th>
              <th>Start</th>
              <th>End</th>
              <th>Soft Min</th>
              <th>Hard Max</th>
              <th>Full-length</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{dayLabels[r.weekday]}</td>
                <td>{r.start_time}</td>
                <td>{r.end_time}</td>
                <td>{r.min_staff ?? ''}</td>
                <td>{r.max_staff ?? ''}</td>
                <td>{r.prefer_full_length ? 'Yes' : ''}</td>
                <td>
                  <button className="button" onClick={() => delWindow(r.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="label">
        Tip: for “Sunday min 4 all day”, add a Sunday window open→close with Soft Min = 4 and check “Prefer
        full-length”.
      </div>
    </div>
  )
}
