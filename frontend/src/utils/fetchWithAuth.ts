// frontend/src/utils/fetchWithAuth.ts
import { getStoredToken, clearStoredToken } from "../context/AuthContext";

export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getStoredToken();

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Automatically log out on expired/invalid token
  if (response.status === 401) {
    clearStoredToken();
    window.location.href = "/login";
  }

  return response;
}
