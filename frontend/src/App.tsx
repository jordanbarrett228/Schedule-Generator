import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import DashboardView from './pages/DashboardView'
import EmployeesView from './pages/EmployeesView'
import SettingsView from './pages/SettingsView'
import StaffingPrefsView from './pages/StaffingPrefsView'
import LoginPage from './pages/LoginPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuth } from './context/AuthContext'
import './styles.css'

function AppShell() {
  const { logout } = useAuth()

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
        <button
          onClick={logout}
          className="button small"
          style={{ marginLeft: 'auto', marginRight: 12 }}
        >
          Logout
        </button>
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
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route for login */}
        <Route path="/login" element={<LoginPage />} />

        {/* All other routes require login */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
