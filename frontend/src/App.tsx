import { HashRouter, Routes, Route, NavLink } from 'react-router-dom'
import DashboardView from './pages/DashboardView'
import EmployeesView from './pages/EmployeesView'
import SettingsView from './pages/SettingsView'
import StaffingPrefsView from './pages/StaffingPrefsView'
import { ScheduleProvider, useSchedule } from './context/ScheduleContext'
import './styles.css'

function AppShell() {
  const { isGenerating, progress } = useSchedule()

  return (
    <div className="app-shell">
      <nav className="topnav">
        <div className="brand">Schedule Generator</div>
        <div className="links">
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/employees">Employees</NavLink>
          <NavLink to="/settings">Settings</NavLink>
          <NavLink to="/staffing-prefs">Staffing Prefs</NavLink>
        </div>
      </nav>
      {isGenerating && (
        <div style={{
          position: 'fixed',
          top: 50,
          right: 16,
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: 6,
          padding: '8px 12px',
          fontSize: '0.85em',
          color: '#666',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          <div style={{
            width: 12,
            height: 12,
            border: '2px solid #3b82f6',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <div>
            <div style={{ fontWeight: 500 }}>Generating schedule...</div>
            {progress.count > 0 && (
              <div style={{ fontSize: '0.9em', color: '#999' }}>
                {progress.count} solution{progress.count > 1 ? 's' : ''} • {progress.elapsed}s
              </div>
            )}
          </div>
        </div>
      )}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardView />} />
          <Route path="/employees" element={<EmployeesView />} />
          <Route path="/settings" element={<SettingsView />} />
          <Route path="/staffing-prefs" element={<StaffingPrefsView />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <HashRouter>
      <ScheduleProvider>
        <Routes>
          <Route path="/*" element={<AppShell />} />
        </Routes>
      </ScheduleProvider>
    </HashRouter>
  )
}
