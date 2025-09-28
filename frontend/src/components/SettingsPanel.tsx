import { useEffect, useState } from 'react'

export type GlobalSettings = {
  id: number
  min_staff_default: number
  business_open: string // "HH:MM:SS" from API
  business_close: string
}

export type CoveragePeak = {
  id: number
  date?: string | null
  weekday?: number | null
  start_time: string
  end_time: string
  min_staff: number
}

const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function SettingsPanel() {
  const [gs, setGs] = useState<GlobalSettings | null>(null)
  const [peaks, setPeaks] = useState<CoveragePeak[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const [g, p] = await Promise.all([
      fetch('/api/settings/global').then(r => r.json()),
      fetch('/api/coverage/peaks').then(r => r.json()),
    ])
    setGs(g)
    setPeaks(p)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  const save = async () => {
    if (!gs) return
    await fetch('/api/settings/global', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(gs),
    })
    await load()
  }

  const addPeak = async (peak: Omit<CoveragePeak, 'id'>) => {
    const res = await fetch('/api/coverage/peaks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(peak),
    })
    const rec = await res.json()
    setPeaks(p => [...p, rec])
  }

  const delPeak = async (id: number) => {
    await fetch(`/api/coverage/peaks/${id}`, { method: 'DELETE' })
    setPeaks(p => p.filter(x => x.id !== id))
  }

  if (loading || !gs) return <div className="section">Loading settings…</div>

  const openHHMM = gs.business_open.slice(0, 5)
  const closeHHMM = gs.business_close.slice(0, 5)

  return (
    <div className="section grid" style={{ gap: 12 }}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <strong>Global Settings</strong>
        <button className="button primary" onClick={save}>Save</button>
      </div>

      <div className="row" style={{ gap: 16, flexWrap: 'wrap' }}>
        <label className="row" style={{ gap: 8 }}>
          Min staff default
          <input
            className="input"
            type="number"
            min={0}
            value={gs.min_staff_default}
            onChange={e => setGs({ ...gs, min_staff_default: +e.target.value })}
          />
        </label>

        <label className="row" style={{ gap: 8 }}>
          Business open
          <input
            className="input"
            type="time"
            value={openHHMM}
            onChange={e => setGs({ ...gs, business_open: e.target.value + ':00' })}
          />
        </label>

        <label className="row" style={{ gap: 8 }}>
          Business close
          <input
            className="input"
            type="time"
            value={closeHHMM}
            onChange={e => setGs({ ...gs, business_close: e.target.value + ':00' })}
          />
        </label>
      </div>

      <div className="grid" style={{ gap: 8 }}>
        <strong>Rush / Peak Staffing</strong>
        <AddPeak onAdd={addPeak} />
        <table className="table">
          <thead>
            <tr><th>Scope</th><th>Start</th><th>End</th><th>Min Staff</th><th></th></tr>
          </thead>
          <tbody>
            {peaks.map(p => (
              <tr key={p.id}>
                <td>{p.date ? `Date ${p.date}` : `Weekly ${weekdays[p.weekday ?? 0]}`}</td>
                <td>{p.start_time}</td>
                <td>{p.end_time}</td>
                <td>{p.min_staff}</td>
                <td><button className="button" onClick={() => delPeak(p.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function AddPeak({ onAdd }: { onAdd: (p: Omit<CoveragePeak, 'id'>) => void }) {
  const [mode, setMode] = useState<'weekday' | 'date'>('weekday')
  const [weekday, setWeekday] = useState(0)
  const [date, setDate] = useState('')
  const [start, setStart] = useState('11:00')
  const [end, setEnd] = useState('14:00')
  const [minStaff, setMinStaff] = useState(3)

  const onModeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value === 'date' ? 'date' : 'weekday' // type-safe, no `any`
    setMode(v)
  }

  const submit = () => {
    if (mode === 'weekday') {
      onAdd({ weekday, start_time: start + ':00', end_time: end + ':00', min_staff: minStaff })
    } else if (date) {
      onAdd({ date, start_time: start + ':00', end_time: end + ':00', min_staff: minStaff })
    }
  }

  return (
    <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
      <select value={mode} onChange={onModeChange}>
        <option value="weekday">Weekly</option>
        <option value="date">Specific date</option>
      </select>

      {mode === 'weekday' ? (
        <select value={weekday} onChange={e => setWeekday(+e.target.value)}>
          {weekdays.map((w, i) => (<option key={i} value={i}>{w}</option>))}
        </select>
      ) : (
        <input className="input" type="date" value={date} onChange={e => setDate(e.target.value)} />
      )}

      <input className="input" type="time" value={start} onChange={e => setStart(e.target.value)} />
      <input className="input" type="time" value={end} onChange={e => setEnd(e.target.value)} />
      <input className="input" type="number" min={1} value={minStaff} onChange={e => setMinStaff(+e.target.value)} />
      <button className="button" onClick={submit}>Add</button>
    </div>
  )
}
