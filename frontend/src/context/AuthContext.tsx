// src/context/AuthContext.tsx
import { createContext, useContext, useState, type ReactNode } from "react";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());

  // --- Core login logic ---
  const login = async (username: string, password: string): Promise<void> => {
    const response = await fetch("/api/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }),
    });

    if (!response.ok) {
      throw new Error("Invalid credentials");
    }

    const data = await response.json();
    const accessToken = data.access_token;
    setToken(accessToken);
    localStorage.setItem("authToken", accessToken);
  };

  // --- Logout ---
  const logout = () => {
    setToken(null);
    clearStoredToken();
    window.location.href = "/login";
  };

  const value: AuthContextType = {
    token,
    isAuthenticated: !!token,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

// --- Helpers ---
export function getStoredToken(): string | null {
  return localStorage.getItem("authToken");
}

export function clearStoredToken() {
  localStorage.removeItem("authToken");
}
