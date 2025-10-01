import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import DashboardView from './pages/DashboardView.tsx'
import EmployeesView from './pages/EmployeesView.tsx'
import SettingsView from './pages/SettingsView.tsx'
import StaffingPrefsView from './pages/StaffingPrefsView'
import './styles.css'

export default function App() {
  return (
    <BrowserRouter>
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
        <main className="content">
          <Routes>
            <Route path="/" element={<DashboardView />} />
            <Route path="/employees" element={<EmployeesView />} />
            <Route path="/settings" element={<SettingsView />} />
            <Route path="/staffing-prefs" element={<StaffingPrefsView />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}