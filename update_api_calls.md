# API Update Script

## Manual Updates Needed

### EmployeeEditor.tsx
Replace import:
- `import { fetchWithAuth } from '../utils/fetchWithAuth';` 
- WITH: `import { api } from '../utils/api';`

Replace all patterns:
- `fetchWithAuth('/api/employees').then(r=>r.json())` → `api.get('/api/employees')`
- `fetchWithAuth('/api/employees/${empId}/unavailable').then(r=>r.json())` → `api.get('/api/employees/${empId}/unavailable')`
- `fetchWithAuth('/api/employees/${empId}/timeoff').then(r=>r.json())` → `api.get('/api/employees/${empId}/timeoff')`
- `fetchWithAuth('/api/employees/${empId}/locked_shifts').then(r=>r.json())` → `api.get('/api/employees/${empId}/locked_shifts')`
- `fetchWithAuth(url, {method:'PUT', headers:{...}, body:JSON.stringify(data)})` → `api.put(url, data)`
- `fetchWithAuth(url, {method:'POST', headers:{...}, body:JSON.stringify(data)})` → `api.post(url, data)`
- `fetchWithAuth(url, {method:'DELETE'})` → `api.delete(url)`

### SettingsPanel.tsx
Same pattern as above.

