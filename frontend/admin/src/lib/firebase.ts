import { initializeApp, type FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, type Auth } from 'firebase/auth';
import { getFirebaseConfig } from '../config';

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

export function getFirebaseAuth(): Auth {
  if (auth) return auth;
  const cfg = getFirebaseConfig();
  if (!cfg) throw new Error('Firebase config missing. Set VITE_FIREBASE_* env vars.');
  app = initializeApp(cfg);
  auth = getAuth(app);
  return auth;
}

export const googleProvider = new GoogleAuthProvider();
