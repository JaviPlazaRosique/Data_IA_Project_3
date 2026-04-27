const SESSION_KEY = 'analytics_session_id';

function genId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

export function getSessionId(): string {
  try {
    const existing = sessionStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    const fresh = genId();
    sessionStorage.setItem(SESSION_KEY, fresh);
    return fresh;
  } catch {
    return genId();
  }
}
