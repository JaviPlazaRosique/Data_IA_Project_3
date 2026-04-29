export interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
}

interface PublicConfig {
  backendUrl: string;
  firebase?: FirebaseConfig;
}

let config: PublicConfig = { backendUrl: '' };
let serverAvailable = true;

// Fire the fetch eagerly on module import so it overlaps React boot.
// Pages call awaitConfig() (or use the api helpers) which won't issue
// requests until this resolves.
export const configReady: Promise<void> = (async () => {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}public-config.json`);
    if (res.ok) {
      config = await res.json();
    } else {
      serverAvailable = false;
    }
  } catch {
    serverAvailable = false;
  }
})();

export function awaitConfig(): Promise<void> {
  return configReady;
}

export function getBackendUrl(): string {
  return config.backendUrl;
}

export function isServerAvailable(): boolean {
  return serverAvailable;
}

export function getFirebaseConfig(): FirebaseConfig | null {
  return config.firebase ?? null;
}
