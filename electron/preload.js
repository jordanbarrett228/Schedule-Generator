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
  }
});
