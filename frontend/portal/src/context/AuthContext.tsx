import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  sendEmailVerification,
  signOut,
  type User as FbUser,
} from 'firebase/auth';
import { getFirebaseAuth, googleProvider, microsoftProvider } from '../lib/firebase';
import { apiGetMe, type UserRead } from '../api';

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

export class EmailNotVerifiedError extends Error {
  constructor() {
    super('Email no verificado. Revisa tu bandeja de entrada.');
    this.name = 'EmailNotVerifiedError';
  }
}

function isPasswordProvider(u: FbUser): boolean {
  return u.providerData.some((p) => p.providerId === 'password');
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [fbUser, setFbUser] = useState<FbUser | null>(null);
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let unsub: (() => void) | undefined;
    (async () => {
      const auth = await getFirebaseAuth();
      unsub = onAuthStateChanged(auth, async (u) => {
        if (!u) {
          setFbUser(null);
          setUser(null);
          setLoading(false);
          return;
        }
        if (isPasswordProvider(u) && !u.emailVerified) {
          setFbUser(u);
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
    })();
    return () => { if (unsub) unsub(); };
  }, []);

  async function loginEmail(email: string, password: string) {
    const auth = await getFirebaseAuth();
    const cred = await signInWithEmailAndPassword(auth, email, password);
    if (!cred.user.emailVerified) {
      await signOut(auth);
      throw new EmailNotVerifiedError();
    }
  }

  async function loginGoogle() {
    const auth = await getFirebaseAuth();
    await signInWithPopup(auth, googleProvider);
  }

  async function loginMicrosoft() {
    const auth = await getFirebaseAuth();
    await signInWithPopup(auth, microsoftProvider);
  }

  async function registerEmail(email: string, password: string) {
    const auth = await getFirebaseAuth();
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    await sendEmailVerification(cred.user);
    await signOut(auth);
  }

  async function logout() {
    const auth = await getFirebaseAuth();
    await signOut(auth);
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
