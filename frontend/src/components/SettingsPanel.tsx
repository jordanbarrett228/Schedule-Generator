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

const weekdays = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']


export function SettingsPanel() {
  const [gs, setGs] = useState<GlobalSettings | null>(null)
  const [bh, setBh] = useState<BusinessHours[]>([])
  const [loading, setLoading] = useState(true)

  async function load(){
    setLoading(true)
    const [g, rawBh] = await Promise.all([
      fetch('/api/settings/global').then(r=>r.json()),
      fetch('/api/settings/business_hours').then(r=>r.json()),
    ])
    setGs(g)

    // Use API-provided business hours directly. Backend is responsible for defaults.
    setBh(rawBh)
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
    </div>
  )
}