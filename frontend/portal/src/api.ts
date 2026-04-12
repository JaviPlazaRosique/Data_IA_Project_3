import { getBackendUrl } from './config';

// ─── Token storage ────────────────────────────────────────────────────────────

const TOKEN_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY);
export const getRefreshToken = (): string | null => localStorage.getItem(REFRESH_KEY);
export const setTokens = (access: string, refresh: string): void => {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
};
export const clearTokens = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

// ─── Types ────────────────────────────────────────────────────────────────────

export interface UserRead {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  preferred_budget: string | null;
  preferred_location: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface UpdateMeData {
  full_name?: string | null;
  avatar_url?: string | null;
  preferred_budget?: string | null;
  preferred_location?: string | null;
  password?: string | null;
}

// ─── Base fetch ───────────────────────────────────────────────────────────────

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const base = getBackendUrl();
  return fetch(`${base}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
  });
}

// ─── Authenticated fetch (auto-refresh on 401) ────────────────────────────────

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function attemptRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const res = await apiFetch('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data: TokenResponse = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

export async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> ?? {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${getBackendUrl()}${path}`, { ...options, headers });

  if (res.status !== 401) return res;

  // Single concurrent refresh
  if (!isRefreshing) {
    isRefreshing = true;
    refreshPromise = attemptRefresh().finally(() => { isRefreshing = false; });
  }
  const refreshed = await refreshPromise!;
  if (!refreshed) {
    clearTokens();
    window.location.hash = '#/login';
    return res;
  }

  // Retry with new token
  const newToken = getToken();
  headers['Authorization'] = `Bearer ${newToken}`;
  return fetch(`${getBackendUrl()}${path}`, { ...options, headers });
}

// ─── API calls ────────────────────────────────────────────────────────────────

export async function apiRegister(data: RegisterData): Promise<UserRead> {
  const res = await apiFetch('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail ?? 'Registration failed');
  }
  return res.json();
}

export async function apiLogin(data: LoginData): Promise<TokenResponse> {
  const res = await apiFetch('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail ?? 'Login failed');
  }
  return res.json();
}

export async function apiRefresh(refreshToken: string): Promise<TokenResponse> {
  const res = await apiFetch('/api/v1/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) throw new ApiError(res.status, 'Session expired');
  return res.json();
}

export async function apiLogout(): Promise<void> {
  await authFetch('/api/v1/auth/logout', { method: 'POST' }).catch(() => {});
}

export async function apiGetMe(): Promise<UserRead> {
  const res = await authFetch('/api/v1/users/me');
  if (!res.ok) throw new ApiError(res.status, 'Failed to load user');
  return res.json();
}

export async function apiUpdateMe(data: UpdateMeData): Promise<UserRead> {
  const res = await authFetch('/api/v1/users/me', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail ?? 'Update failed');
  }
  return res.json();
}

// ─── Error type ───────────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// ─── Plan types ───────────────────────────────────────────────────────────────

export interface PlanMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface PlanItinerary {
  stops: unknown[];
  budget: number;
  vibe_chaos: number;
  vibe_hidden: number;
}

export interface PlanRead {
  plan_id: string;
  user_id: string;
  title: string;
  messages: PlanMessage[];
  itinerary: PlanItinerary;
  created_at: string;
  updated_at: string;
}

export interface PlanCreate {
  title?: string;
  messages?: PlanMessage[];
  itinerary?: Partial<PlanItinerary>;
}

export interface PlanUpdate {
  title?: string;
  messages?: PlanMessage[];
  itinerary?: Partial<PlanItinerary>;
}

// ─── Saved event types ────────────────────────────────────────────────────────

export interface SavedEventRead {
  id: string;
  user_id: string;
  event_id: string;
  event_title: string | null;
  event_venue: string | null;
  event_date: string | null;
  event_time: string | null;
  event_image_url: string | null;
  created_at: string;
}

export interface SavedEventCreate {
  event_id: string;
  event_title?: string | null;
  event_venue?: string | null;
  event_date?: string | null;
  event_time?: string | null;
  event_image_url?: string | null;
}

// ─── Review types ─────────────────────────────────────────────────────────────

export interface EventReviewRead {
  id: string;
  user_id: string;
  event_id: string;
  rating: number;
  review_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface EventReviewCreate {
  rating: number;
  review_text?: string | null;
}

export interface EventReviewUpdate {
  rating?: number;
  review_text?: string | null;
}

// ─── Plans API ────────────────────────────────────────────────────────────────

export async function apiListPlans(): Promise<PlanRead[]> {
  const res = await authFetch('/api/v1/plans');
  if (!res.ok) throw new ApiError(res.status, 'Failed to load plans');
  return res.json();
}

export async function apiCreatePlan(data: PlanCreate): Promise<PlanRead> {
  const res = await authFetch('/api/v1/plans', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, 'Failed to create plan');
  return res.json();
}

export async function apiGetPlan(planId: string): Promise<PlanRead> {
  const res = await authFetch(`/api/v1/plans/${planId}`);
  if (!res.ok) throw new ApiError(res.status, 'Failed to load plan');
  return res.json();
}

export async function apiUpdatePlan(planId: string, data: PlanUpdate): Promise<PlanRead> {
  const res = await authFetch(`/api/v1/plans/${planId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, 'Failed to update plan');
  return res.json();
}

export async function apiDeletePlan(planId: string): Promise<void> {
  await authFetch(`/api/v1/plans/${planId}`, { method: 'DELETE' });
}

// ─── Saved Events API ─────────────────────────────────────────────────────────

export async function apiListSavedEvents(): Promise<SavedEventRead[]> {
  const res = await authFetch('/api/v1/users/me/saved-events');
  if (!res.ok) throw new ApiError(res.status, 'Failed to load saved events');
  return res.json();
}

export async function apiSaveEvent(data: SavedEventCreate): Promise<SavedEventRead> {
  const res = await authFetch('/api/v1/users/me/saved-events', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, 'Failed to save event');
  return res.json();
}

export async function apiUnsaveEvent(eventId: string): Promise<void> {
  await authFetch(`/api/v1/users/me/saved-events/${eventId}`, { method: 'DELETE' });
}

// ─── Reviews API ──────────────────────────────────────────────────────────────

export async function apiCreateReview(
  eventId: string,
  data: EventReviewCreate,
): Promise<EventReviewRead> {
  const res = await authFetch(`/api/v1/events/${eventId}/reviews`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, 'Failed to submit review');
  return res.json();
}

export async function apiListEventReviews(eventId: string): Promise<EventReviewRead[]> {
  const res = await authFetch(`/api/v1/events/${eventId}/reviews`);
  if (!res.ok) throw new ApiError(res.status, 'Failed to load reviews');
  return res.json();
}

export async function apiListMyReviews(): Promise<EventReviewRead[]> {
  const res = await authFetch('/api/v1/users/me/reviews');
  if (!res.ok) throw new ApiError(res.status, 'Failed to load reviews');
  return res.json();
}

export async function apiUpdateReview(
  reviewId: string,
  data: EventReviewUpdate,
): Promise<EventReviewRead> {
  const res = await authFetch(`/api/v1/users/me/reviews/${reviewId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, 'Failed to update review');
  return res.json();
}
