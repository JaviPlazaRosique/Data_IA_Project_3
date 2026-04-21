interface PublicConfig {
  backendUrl: string;
}

let config: PublicConfig = { backendUrl: '' };
let serverAvailable = true;

export async function loadConfig(): Promise<void> {
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
}

export function getBackendUrl(): string {
  return config.backendUrl;
}

export function isServerAvailable(): boolean {
  return serverAvailable;
}
