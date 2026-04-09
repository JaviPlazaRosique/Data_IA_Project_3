import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  apiGetMe,
  apiLogin,
  apiLogout,
  apiRefresh,
  apiRegister,
  clearTokens,
  getRefreshToken,
  getToken,
  setTokens,
  type RegisterData,
  type UserRead,
} from '../api';

interface AuthContextValue {
  user: UserRead | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: UserRead) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    async function restore() {
      const token = getToken();
      if (!token) { setLoading(false); return; }

      try {
        const me = await apiGetMe();
        setUser(me);
      } catch {
        // Access token expired — try refresh
        const refreshToken = getRefreshToken();
        if (!refreshToken) { clearTokens(); setLoading(false); return; }
        try {
          const tokens = await apiRefresh(refreshToken);
          setTokens(tokens.access_token, tokens.refresh_token);
          const me = await apiGetMe();
          setUser(me);
        } catch {
          clearTokens();
        }
      } finally {
        setLoading(false);
      }
    }
    restore();
  }, []);

  async function login(email: string, password: string) {
    const tokens = await apiLogin({ email, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    const me = await apiGetMe();
    setUser(me);
  }

  async function register(data: RegisterData) {
    await apiRegister(data);
    await login(data.email, data.password);
  }

  async function logout() {
    await apiLogout();
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
