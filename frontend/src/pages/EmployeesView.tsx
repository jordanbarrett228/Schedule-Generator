import { useEffect, useState } from 'react'
import { EmployeeEditor, type Employee } from '../components/EmployeeEditor'

export default function EmployeesView() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [newName, setNewName] = useState('')
  const [editing, setEditing] = useState<number | null>(null)

  const refresh = () => {
    fetch('/api/employees').then(r => r.json()).then(setEmployees)
  }
  useEffect(() => { refresh() }, [])

  const add = async () => {
    if (!newName.trim()) return
    await fetch('/api/employees', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName, active: true })
    })
    setNewName('')
    refresh()
  }

  const remove = async (id: number, name: string) => {
    const ok = window.confirm(
    `Are you sure you'd like to delete employee "${name}"?\n\nThis will permanently remove their constraints, time off, and locked shifts.`
    )
    if(!ok) return

    await fetch(`/api/employees/${id}`, { method: 'DELETE' })
    refresh()
  }

  const toggleActive = async (e: Employee) => {
    await fetch(`/api/employees/${e.id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ active: !e.active }) })
    refresh()
  }

  return (
    <section className="empViewSection">
      <h2>Employees</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, maxWidth: 'fit-content' }}>
        <input className="input" placeholder="Employee name" value={newName} onChange={e => setNewName(e.target.value)} />
        <button className="button" onClick={add}>Add</button>
      </div>
      <table className="table">
        <thead><tr><th>Name</th><th>Include</th><th></th></tr></thead>
        <tbody>
          {employees.map(e => (
            <tr key={e.id}>
              <td>{e.name}</td>
              <td>
                <label style={{display:'flex', alignItems:'center', gap:6}}>
                  <input type="checkbox" checked={e.active} onChange={()=>toggleActive(e)} /> include in generation
                </label>
              </td>
              <td style={{textAlign:'right'}}>
                <button className="button" onClick={()=>setEditing(e.id)}>Edit</button>
                <button className="button" style={{ marginLeft: 8 }} onClick={() => remove(e.id, e.name)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {editing!==null && <EmployeeEditor empId={editing} onClose={()=>{ setEditing(null); refresh(); }} />}
    </section>
  )
}