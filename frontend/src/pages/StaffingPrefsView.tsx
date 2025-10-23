import { useEffect, useState } from 'react'
import { api } from '../utils/api'

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
      const windows = await api.get('/api/staffing-windows')
      setRows(windows)
      const settings = await api.get('/api/settings/global')
      setGs(settings)
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
    const rec: StaffingWindow = await api.post('/api/staffing-windows', payload)
    setRows((prev) => [...prev, rec])
  }

  const delWindow = async (id: number) => {
    await api.delete(`/api/staffing-windows/${id}`)
    setRows((prev) => prev.filter((x) => x.id !== id))
  }

  const saveGs = async (patch: Partial<GlobalSettings>) => {
    if (!gs) return
    const next: GlobalSettings = { ...gs, ...patch }
    setGs(next)
    await api.put('/api/settings/global', next)
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
      const rec: StaffingWindow = await api.post('/api/staffing-windows', payload)
      setRows((prev) => [...prev, rec])
    }
  }

  return (
    <section className="staffing-prefs-view">
      <h2>Staffing Windows & Coordinator Opening</h2>

      <div style={{ marginBottom: 24 }}>
        <h3>Coordinator Opening</h3>
        <p style={{ fontSize: 13, marginBottom: 8, color: '#666' }}>
          Select which days require a coordinator for the opening window.
        </p>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
          {dayLabels.map((lbl, idx) => {
            const key = openingKey(idx)
            return (
              <label key={idx} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <input
                  type="checkbox"
                  checked={gs ? (gs[key] as boolean) : false}
                  onChange={(e) => saveGs({ [key]: e.target.checked })}
                />
                <span>{lbl}</span>
              </label>
            )
          })}
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
          Opening window (minutes):
          <input
            type="number"
            className="input"
            style={{ width: 80 }}
            value={gs?.coordinator_open_window_minutes ?? 60}
            onChange={(e) => saveGs({ coordinator_open_window_minutes: Number(e.target.value) })}
          />
        </label>
      </div>

      <div style={{ marginBottom: 24 }}>
        <h3>Staffing Windows</h3>
        <p style={{ fontSize: 13, marginBottom: 8, color: '#666' }}>
          Define time windows with specific min/max staffing requirements or full-length preferences.
        </p>

        <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label>
            <div style={{ fontSize: 13, marginBottom: 2 }}>Weekday</div>
            <select className="input" value={weekday} onChange={(e) => setWeekday(Number(e.target.value))}>
              {dayLabels.map((lbl, idx) => (
                <option key={idx} value={idx}>
                  {lbl}
                </option>
              ))}
            </select>
          </label>
          <label>
            <div style={{ fontSize: 13, marginBottom: 2 }}>Start</div>
            <input className="input" type="time" value={start} onChange={(e) => setStart(e.target.value)} />
          </label>
          <label>
            <div style={{ fontSize: 13, marginBottom: 2 }}>End</div>
            <input className="input" type="time" value={end} onChange={(e) => setEnd(e.target.value)} />
          </label>
          <label>
            <div style={{ fontSize: 13, marginBottom: 2 }}>Min Staff</div>
            <input
              className="input"
              type="number"
              style={{ width: 80 }}
              placeholder="–"
              value={minStaff}
              onChange={(e) => setMinStaff(e.target.value)}
            />
          </label>
          <label>
            <div style={{ fontSize: 13, marginBottom: 2 }}>Max Staff</div>
            <input
              className="input"
              type="number"
              style={{ width: 80 }}
              placeholder="–"
              value={maxStaff}
              onChange={(e) => setMaxStaff(e.target.value)}
            />
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <input type="checkbox" checked={prefFull} onChange={(e) => setPrefFull(e.target.checked)} />
            <span style={{ fontSize: 13 }}>Prefer Full</span>
          </label>
          <button className="button" onClick={addWindow}>
            Add Window
          </button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Day</th>
              <th>Start</th>
              <th>End</th>
              <th>Min</th>
              <th>Max</th>
              <th>Pref Full</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{dayLabels[r.weekday]}</td>
                <td>{r.start_time}</td>
                <td>{r.end_time}</td>
                <td>{r.min_staff ?? '–'}</td>
                <td>{r.max_staff ?? '–'}</td>
                <td>{r.prefer_full_length ? 'Yes' : 'No'}</td>
                <td style={{ textAlign: 'right' }}>
                  <button className="button" onClick={() => delWindow(r.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: 16 }}>
          <button className="button" onClick={quickWeekdayCapBefore}>
            Quick Add: Mon–Fri 00:00–07:00 (max=2)
          </button>
        </div>
      </div>
    </section>
  )
}
