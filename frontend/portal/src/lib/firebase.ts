import { initializeApp, type FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, OAuthProvider, type Auth } from 'firebase/auth';
import { awaitConfig, getFirebaseConfig } from '../config';

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

export async function getFirebaseAuth(): Promise<Auth> {
  if (auth) return auth;
  await awaitConfig();
  const cfg = getFirebaseConfig();
  if (!cfg) throw new Error('Firebase config missing in public-config.json');
  app = initializeApp(cfg);
  auth = getAuth(app);
  return auth;
}

export const googleProvider = new GoogleAuthProvider();
export const microsoftProvider = new OAuthProvider('microsoft.com');
microsoftProvider.setCustomParameters({ tenant: 'common' });
