import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  type User as FbUser,
} from 'firebase/auth';
import { getFirebaseAuth, googleProvider } from '../lib/firebase';
import { apiGetMe, type AdminUserRead } from '../api';

interface AuthContextValue {
  fbUser: FbUser | null;
  user: AdminUserRead | null;
  loading: boolean;
  loginEmail: (email: string, password: string) => Promise<void>;
  loginGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [fbUser, setFbUser] = useState<FbUser | null>(null);
  const [user, setUser] = useState<AdminUserRead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let unsub: (() => void) | undefined;
    (async () => {
      try {
        const auth = await getFirebaseAuth();
        unsub = onAuthStateChanged(auth, async (u) => {
          if (!u) {
            setFbUser(null);
            setUser(null);
            setLoading(false);
            return;
          }
          setFbUser(u);
          try {
            const me = await apiGetMe();
            setUser(me);
          } catch {
            setUser(null);
          } finally {
            setLoading(false);
          }
        });
      } catch {
        setFbUser(null);
        setUser(null);
        setLoading(false);
      }
    })();
    return () => { if (unsub) unsub(); };
  }, []);

  async function loginEmail(email: string, password: string) {
    await signInWithEmailAndPassword(await getFirebaseAuth(), email, password);
  }

  async function loginGoogle() {
    await signInWithPopup(await getFirebaseAuth(), googleProvider);
  }

  async function logout() {
    try {
      await signOut(await getFirebaseAuth());
    } catch {
      setFbUser(null);
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider value={{ fbUser, user, loading, loginEmail, loginGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
