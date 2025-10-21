import { useEffect, useState, useRef } from 'react'
import { fetchWithAuth } from '../utils/fetchWithAuth'

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
      fetchWithAuth('/api/settings/global').then(r=>r.json()),
      fetchWithAuth('/api/settings/business_hours').then(r=>r.json()),
    ])
    setGs(g)

    // Use API-provided business hours directly. Backend is responsible for defaults.
    setBh(rawBh)
    setLoading(false)
  }
  useEffect(()=>{ load() }, [])

  const saveGlobal = async () => {
    if (!gs) return
    await fetchWithAuth('/api/settings/global', { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(gs) })
  }

  const saveBusinessHours = async () => {
    // send array without ids is okay; backend upserts by weekday
    const payload = bh.map(({weekday, open_time, close_time}) => ({weekday, open_time, close_time}))
    await fetchWithAuth('/api/settings/business_hours', { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
    await load()
  }

  const fileRef = useRef<HTMLInputElement>(null)
  const backupData = async () => {
    try {
        const res = await fetchWithAuth('/api/admin/backup')
        if (!res.ok) {
        const t = await res.text()
        alert(`Backup failed: ${t || res.statusText}`)
        return
        }
        const data = await res.json()
        const stamp = new Date().toISOString().slice(0, 10) // YYYY-MM-DD
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `schedule-backup-${stamp}.json`
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
    } catch (e) {
        alert('Backup failed. See console for details.')
        console.error(e)
    }
    }

const triggerRestore = () => fileRef.current?.click()

const onRestoreFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0]
  if (!file) return
  try {
    const text = await file.text()
    const payload = JSON.parse(text) as Record<string, unknown>
    const ok = window.confirm(
      'Restore will replace current data with the backup contents. Continue?'
    )
    if (!ok) return

    const res = await fetchWithAuth('/api/admin/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const t = await res.text()
      alert(`Restore failed: ${t || res.statusText}`)
      return
    }
    alert('Restore complete.')
    // optional: refresh the page or refetch settings/employees here
    // location.reload()
  } catch (err) {
    alert('Invalid or unreadable backup file.')
    console.error(err)
  } finally {
    // reset the file input so choosing the same file again will fire onChange
    e.target.value = ''
  }
}
  if (loading || !gs) return <div className="section">Loading settings…</div>

  return (
    <div>
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
      
      <div className="panel" style={{ marginTop: 16 }}>
        <h3 style={{ marginTop: 0 }}>Backup &amp; Restore</h3>
        <input
            ref={fileRef}
            type="file"
            accept="application/json"
            style={{ display: 'none' }}
            onChange={onRestoreFile}
        />
        <div className="row" style={{ gap: 12, flexWrap: 'wrap' }}>
            <button className="button danger-soft" onClick={backupData}>
            Backup data
            </button>
            <button className="button danger-soft" onClick={triggerRestore}>
            Restore data from backup
            </button>
        </div>
      </div>
    </div>
  )
}