import { useEffect, useState } from 'react'

export type Employee = {
  id: number
  name: string
  active: boolean
  min_hours_week: number
  max_hours_week: number
  min_shift_hours: number
  max_shift_hours: number
  preferred_hours: number | null
  prefer_opening: boolean
  prefer_mid: boolean
  prefer_closing: boolean
  max_consecutive_days: number | null
}

export type UnavailableBlock = { id: number; employee_id: number; weekday: number; start_time: string; end_time: string }
export type TimeOff = { id: number; employee_id: number; start_date: string; end_date: string; reason?: string }
export type LockedShift = { id: number; employee_id: number; date: string; start_time: string; end_time: string; note?: string }

const weekdays = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

export function EmployeeEditor({ empId, onClose }: { empId: number, onClose: () => void }) {
  const [emp, setEmp] = useState<Employee | null>(null)
  const [unavail, setUnavail] = useState<UnavailableBlock[]>([])
  const [timeOff, setTimeOff] = useState<TimeOff[]>([])
  const [locked, setLocked] = useState<LockedShift[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const [e, u, t, l] = await Promise.all([
      fetch(`/api/employees`).then(r=>r.json()).then((arr: Employee[])=>arr.find(x=>x.id===empId)),
      fetch(`/api/employees/${empId}/unavailable`).then(r=>r.json()),
      fetch(`/api/employees/${empId}/timeoff`).then(r=>r.json()),
      fetch(`/api/employees/${empId}/locked_shifts`).then(r=>r.json()),
    ])
    if (e) setEmp(e)
    setUnavail(u)
    setTimeOff(t)
    setLocked(l)
    setLoading(false)
  }

  useEffect(()=>{ load() }, [empId])

  const saveEmp = async () => {
    if (!emp) return
    await fetch(`/api/employees/${emp.id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(emp)
    })
    onClose()
  }

  const addUnavail = async (weekday: number, start: string, end: string) => {
    const res = await fetch(`/api/employees/${empId}/unavailable`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ employee_id: empId, weekday, start_time: start, end_time: end })
    })
    const rec = await res.json()
    setUnavail(p=>[...p, rec])
  }
  const delUnavail = async (id: number) => {
    await fetch(`/api/unavailable/${id}`, { method:'DELETE' })
    setUnavail(p=>p.filter(x=>x.id!==id))
  }

  const addTimeOff = async (start_date: string, end_date: string, reason: string) => {
    const res = await fetch(`/api/employees/${empId}/timeoff`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ employee_id: empId, start_date, end_date, reason })
    })
    const rec = await res.json()
    setTimeOff(p=>[...p, rec])
  }
  const delTimeOff = async (id: number) => {
    await fetch(`/api/timeoff/${id}`, { method:'DELETE' })
    setTimeOff(p=>p.filter(x=>x.id!==id))
  }

  const addLocked = async (date: string, start_time: string, end_time: string, note: string) => {
    const res = await fetch(`/api/employees/${empId}/locked_shifts`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ employee_id: empId, date, start_time, end_time, note })
    })
    const rec = await res.json()
    setLocked(p=>[...p, rec])
  }
  const delLocked = async (id: number) => {
    await fetch(`/api/locked_shifts/${id}`, { method:'DELETE' })
    setLocked(p=>p.filter(x=>x.id!==id))
  }

  if (loading || !emp) return (
    <div className="modal-backdrop"><div className="modal"><header><h3>Loading…</h3><button className="button" onClick={onClose}>Close</button></header></div></div>
  )

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <header>
          <h3>Edit: {emp.name}</h3>
          <div className="row">
            <button className="button" onClick={onClose}>Close</button>
            <button className="button primary" onClick={saveEmp}>Save</button>
          </div>
        </header>

        <div className="grid" style={{gap:16}}>
          <div className="section grid" style={{gap:12}}>
            <div className="row" style={{justifyContent:'space-between'}}>
              <strong>Hard Constraints</strong>
              <label className="row" style={{gap:8}}>
                <input type="checkbox" checked={emp.active} onChange={e=>setEmp({...emp, active:e.target.checked})} /> Include in generation
              </label>
            </div>
            <div className="row" style={{gap:12, flexWrap:'wrap'}}>
              <div>
                <div className="label">Min hours/week</div>
                <input className="input" type="number" step="0.5" value={emp.min_hours_week}
                  onChange={e=>setEmp({...emp, min_hours_week: +e.target.value})} />
              </div>
              <div>
                <div className="label">Max hours/week</div>
                <input className="input" type="number" step="0.5" value={emp.max_hours_week}
                  onChange={e=>setEmp({...emp, max_hours_week: +e.target.value})} />
              </div>
              <div>
                <div className="label">Min hours/shift</div>
                <input className="input" type="number" step="0.5" value={emp.min_shift_hours}
                  onChange={e=>setEmp({...emp, min_shift_hours: +e.target.value})} />
              </div>
              <div>
                <div className="label">Max hours/shift</div>
                <input className="input" type="number" step="0.5" value={emp.max_shift_hours}
                  onChange={e=>setEmp({...emp, max_shift_hours: +e.target.value})} />
              </div>
              <div>
                <div className="label">Max consecutive days (soft)</div>
                <input className="input" type="number" min={0} value={emp.max_consecutive_days ?? ''}
                  onChange={e=>setEmp({...emp, max_consecutive_days: e.target.value? +e.target.value : null})} />
              </div>
            </div>
            
            <div className="grid" style={{gap:8}}>
              <strong>Unavailable (weekly)</strong>
              <UnavailableEditor rows={unavail} onAdd={addUnavail} onDelete={delUnavail} />
            </div>

            <div className="grid" style={{gap:8}}>
              <strong>Time Off (dates)</strong>
              <TimeOffEditor rows={timeOff} onAdd={addTimeOff} onDelete={delTimeOff} />
            </div>

            <div className="grid" style={{gap:8}}>
              <strong>Fixed Shifts (locked)</strong>
              <LockedEditor rows={locked} onAdd={addLocked} onDelete={delLocked} />
            </div>
          </div>

          <div className="section grid" style={{gap:12}}>
            <strong>Soft Preferences</strong>
            <div className="row" style={{gap:12, flexWrap:'wrap'}}>
              <div>
                <div className="label">Target hours/week</div>
                <input className="input" type="number" step="0.5" value={emp.preferred_hours ?? ''}
                  onChange={e=>setEmp({...emp, preferred_hours: e.target.value? +e.target.value : null})} />
              </div>
              <div className="row" style={{gap:16}}>
                <label className="row" style={{gap:6}}><input type="checkbox" checked={emp.prefer_opening} onChange={e=>setEmp({...emp, prefer_opening:e.target.checked})}/> Opening</label>
                <label className="row" style={{gap:6}}><input type="checkbox" checked={emp.prefer_mid} onChange={e=>setEmp({...emp, prefer_mid:e.target.checked})}/> Mid</label>
                <label className="row" style={{gap:6}}><input type="checkbox" checked={emp.prefer_closing} onChange={e=>setEmp({...emp, prefer_closing:e.target.checked})}/> Closing</label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function UnavailableEditor({ rows, onAdd, onDelete }:{ rows:UnavailableBlock[], onAdd:(weekday:number,start:string,end:string)=>void, onDelete:(id:number)=>void }){
  const [weekday, setWeekday] = useState(0)
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('17:00')
  return (
    <div className="grid" style={{gap:8}}>
      <div className="row" style={{gap:8, flexWrap:'wrap'}}>
        <select value={weekday} onChange={e=>setWeekday(+e.target.value)}>
          {weekdays.map((w,i)=>(<option key={i} value={i}>{w}</option>))}
        </select>
        <input className="input" type="time" value={start} onChange={e=>setStart(e.target.value)} />
        <input className="input" type="time" value={end} onChange={e=>setEnd(e.target.value)} />
        <button className="button" onClick={()=>onAdd(weekday,start,end)}>Add</button>
      </div>
      <table className="table">
        <thead><tr><th>Day</th><th>Start</th><th>End</th><th></th></tr></thead>
        <tbody>
          {rows.map(r=> (
            <tr key={r.id}>
              <td>{weekdays[r.weekday]}</td>
              <td>{r.start_time}</td>
              <td>{r.end_time}</td>
              <td><button className="button" onClick={()=>onDelete(r.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TimeOffEditor({ rows, onAdd, onDelete }:{ rows:TimeOff[], onAdd:(start:string,end:string,reason:string)=>void, onDelete:(id:number)=>void }){
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [reason, setReason] = useState('')
  return (
    <div className="grid" style={{gap:8}}>
      <div className="row" style={{gap:8, flexWrap:'wrap'}}>
        <input className="input" type="date" value={start} onChange={e=>setStart(e.target.value)} />
        <input className="input" type="date" value={end} onChange={e=>setEnd(e.target.value)} />
        <input className="input" placeholder="Reason (optional)" value={reason} onChange={e=>setReason(e.target.value)} />
        <button className="button" onClick={()=>{ if(start&&end) onAdd(start,end,reason); }}>Add</button>
      </div>
      <table className="table">
        <thead><tr><th>Start</th><th>End</th><th>Reason</th><th></th></tr></thead>
        <tbody>
          {rows.map(r=> (
            <tr key={r.id}>
              <td>{r.start_date}</td>
              <td>{r.end_date}</td>
              <td>{r.reason ?? ''}</td>
              <td><button className="button" onClick={()=>onDelete(r.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LockedEditor({ rows, onAdd, onDelete }:{ rows:LockedShift[], onAdd:(date:string,start:string,end:string,note:string)=>void, onDelete:(id:number)=>void }){
  const [date, setDate] = useState('')
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('17:00')
  const [note, setNote] = useState('')
  return (
    <div className="grid" style={{gap:8}}>
      <div className="row" style={{gap:8, flexWrap:'wrap'}}>
        <input className="input" type="date" value={date} onChange={e=>setDate(e.target.value)} />
        <input className="input" type="time" value={start} onChange={e=>setStart(e.target.value)} />
        <input className="input" type="time" value={end} onChange={e=>setEnd(e.target.value)} />
        <input className="input" placeholder="Note (optional)" value={note} onChange={e=>setNote(e.target.value)} />
        <button className="button" onClick={()=>{ if(date) onAdd(date,start,end,note); }}>Add</button>
      </div>
      <table className="table">
        <thead><tr><th>Date</th><th>Start</th><th>End</th><th>Note</th><th></th></tr></thead>
        <tbody>
          {rows.map(r=> (
            <tr key={r.id}>
              <td>{r.date}</td>
              <td>{r.start_time}</td>
              <td>{r.end_time}</td>
              <td>{r.note ?? ''}</td>
              <td><button className="button" onClick={()=>onDelete(r.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}