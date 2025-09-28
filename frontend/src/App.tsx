import { useEffect, useState } from 'react'


type Employee = {
  id: number
  name: string
  active: boolean
}


function App() {
  const [status, setStatus] = useState<string>('…')
  const [employees, setEmployees] = useState<Employee[]>([])
  const [newName, setNewName] = useState('')


  useEffect(() => {
  fetch('/api/health').then(r => r.json()).then(d => setStatus(d.status)).catch(() => setStatus('error'))
  refresh()
  }, [])


  const refresh = () => {
  fetch('/api/employees').then(r => r.json()).then(setEmployees)
}

async function quitApp() {
  await fetch('/api/shutdown', { method: 'POST' });
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


return (
  <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24 }}>
    <h1>Schedule Generator</h1>
    <button onClick={quitApp}>Quit app</button>
    <p>Backend status: <b>{status}</b></p>


    <h2>Employees</h2>
    <div style={{ display: 'flex', gap: 8 }}>
      <input
        placeholder="Employee name"
        value={newName}
        onChange={e => setNewName(e.target.value)}
      />
    <button onClick={add}>Add</button>
    </div>

    <ul>
      {employees.map(e => (
        <li key={e.id}>
          {e.name} {e.active ? '' : '(inactive)'}
          <button style={{ marginLeft: 8 }} onClick={() => remove(e.id)}>Delete</button>
        </li>
      ))}
    </ul>
  </div>
  )
}

export default App