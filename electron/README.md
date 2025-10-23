# Electron Application Files

## Files in this directory:

### main.js
The Electron main process. This file:
- Spawns the Python backend as a child process
- Creates the application window
- Handles IPC communication between frontend and Python
- Manages app lifecycle (startup, shutdown)

### preload.js
The IPC bridge that runs in the renderer process. This file:
- Exposes `window.electron.invoke()` to the frontend
- Provides secure IPC communication via contextBridge
- Isolates Node.js APIs from the renderer

### icon.ico (TODO - Create this file)
The application icon for Windows.

**To create:**
1. Use any icon editor or online tool (e.g., https://www.icoconverter.com/)
2. Create a 256x256 PNG image with your logo
3. Convert to .ico format
4. Save as `electron/icon.ico`

**Recommended design:**
- Simple, recognizable symbol
- Works well at small sizes (16x16, 32x32)
- High contrast
- Related to scheduling/calendar theme

## How it Works

```
┌─────────────────────────────────────────┐
│        Electron Main Process            │
│         (electron/main.js)              │
│                                         │
│  1. Spawns Python backend via spawn()  │
│  2. Creates BrowserWindow               │
│  3. Routes IPC ↔ Python stdin/stdout   │
└────────┬──────────────────┬─────────────┘
         │                  │
         │                  │ JSON messages
         ▼                  ▼
┌──────────────────┐  ┌────────────────────┐
│   Frontend       │  │  Python Backend    │
│   (React in      │  │  (ipc_server.py)   │
│   renderer)      │  │                    │
│                  │  │  - Reads stdin     │
│  Uses:           │  │  - Processes req   │
│  window.electron │  │  - Writes stdout   │
│  .invoke()       │  │  - OR-Tools solver │
└──────────────────┘  └────────────────────┘
```

## Development vs Production

### Development Mode
```bash
npm run dev
```
- Loads frontend from Vite dev server (http://localhost:5173)
- Opens DevTools automatically
- Uses local Python installation
- Hot reload for frontend changes

### Production Mode
```bash
npm run build
```
- Loads frontend from `frontend/dist/` (static files)
- No DevTools
- Uses bundled Python runtime from `python-runtime/` or `resources/`
- Single executable file

## Environment Variables

The main process checks `process.argv` for flags:
- `--dev`: Runs in development mode
- `--data-dir <path>`: Custom database directory

## Security

The app uses:
- `nodeIntegration: false` - Prevents direct Node.js access in renderer
- `contextIsolation: true` - Isolates renderer from main process
- `preload.js` - Only exposes specific, safe APIs to frontend

This prevents malicious frontend code from accessing system resources directly.

## Debugging

### Python Backend Issues:
```bash
# Test Python IPC server independently:
cd backend
python -m app.ipc_server --data-dir ./test_data

# Then manually type JSON requests:
{"id":1,"method":"GET","endpoint":"/api/employees"}
# Press Enter - should get JSON response
```

### Electron Issues:
- Check main process logs in terminal where you ran `npm start`
- Check renderer logs in DevTools (Ctrl+Shift+I in development)
- Look for IPC errors: "Python process not running", "Request timeout"

### IPC Communication Issues:
- Verify `pythonProcess` is running (check terminal output)
- Check for Python stderr output (errors)
- Ensure JSON requests are properly formatted
- Watch for timeout errors (increase timeout in main.js if needed)

## Performance

The IPC communication adds minimal overhead:
- Small requests (<1ms overhead)
- Large responses (schedule generation): ~same as HTTP
- No network stack, no TCP/IP
- Direct process pipes are very fast

## Limitations

- Python backend must be running for app to work
- If Python crashes, app needs restart
- Large data transfers (>100MB) might be slow via stdin/stdout
  (but unlikely for this app)

## Future Improvements

- [ ] Add loading indicator during Python startup
- [ ] Implement graceful Python restart on crash
- [ ] Add health check ping/pong between processes
- [ ] Cache initial data to speed up startup
- [ ] Implement background scheduling (schedule generation without blocking UI)
