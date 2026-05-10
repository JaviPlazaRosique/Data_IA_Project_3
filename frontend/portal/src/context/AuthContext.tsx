import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut,
  type User as FbUser,
} from 'firebase/auth';
import { getFirebaseAuth, googleProvider, microsoftProvider } from '../lib/firebase';
import { apiGetMe, clearDevAuthToken, hasDevAuthToken, type UserRead } from '../api';

interface AuthContextValue {
  fbUser: FbUser | null;
  user: UserRead | null;
  loading: boolean;
  loginEmail: (email: string, password: string) => Promise<void>;
  loginGoogle: () => Promise<void>;
  loginMicrosoft: () => Promise<void>;
  registerEmail: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: UserRead) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [fbUser, setFbUser] = useState<FbUser | null>(null);
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let unsub: (() => void) | undefined;
    (async () => {
      if (hasDevAuthToken()) {
        try {
          setUser(await apiGetMe());
        } catch {
          clearDevAuthToken();
          setUser(null);
        } finally {
          setFbUser(null);
          setLoading(false);
        }
        return;
      }

      const auth = await getFirebaseAuth();
      // Process any pending redirect result (mobile fallback)
      await getRedirectResult(auth).catch(() => {});
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
    })().catch(() => {
      setFbUser(null);
      setUser(null);
      setLoading(false);
    });
    return () => { if (unsub) unsub(); };
  }, []);

  async function loginEmail(email: string, password: string) {
    await signInWithEmailAndPassword(await getFirebaseAuth(), email, password);
  }

  async function loginGoogle() {
    const auth = await getFirebaseAuth();
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      if ((err as { code?: string })?.code === 'auth/popup-blocked') {
        await signInWithRedirect(auth, googleProvider);
      } else {
        throw err;
      }
    }
  }

  async function loginMicrosoft() {
    const auth = await getFirebaseAuth();
    try {
      await signInWithPopup(auth, microsoftProvider);
    } catch (err) {
      if ((err as { code?: string })?.code === 'auth/popup-blocked') {
        await signInWithRedirect(auth, microsoftProvider);
      } else {
        throw err;
      }
    }
  }

  async function registerEmail(email: string, password: string) {
    await createUserWithEmailAndPassword(await getFirebaseAuth(), email, password);
  }

  async function logout() {
    clearDevAuthToken();
    try {
      const auth = await getFirebaseAuth();
      await signOut(auth);
    } catch {
      setFbUser(null);
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider value={{ fbUser, user, loading, loginEmail, loginGoogle, loginMicrosoft, registerEmail, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
