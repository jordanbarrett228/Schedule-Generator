const { contextBridge, ipcRenderer } = require('electron');

// Expose IPC API to the frontend
contextBridge.exposeInMainWorld('electron', {
  // Generic API request handler
  invoke: async (method, endpoint, data) => {
    const result = await ipcRenderer.invoke('api-request', { method, endpoint, data });

    if (!result.success) {
      throw new Error(result.error);
    }

    return result.data;
  },

  // Subscribe to solver progress events
  onSolverProgress: (callback) => {
    ipcRenderer.on('solver-progress', (event, data) => callback(data));
  },

  // Unsubscribe from solver progress events
  offSolverProgress: (callback) => {
    ipcRenderer.removeListener('solver-progress', callback);
  }
});
