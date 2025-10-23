// frontend/src/utils/api.ts
// API utility for Electron IPC communication (no HTTP, no auth)

declare global {
  interface Window {
    electron?: {
      invoke: (method: string, endpoint: string, data?: any) => Promise<any>;
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
  } else {
    // Fall back to HTTP (for development)
    const baseURL = 'http://localhost:8000';
    const url = baseURL + endpoint;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `HTTP ${response.status}`);
    }

    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return null;
    }

    return await response.json();
  }
}

// Convenience methods
export const api = {
  get: (endpoint: string) => apiRequest('GET', endpoint),
  post: (endpoint: string, data?: any) => apiRequest('POST', endpoint, data),
  put: (endpoint: string, data?: any) => apiRequest('PUT', endpoint, data),
  delete: (endpoint: string) => apiRequest('DELETE', endpoint),
};
