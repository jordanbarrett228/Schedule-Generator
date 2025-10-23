import { useEffect, useState, useRef } from 'react'
import { EmployeeEditor, type Employee } from '../components/EmployeeEditor'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { api } from '../utils/api'

export default function EmployeesView() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [newName, setNewName] = useState('')
  const [editing, setEditing] = useState<number | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<{ id: number; name: string } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

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

  const remove = (id: number, name: string) => {
    setConfirmDelete({ id, name })
  }

  const confirmRemove = async () => {
    if (!confirmDelete) return

    await api.delete(`/api/employees/${confirmDelete.id}`)
    setConfirmDelete(null)
    await refresh()

    // Restore focus to input after deletion
    inputRef.current?.focus()
  }

  const cancelRemove = () => {
    setConfirmDelete(null)
    // Restore focus to input when canceling
    inputRef.current?.focus()
  }

  const toggleActive = async (e: Employee) => {
    await api.put(`/api/employees/${e.id}`, { active: !e.active })
    await refresh()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      add()
    }
  }

  return (
    <section className="empViewSection">
      <h2>Employees</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, maxWidth: 'fit-content' }}>
        <input
          ref={inputRef}
          className="input"
          placeholder="Employee name"
          value={newName}
          onChange={e => setNewName(e.target.value)}
          onKeyDown={handleKeyDown}
        />
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

      {confirmDelete && (
        <ConfirmDialog
          title="Delete Employee"
          message={`Are you sure you'd like to delete employee "${confirmDelete.name}"?\n\nThis will permanently remove their constraints, time off, and locked shifts.`}
          onConfirm={confirmRemove}
          onCancel={cancelRemove}
        />
      )}
    </section>
  )
}