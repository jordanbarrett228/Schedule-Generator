const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;
let requestId = 0;
let pendingRequests = new Map();

// Get the app data directory for storing databases
function getAppDataPath() {
  const userDataPath = app.getPath('userData');
  const dataDir = path.join(userDataPath, 'data');

  // Create data directory if it doesn't exist
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  return dataDir;
}

// Start Python backend process
function startPythonBackend() {
  const isDev = process.argv.includes('--dev');
  const dataPath = getAppDataPath();

  let pythonCmd, pythonArgs;

  if (isDev) {
    // Development mode: use local Python
    pythonCmd = 'python';
    pythonArgs = [
      '-m',
      'app.ipc_server',
      '--data-dir',
      dataPath
    ];
  } else {
    // Production mode: use bundled Python executable
    pythonCmd = path.join(process.resourcesPath, 'schedule-backend', 'schedule-backend.exe');
    pythonArgs = [
      '--data-dir',
      dataPath
    ];
  }

  console.log('Starting Python backend:', pythonCmd, pythonArgs);

  const spawnOptions = isDev ? {
    cwd: path.join(__dirname, '..', 'backend')
  } : {};

  pythonProcess = spawn(pythonCmd, pythonArgs, spawnOptions);

  // Handle Python stdout (responses)
  pythonProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n');

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const response = JSON.parse(line);

        if (response.id !== undefined && pendingRequests.has(response.id)) {
          const { resolve, reject } = pendingRequests.get(response.id);
          pendingRequests.delete(response.id);

          if (response.error) {
            reject(new Error(response.error));
          } else {
            resolve(response.data);
          }
        }
      } catch (err) {
        console.error('Failed to parse Python response:', line, err);
      }
    }
  });

  // Handle Python stderr (logs/errors)
  pythonProcess.stderr.on('data', (data) => {
    console.error('Python stderr:', data.toString());
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python process:', err);
    pythonProcess = null;
  });
}

// Send request to Python backend
function sendToPython(method, endpoint, data = null) {
  return new Promise((resolve, reject) => {
    if (!pythonProcess) {
      return reject(new Error('Python process not running'));
    }

    const id = requestId++;
    const request = {
      id,
      method,
      endpoint,
      data
    };

    pendingRequests.set(id, { resolve, reject });

    // Send request to Python via stdin
    pythonProcess.stdin.write(JSON.stringify(request) + '\n');

    // Timeout after 60 seconds (for long-running solver operations)
    setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id);
        reject(new Error('Request timeout'));
      }
    }, 60000);
  });
}

// Create the main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'icon.ico')
  });

  // Load the frontend - ALWAYS from local files (no HTTP/networking)
  const isDev = process.argv.includes('--dev');

  // Always load from built frontend files
  mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));

  // Open DevTools in dev mode
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC handlers - must be registered before app.ready but after module load
ipcMain.handle('api-request', async (event, { method, endpoint, data }) => {
  try {
    const result = await sendToPython(method, endpoint, data);
    return { success: true, data: result };
  } catch (error) {
    console.error('API request failed:', error);
    return { success: false, error: error.message };
  }
});

// App lifecycle
app.whenReady().then(() => {
  startPythonBackend();

  // Give Python a moment to start up
  setTimeout(() => {
    createWindow();
  }, 1000);
});

app.on('window-all-closed', () => {
  // Kill Python process
  if (pythonProcess) {
    pythonProcess.kill();
  }
  app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Cleanup on exit
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
