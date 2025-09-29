import { useEffect, useState } from 'react'

export type GlobalSettings = {
  id: number
  min_staff_default: number
}

export type BusinessHours = {
  id: number
  weekday: number
  open_time: string // HH:MM:SS
  close_time: string
}

export type CoveragePeak = {
  id: number
  date?: string | null
  weekday?: number | null
  start_time: string
  end_time: string
  min_staff: number
}

const weekdays = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

export function SettingsPanel() {
  const [gs, setGs] = useState<GlobalSettings | null>(null)
  const [bh, setBh] = useState<BusinessHours[]>([])
  const [peaks, setPeaks] = useState<CoveragePeak[]>([])
  const [loading, setLoading] = useState(true)

  async function load(){
    setLoading(true)
    const [g, b, p] = await Promise.all([
      fetch('/api/settings/global').then(r=>r.json()),
      fetch('/api/settings/business_hours').then(r=>r.json()),
      fetch('/api/coverage/peaks').then(r=>r.json()),
    ])
    setGs(g)
    setBh(b)
    setPeaks(p)
    setLoading(false)
  }
  useEffect(()=>{ load() }, [])

  const saveGlobal = async () => {
    if (!gs) return
    await fetch('/api/settings/global', { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(gs) })
  }

  const saveBusinessHours = async () => {
    // send array without ids is okay; backend upserts by weekday
    const payload = bh.map(({weekday, open_time, close_time}) => ({weekday, open_time, close_time}))
    await fetch('/api/settings/business_hours', { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
    await load()
  }

  const addPeak = async (peak: Omit<CoveragePeak,'id'>) => {
    const res = await fetch('/api/coverage/peaks', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(peak) })
    const rec = await res.json()
    setPeaks(p=>[...p, rec])
  }
  const delPeak = async (id:number) => {
    await fetch(`/api/coverage/peaks/${id}`, { method:'DELETE' })
    setPeaks(p=>p.filter(x=>x.id!==id))
  }

  if (loading || !gs) return <div className="section">Loading settings…</div>

  return (
    <div className="grid" style={{gap:16}}>
      <div className="section grid" style={{gap:12}}>
        <div className="row" style={{justifyContent:'space-between'}}>
          <strong>Global</strong>
          <button className="button primary" onClick={saveGlobal}>Save</button>
        </div>
        <label className="row" style={{gap:8, alignItems:'center'}}>
          Min staff default
          <input className="input" type="number" min={0} value={gs.min_staff_default}
            onChange={e=>setGs({...gs, min_staff_default: +e.target.value})} />
        </label>
      </div>

      <div className="section grid" style={{gap:12}}>
        <div className="row" style={{justifyContent:'space-between'}}>
          <strong>Business Hours (per day)</strong>
          <button className="button primary" onClick={saveBusinessHours}>Save</button>
        </div>
        <table className="table">
          <thead><tr><th>Day</th><th>Open</th><th>Close</th></tr></thead>
          <tbody>
            {bh.sort((a,b)=>a.weekday-b.weekday).map(row => (
              <tr key={row.weekday}>
                <td>{weekdays[row.weekday]}</td>
                <td>
                  <input className="input" type="time" value={row.open_time.slice(0,5)}
                    onChange={e=>setBh(prev=>prev.map(r=> r.weekday===row.weekday ? {...r, open_time: e.target.value+':00'} : r))} />
                </td>
                <td>
                  <input className="input" type="time" value={row.close_time.slice(0,5)}
                    onChange={e=>setBh(prev=>prev.map(r=> r.weekday===row.weekday ? {...r, close_time: e.target.value+':00'} : r))} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="section grid" style={{gap:8}}>
        <div className="row" style={{justifyContent:'space-between'}}>
          <strong>Rush / Peak Staffing</strong>
          <AddPeak onAdd={addPeak} />
        </div>
        <table className="table">
          <thead><tr><th>Scope</th><th>Start</th><th>End</th><th>Min Staff</th><th></th></tr></thead>
          <tbody>
            {peaks.map(p=> (
              <tr key={p.id}>
                <td>{p.date ? `Date ${p.date}` : `Weekly ${weekdays[p.weekday ?? 0]}`}</td>
                <td>{p.start_time}</td>
                <td>{p.end_time}</td>
                <td>{p.min_staff}</td>
                <td><button className="button" onClick={()=>delPeak(p.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function AddPeak({ onAdd }: { onAdd: (p: Omit<CoveragePeak,'id'>) => void }){
  const [mode, setMode] = useState<'weekday'|'date'>('weekday')
  const [weekday, setWeekday] = useState(0)
  const [date, setDate] = useState('')
  const [start, setStart] = useState('11:00')
  const [end, setEnd] = useState('14:00')
  const [minStaff, setMinStaff] = useState(3)

  const onModeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value === 'date' ? 'date' : 'weekday'
    setMode(v)
  }

  const submit = () => {
    if (mode==='weekday') onAdd({ weekday, start_time:start+':00', end_time:end+':00', min_staff: minStaff })
    else if (date) onAdd({ date, start_time:start+':00', end_time:end+':00', min_staff: minStaff })
  }

  return (
    <div className="row" style={{gap:8, flexWrap:'wrap'}}>
      <select value={mode} onChange={onModeChange}>
        <option value="weekday">Weekly</option>
        <option value="date">Specific date</option>
      </select>
      {mode==='weekday' ? (
        <select value={weekday} onChange={e=>setWeekday(+e.target.value)}>
          {weekdays.map((w,i)=>(<option key={i} value={i}>{w}</option>))}
        </select>
      ) : (
        <input className="input" type="date" value={date} onChange={e=>setDate(e.target.value)} />
      )}
      <input className="input" type="time" value={start} onChange={e=>setStart(e.target.value)} />
      <input className="input" type="time" value={end} onChange={e=>setEnd(e.target.value)} />
      <input className="input" type="number" min={1} value={minStaff} onChange={e=>setMinStaff(+e.target.value)} />
      <button className="button" onClick={submit}>Add</button>
    </div>
  )
}