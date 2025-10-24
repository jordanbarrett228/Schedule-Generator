// frontend/src/utils/api.ts
// API utility for Electron IPC communication (no HTTP, no auth)

declare global {
  interface Window {
    electron?: {
      invoke: (method: string, endpoint: string, data?: any) => Promise<any>;
      onSolverProgress: (callback: (data: any) => void) => void;
      offSolverProgress: (callback: (data: any) => void) => void;
      onSolverComplete: (callback: (data: any) => void) => void;
      offSolverComplete: (callback: (data: any) => void) => void;
    };
  }
}

/**
 * Make an API request via Electron IPC
 * Falls back to HTTP fetch for development/web mode
 */
export async function apiRequest(
  method: string,
  endpoint: string,
  data?: any
): Promise<any> {
  // Check if running in Electron
  if (window.electron) {
    // Use Electron IPC
    try {
      const result = await window.electron.invoke(method, endpoint, data);
      return result;
    } catch (error: any) {
      throw new Error(error.message || 'API request failed');
    }
  }
}

// Convenience methods
export const api = {
  get: (endpoint: string) => apiRequest('GET', endpoint),
  post: (endpoint: string, data?: any) => apiRequest('POST', endpoint, data),
  put: (endpoint: string, data?: any) => apiRequest('PUT', endpoint, data),
  delete: (endpoint: string) => apiRequest('DELETE', endpoint),
};
