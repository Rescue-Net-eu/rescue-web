"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, type Role, type User } from "./api";

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (email: string, role: Role) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

const STORAGE_KEY = "rescuenet.token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore a persisted session on first load.
  useEffect(() => {
    const stored =
      typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
    if (!stored) {
      setLoading(false);
      return;
    }
    api
      .me(stored)
      .then((u) => {
        setToken(stored);
        setUser(u);
      })
      .catch(() => localStorage.removeItem(STORAGE_KEY))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, role: Role) => {
    const { access_token } = await api.devLogin(email, role);
    const u = await api.me(access_token);
    localStorage.setItem(STORAGE_KEY, access_token);
    setToken(access_token);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
