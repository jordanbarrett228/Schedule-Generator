# Electron Conversion Guide

## API Call Replacements

All `fetchWithAuth()` calls need to be replaced with the new `api` utility.

### Import Changes
```typescript
// OLD:
import { fetchWithAuth } from '../utils/fetchWithAuth'

// NEW:
import { api } from '../utils/api'
```

### Pattern Replacements

#### GET Requests
```typescript
// OLD:
const response = await fetchWithAuth('/api/employees')
const data = await response.json()

// NEW:
const data = await api.get('/api/employees')
```

#### POST Requests
```typescript
// OLD:
await fetchWithAuth('/api/employees', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'John', active: true })
})

// NEW:
await api.post('/api/employees', { name: 'John', active: true })
```

#### PUT Requests
```typescript
// OLD:
await fetchWithAuth('/api/settings/global', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})

// NEW:
await api.put('/api/settings/global', data)
```

#### DELETE Requests
```typescript
// OLD:
await fetchWithAuth(`/api/employees/${id}`, { method: 'DELETE' })

// NEW:
await api.delete(`/api/employees/${id}`)
```

## Files that Need Updates

- [x] frontend/src/App.tsx - Remove authentication
- [x] frontend/src/pages/DashboardView.tsx - Replace fetchWithAuth
- [x] frontend/src/pages/EmployeesView.tsx - Replace fetchWithAuth
- [ ] frontend/src/pages/StaffingPrefsView.tsx - Replace fetchWithAuth
- [ ] frontend/src/pages/SettingsView.tsx - Replace fetchWithAuth (if exists)
- [ ] frontend/src/components/EmployeeEditor.tsx - Replace fetchWithAuth
- [ ] frontend/src/components/SettingsPanel.tsx - Replace fetchWithAuth

## Backend Changes

- Created `backend/app/ipc_server.py` - Handles stdin/stdout IPC
- Created `backend/app/ipc_implementations.py` - Implementation functions without auth
- Updated `backend/app/db.py` - Added `set_data_directory()` for custom DB path
- Removed user authentication from all IPC implementations

## Running in Development

### Start Backend (IPC mode):
```bash
cd backend
python -m app.ipc_server --data-dir ./data
```

### Start Frontend:
```bash
cd frontend
npm run dev
```

### Start Electron:
```bash
npm run dev
```

## Building Portable Application

### 1. Build Frontend
```bash
cd frontend
npm run build
```

### 2. Install Electron Dependencies
```bash
npm install
```

### 3. Build Portable App
```bash
npm run build:portable
```

The portable application will be created in `dist-electron/`.
