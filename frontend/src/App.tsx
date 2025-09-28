import { useEffect, useState } from 'react'
import { EmployeeEditor, type Employee } from './components/EmployeeEditor'
import { SettingsPanel } from './components/SettingsPanel'

function App() {
  const [status, setStatus] = useState<string>('…')
  const [employees, setEmployees] = useState<Employee[]>([])
  const [newName, setNewName] = useState('')
  const [editing, setEditing] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(d => setStatus(d.status)).catch(() => setStatus('error'))
    refresh()
  }, [])
  
  async function quitApp() {
    await fetch('/api/shutdown', { method: 'POST' });
  }

  const refresh = () => {
    fetch('/api/employees').then(r => r.json()).then(setEmployees)
  }

  const add = async () => {
    if (!newName.trim()) return
    await fetch('/api/employees', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName, active: true })
    })
    setNewName('')
    refresh()
  }

  const remove = async (id: number) => {
    await fetch(`/api/employees/${id}`, { method: 'DELETE' })
    refresh()
  }

  const toggleActive = async (e: Employee) => {
    await fetch(`/api/employees/${e.id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ active: !e.active }) })
    refresh()
  }

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24, display:'grid', gap: 16 }}>
      <header style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h1>Schedule Generator</h1>
        <span>Backend: <b>{status}</b></span>
        <button onClick={quitApp}>Quit app</button>
      </header>
      
      <SettingsPanel />

      <section className="section">
        <h2>Employees</h2>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
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
                  <button className="button" style={{ marginLeft: 8 }} onClick={() => remove(e.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {editing!==null && <EmployeeEditor empId={editing} onClose={()=>{ setEditing(null); refresh(); }} />}
    </div>
  )
}

export default App