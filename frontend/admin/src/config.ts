export interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
}

interface PublicConfig {
  adminApiUrl?: string;
  firebase?: FirebaseConfig;
}

let config: PublicConfig = {};

export const configReady: Promise<void> = (async () => {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}public-config.json`);
    if (res.ok) config = await res.json();
  } catch {
    // fall through to env var fallbacks
  }
})();

export function awaitConfig(): Promise<void> {
  return configReady;
}

export function getAdminApiUrl(): string {
  return config.adminApiUrl ?? import.meta.env.VITE_ADMIN_API_URL ?? 'http://localhost:8001';
}

export function getFirebaseConfig(): FirebaseConfig | null {
  if (config.firebase) return config.firebase;
  const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
  const authDomain = import.meta.env.VITE_FIREBASE_AUTH_DOMAIN;
  const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID;
  if (!apiKey || !authDomain || !projectId) return null;
  return { apiKey, authDomain, projectId };
}
