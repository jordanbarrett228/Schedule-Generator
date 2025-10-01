import { useEffect, useState } from 'react'
import { format12 } from '../lib/time';

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
  allow_split_shifts: boolean

  capable_opening: boolean
  open_not_before: string | null
  no_clopen: boolean
  clopen_next_day_not_before: string | null
  target_days_off: number | null
}

export type UnavailableBlock = { id: number; employee_id: number; weekday: number; start_time: string; end_time: string }
export type TimeOff = {
  id: number
  employee_id: number
  date: string
  all_day: boolean
  start_time?: string | null
  end_time?: string | null
  reason?: string
}
export type LockedShift = { id: number; employee_id: number; weekday: number; start_time: string; end_time: string; note?: string }

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
  const updateUnavail = async (id: number, weekday: number, start: string, end: string) => {
    const res = await fetch(`/api/unavailable/${id}`, {
      method:'PUT', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ weekday, start_time: start, end_time: end })
    })
    if (!res.ok) {
      const txt = await res.text()
      alert(`Failed to update: ${txt}`)
      return
    }
    const rec = await res.json()
    setUnavail(p => p.map(x => x.id === id ? { ...x, weekday: rec.weekday, start_time: rec.start_time, end_time: rec.end_time } : x))
  }

  const addTimeOff = async (date: string, all_day: boolean, start_time?: string|null, end_time?: string|null, reason?: string) => {
    const res = await resFetch(`/api/employees/${empId}/timeoff`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ employee_id: empId, date, all_day, start_time, end_time, reason })
    })
    const rec = await res.json()
    setTimeOff(p=>[...p, rec])
  }
  // small helper so we don't shadow res var name above
  function resFetch(input: RequestInfo | URL, init?: RequestInit) { return fetch(input, init) }

  const delTimeOff = async (id: number) => {
    await fetch(`/api/timeoff/${id}`, { method:'DELETE' })
    setTimeOff(p=>p.filter(x=>x.id!==id))
  }
  
  const addLocked = async (weekday: number, start_time: string, end_time: string, note: string) => {
    const res = await fetch(`/api/employees/${empId}/locked_shifts`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ employee_id: empId, weekday, start_time, end_time, note })
    })
    const rec = await res.json()
    setLocked(p=>[...p, rec])
  }

  const delLocked = async (id: number) => {
    await fetch(`/api/locked_shifts/${id}`, { method:'DELETE' })
    setLocked(p=>p.filter(x=>x.id!==id))
  }

  const updateLocked = async (id: number, weekday: number, start_time: string, end_time: string, note: string) => {
    if (!start_time || !end_time || start_time >= end_time) {
      alert('End time must be after start time.')
      return
    }
    const res = await fetch(`/api/employees/${empId}/locked_shifts/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weekday, start_time, end_time, note }),
    });
    if (!res.ok) {
      const t = await res.text()
      alert(`Failed to update: ${t}`)
      return
    }
    const rec = await res.json()
    setLocked(p =>
      p.map(x => x.id === id
        ? { ...x, weekday: rec.weekday, start_time: rec.start_time, end_time: rec.end_time, note: rec.note ?? '' }
        : x
      )
    )
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
              <label className="row" style={{gap:8}}>
                <input
                  type="checkbox"
                  checked={emp.capable_opening}
                  onChange={e=>setEmp({...emp, capable_opening: e.target.checked})}
                />
                Capable of opening
              </label>

              <div className="row" style={{gap:8}}>
                <div className="label">If NOT opening, earliest start</div>
                <input
                  className="input"
                  type="time"
                  value={emp.open_not_before ?? '07:00'}
                  onChange={e=>setEmp({...emp, open_not_before: e.target.value })}
                />
              </div>

              <label className="row" style={{gap:8}}>
                <input
                  type="checkbox"
                  checked={emp.no_clopen}
                  onChange={e=>setEmp({...emp, no_clopen: e.target.checked})}
                />
                No clopen (no opening next day after closing)
              </label>

              <div className="row" style={{gap:8}}>
                <div className="label">If closed yesterday, earliest next-day start</div>
                <input
                  className="input"
                  type="time"
                  value={emp.clopen_next_day_not_before ?? '09:00'}
                  onChange={e=>setEmp({...emp, clopen_next_day_not_before: e.target.value })}
                />
              </div>

              <label className="row" style={{gap:8}}>
                <input type="checkbox" checked={emp.allow_split_shifts}
                  onChange={e=>setEmp({...emp, allow_split_shifts: e.target.checked})} />
                Allow split shifts (max 2/day)
              </label>
              {/* <div>
                <div className="label">Max consecutive days (soft)</div>
                <input className="input" type="number" min={0} value={emp.max_consecutive_days ?? ''}
                  onChange={e=>setEmp({...emp, max_consecutive_days: e.target.value? +e.target.value : null})} />
              </div> */}
            </div>

            <div className="grid" style={{gap:8}}>
              <strong>Unavailable (weekly)</strong>
              <UnavailableEditor
                rows={unavail}
                onAdd={addUnavail}
                onDelete={delUnavail}
                onUpdate={updateUnavail}
              />
            </div>

            <div className="grid" style={{gap:8}}>
              <strong>Time Off (dates)</strong>
              <TimeOffEditor rows={timeOff} onAdd={addTimeOff} onDelete={delTimeOff} />
            </div>

            <div className="grid" style={{gap:8}}>
              <strong>Fixed Shifts (locked)</strong>
              <LockedEditor rows={locked} onAdd={addLocked} onDelete={delLocked} onUpdate={updateLocked} />
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
              <div>
                <div className="label">Target days off/week (0–7)</div>
                <input
                  className="input"
                  type="number"
                  min={0}
                  max={7}
                  value={emp.target_days_off ?? ''}
                  onChange={e=>setEmp({...emp, target_days_off: e.target.value ? +e.target.value : null})}
                />
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

function UnavailableEditor({
  rows,
  onAdd,
  onDelete,
  onUpdate
}:{
  rows:UnavailableBlock[],
  onAdd:(weekday:number,start:string,end:string)=>void,
  onDelete:(id:number)=>void,
  onUpdate:(id:number, weekday:number, start:string, end:string)=>void
}){
  const [weekday, setWeekday] = useState(0)
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('17:00')

  // inline edit state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editDay, setEditDay] = useState<number>(0)
  const [editStart, setEditStart] = useState<string>('09:00')
  const [editEnd, setEditEnd] = useState<string>('17:00')

  const beginEdit = (r: UnavailableBlock) => {
    setEditingId(r.id)
    setEditDay(r.weekday)
    setEditStart(r.start_time)
    setEditEnd(r.end_time)
  }
  const cancelEdit = () => {
    setEditingId(null)
  }
  const saveEdit = async () => {
    if (editingId == null) return
    if (!editStart || !editEnd || editStart >= editEnd) {
      alert('End time must be after start time.')
      return
    }
    await onUpdate(editingId, editDay, editStart, editEnd)
    setEditingId(null)
  }

  // shared cell styles so edit/display rows match widths
  const tdDayStyle   = { width: 120 } as const
  const tdTimeStyle  = { width: 140 } as const
  const tdActStyle   = { width: 200, whiteSpace: 'nowrap' } as const
  const inputFull    = { width: '100%', boxSizing: 'border-box' } as const
  const selectFull   = { width: '100%' } as const

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

      <table className="table" style={{ tableLayout: 'fixed', width: '100%' }}>
        {/* Fix column widths so nothing shifts in edit mode */}
        <colgroup>
          <col style={tdDayStyle} />
          <col style={tdTimeStyle} />
          <col style={tdTimeStyle} />
          <col style={tdActStyle} />
        </colgroup>
        <thead>
          <tr>
            <th>Day</th>
            <th>Start</th>
            <th>End</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r=> {
            const isEditing = editingId === r.id
            if (isEditing) {
              return (
                <tr key={r.id}>
                  <td style={tdDayStyle}>
                    <select style={selectFull} value={editDay} onChange={e=>setEditDay(+e.target.value)}>
                      {weekdays.map((w,i)=>(<option key={i} value={i}>{w}</option>))}
                    </select>
                  </td>
                  <td style={tdTimeStyle}>
                    <input style={inputFull} className="input" type="time" value={editStart} onChange={e=>setEditStart(e.target.value)} />
                  </td>
                  <td style={tdTimeStyle}>
                    <input style={inputFull} className="input" type="time" value={editEnd} onChange={e=>setEditEnd(e.target.value)} />
                  </td>
                  <td style={tdActStyle}>
                    <div style={{display:'flex', gap:8, justifyContent:'flex-end'}}>
                      <button className="button primary" onClick={saveEdit}>Save</button>
                      <button className="button" onClick={cancelEdit}>Cancel</button>
                    </div>
                  </td>
                </tr>
              )
            }
            return (
              <tr key={r.id}>
                <td style={tdDayStyle}>{weekdays[r.weekday]}</td>
                <td style={tdTimeStyle}>{format12(r.start_time)}</td>
                <td style={tdTimeStyle}>{format12(r.end_time)}</td>
                <td style={tdActStyle}>
                  <div style={{display:'flex', gap:8, justifyContent:'flex-end'}}>
                    <button className="button" onClick={()=>beginEdit(r)}>Edit</button>
                    <button className="button" onClick={()=>onDelete(r.id)}>Delete</button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}


function TimeOffEditor({
  rows, onAdd, onDelete
}:{
  rows:TimeOff[],
  onAdd:(date:string, all_day:boolean, start?:string|null, end?:string|null, reason?:string)=>void,
  onDelete:(id:number)=>void
}){
  const [date, setDate] = useState('')
  const [allDay, setAllDay] = useState(true)
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('17:00')
  const [reason, setReason] = useState('')

  return (
    <div className="grid" style={{gap:8}}>
      <div className="row" style={{gap:8, flexWrap:'wrap'}}>
        <input className="input" type="date" value={date} onChange={e=>setDate(e.target.value)} />
        <label className="row" style={{gap:6}}>
          <input type="checkbox" checked={allDay} onChange={e=>setAllDay(e.target.checked)} />
          All day
        </label>
        {!allDay && (
          <>
            <input className="input" type="time" value={start} onChange={e=>setStart(e.target.value)} />
            <input className="input" type="time" value={end} onChange={e=>setEnd(e.target.value)} />
          </>
        )}
        <input className="input" placeholder="Reason (optional)" value={reason} onChange={e=>setReason(e.target.value)} />
        <button className="button" onClick={()=>{
          if(!date) return
          onAdd(date, allDay, allDay ? null : start, allDay ? null : end, reason)
        }}>Add</button>
      </div>
      <table className="table">
        <thead><tr><th>Date</th><th>Time</th><th>Reason</th><th></th></tr></thead>
        <tbody>
          {rows.map(r=> (
            <tr key={r.id}>
              <td>{r.date}</td>
              <td>{r.all_day ? 'All day' : `${r.start_time}–${r.end_time}`}</td>
              <td>{r.reason ?? ''}</td>
              <td><button className="button" onClick={()=>onDelete(r.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LockedEditor({
  rows,
  onAdd,
  onDelete,
  onUpdate
}:{
  rows:LockedShift[],
  onAdd:(weekday:number,start:string,end:string,note:string)=>void,
  onDelete:(id:number)=>void,
  onUpdate:(id:number, weekday:number, start:string, end:string, note:string)=>void
}) {
  const [weekday, setWeekday] = useState(0)
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('17:00')
  const [note, setNote] = useState('')

  // inline edit state
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editDay, setEditDay] = useState<number>(0)
  const [editStart, setEditStart] = useState<string>('09:00')
  const [editEnd, setEditEnd] = useState<string>('17:00')
  const [editNote, setEditNote] = useState<string>('')

  const beginEdit = (r: LockedShift) => {
    setEditingId(r.id)
    setEditDay(r.weekday)
    setEditStart(r.start_time)
    setEditEnd(r.end_time)
    setEditNote(r.note ?? '')
  }
  const cancelEdit = () => {
    setEditingId(null)
  }
  const saveEdit = async () => {
    if (editingId == null) return
    await onUpdate(editingId, editDay, editStart, editEnd, editNote)
    setEditingId(null)
  }

  // helpers for duration + totals
  const toMin = (hhmm: string) => {
    const [h, m] = hhmm.split(':').map(n => parseInt(n || '0', 10))
    return (h * 60) + m
  }
  const durHours = (s: string, e: string) => Math.max(0, toMin(e) - toMin(s)) / 60
  const totalMinutes = rows.reduce((acc, r) => acc + Math.max(0, toMin(r.end_time) - toMin(r.start_time)), 0)
  const totalHours = (totalMinutes / 60).toFixed(2)

  // fixed widths so columns don’t shift in edit mode
  const tdDayStyle  = { width: 120 } as const
  const tdTimeStyle = { width: 260 } as const
  const tdNoteStyle = { width: 1 } as const  // flexible
  const tdActStyle  = { width: 200, whiteSpace: 'nowrap' } as const
  const inputFull   = { width: '100%', boxSizing: 'border-box' } as const
  const selectFull  = { width: '100%' } as const

  return (
    <div className="grid" style={{gap:8}}>
      <div className="row" style={{gap:8, flexWrap:'wrap'}}>
        <select value={weekday} onChange={e=>setWeekday(+e.target.value)}>
          {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((w,i)=>(<option key={i} value={i}>{w}</option>))}
        </select>
        <input className="input" type="time" value={start} onChange={e=>setStart(e.target.value)} />
        <input className="input" type="time" value={end} onChange={e=>setEnd(e.target.value)} />
        <input className="input" placeholder="Note (optional)" value={note} onChange={e=>setNote(e.target.value)} />
        <button className="button" onClick={()=> onAdd(weekday,start,end,note)}>Add</button>
      </div>

      <div className="muted" style={{marginTop:4}}>
        <strong>Total locked hours this week:</strong> {totalHours} h
      </div>

      <table className="table" style={{ tableLayout: 'fixed', width: '100%' }}>
        <colgroup>
          <col style={tdDayStyle} />
          <col style={tdTimeStyle} />
          <col style={tdNoteStyle} />
          <col style={tdActStyle} />
        </colgroup>
        <thead>
          <tr>
            <th>Weekday</th>
            <th>Time (length)</th>
            <th>Note</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => {
            const isEditing = editingId === r.id

            if (isEditing) {
              const lenHrs = durHours(editStart, editEnd).toFixed(2)
              return (
                <tr key={r.id}>
                  <td style={tdDayStyle}>
                    <select style={selectFull} value={editDay} onChange={e=>setEditDay(+e.target.value)}>
                      {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((w,i)=>(<option key={i} value={i}>{w}</option>))}
                    </select>
                  </td>
                  <td style={tdTimeStyle}>
                    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, alignItems:'center'}}>
                      <input style={inputFull} className="input" type="time" value={editStart} onChange={e=>setEditStart(e.target.value)} />
                      <input style={inputFull} className="input" type="time" value={editEnd} onChange={e=>setEditEnd(e.target.value)} />
                    </div>
                    <div className="muted" style={{marginTop:4}}>( {lenHrs} h )</div>
                  </td>
                  <td style={tdNoteStyle}>
                    <input style={inputFull} className="input" value={editNote} onChange={e=>setEditNote(e.target.value)} placeholder="Note (optional)" />
                  </td>
                  <td style={tdActStyle}>
                    <div style={{display:'flex', gap:8, justifyContent:'flex-end'}}>
                      <button className="button primary" onClick={saveEdit}>Save</button>
                      <button className="button" onClick={cancelEdit}>Cancel</button>
                    </div>
                  </td>
                </tr>
              )
            }

            const lenHrs = durHours(r.start_time, r.end_time).toFixed(2)
            return (
              <tr key={r.id}>
                <td style={tdDayStyle}>{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][r.weekday]}</td>
                <td style={tdTimeStyle}>
                  {format12(r.start_time)} – {format12(r.end_time)}{' '}
                  <span className="muted">({lenHrs} h)</span>
                </td>
                <td style={tdNoteStyle}>{r.note ?? ''}</td>
                <td style={tdActStyle}>
                  <div style={{display:'flex', gap:8, justifyContent:'flex-end'}}>
                    <button className="button" onClick={()=>beginEdit(r)}>Edit</button>
                    <button className="button" onClick={()=>onDelete(r.id)}>Delete</button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
