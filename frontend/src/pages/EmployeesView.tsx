import { useEffect, useState } from 'react'
import { EmployeeEditor, type Employee } from '../components/EmployeeEditor'
import { api } from '../utils/api'

export default function EmployeesView() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [newName, setNewName] = useState('')
  const [editing, setEditing] = useState<number | null>(null)

  const refresh = async () => {
    const data = await api.get('/api/employees')
    setEmployees(data)
  }
  useEffect(() => { refresh() }, [])

  const add = async () => {
    if (!newName.trim()) return
    await api.post('/api/employees', { name: newName, active: true })
    setNewName('')
    await refresh()
  }

  const remove = async (id: number, name: string) => {
    const ok = window.confirm(
    `Are you sure you'd like to delete employee "${name}"?\n\nThis will permanently remove their constraints, time off, and locked shifts.`
    )
    if(!ok) return

    await api.delete(`/api/employees/${id}`)
    await refresh()
  }

  const toggleActive = async (e: Employee) => {
    await api.put(`/api/employees/${e.id}`, { active: !e.active })
    await refresh()
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      add()
    }
  }

  return (
    <section className="empViewSection">
      <h2>Employees</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, maxWidth: 'fit-content' }}>
        <input className="input" placeholder="Employee name" value={newName} onChange={e => setNewName(e.target.value)} onKeyPress={handleKeyPress} />
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