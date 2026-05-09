export function getAdminApiUrl(): string {
  return import.meta.env.VITE_ADMIN_API_URL ?? 'http://localhost:8001';
}

export interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
}

export function getFirebaseConfig(): FirebaseConfig | null {
  const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
  const authDomain = import.meta.env.VITE_FIREBASE_AUTH_DOMAIN;
  const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID;
  if (!apiKey || !authDomain || !projectId) return null;
  return { apiKey, authDomain, projectId };
}
