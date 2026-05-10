import { awaitConfig, getAdminApiUrl } from './config';
import { getFirebaseAuth } from './lib/firebase';

async function getToken(): Promise<string | null> {
  try {
    const auth = await getFirebaseAuth();
    const u = auth.currentUser;
    if (!u) return null;
    return u.getIdToken();
  } catch {
    return null;
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  await awaitConfig();
  const token = await getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${getAdminApiUrl()}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AdminUserRead {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface UserListResponse {
  items: AdminUserRead[];
  total: number;
  page: number;
  limit: number;
}

export interface StatsResponse {
  total_users: number;
  active_users: number;
  total_events: number;
  total_saved_events: number;
  total_swipes: number;
  new_users_this_week: number;
  new_users_last_week: number;
  swipes_this_week: number;
  swipes_last_week: number;
}

export interface EventAdminRead {
  id: string;
  nombre: string | null;
  ciudad: string | null;
  segmento: string | null;
  fecha: string | null;
  hora: string | null;
  recinto_nombre: string | null;
  estado: string | null;
}

export interface SwipeTotals {
  left: number;
  right: number;
}

export interface DailySwipe {
  date: string;
  left: number;
  right: number;
}

export interface AnalyticsResponse {
  swipe_totals: SwipeTotals;
  daily_swipes: DailySwipe[];
}

export interface EventSwipeStats {
  event_id: string;
  left: number;
  right: number;
  total: number;
  right_ratio: number;
}

export interface TopSavedEvent {
  event_id: string;
  event_title: string | null;
  event_venue: string | null;
  save_count: number;
}

export interface RecentSave {
  event_id: string;
  event_title: string | null;
  user_email: string;
  saved_at: string;
}

export interface SavedEventsAdminResponse {
  total: number;
  top_events: TopSavedEvent[];
  recent_saves: RecentSave[];
}

// ─── API calls ────────────────────────────────────────────────────────────────

export function apiGetMe(): Promise<AdminUserRead> {
  return apiFetch('/api/v1/me');
}

export function apiGetStats(): Promise<StatsResponse> {
  return apiFetch('/api/v1/stats');
}

export function apiListUsers(page = 1, limit = 50, search?: string): Promise<UserListResponse> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (search) params.set('search', search);
  return apiFetch(`/api/v1/users?${params}`);
}

export function apiPatchUser(
  userId: string,
  patch: { is_active?: boolean; is_admin?: boolean },
): Promise<AdminUserRead> {
  return apiFetch(`/api/v1/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
}

export function apiListEvents(limit = 100, ciudad?: string, segmento?: string): Promise<EventAdminRead[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (ciudad) params.set('ciudad', ciudad);
  if (segmento) params.set('segmento', segmento);
  return apiFetch(`/api/v1/events?${params}`);
}

export function apiGetAnalytics(startDate?: string, endDate?: string): Promise<AnalyticsResponse> {
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  const qs = params.toString();
  return apiFetch(`/api/v1/analytics${qs ? `?${qs}` : ''}`);
}

export function apiGetEventSwipeStats(limit = 20): Promise<EventSwipeStats[]> {
  return apiFetch(`/api/v1/analytics/events?limit=${limit}`);
}

export function apiGetSavedEvents(limit = 20): Promise<SavedEventsAdminResponse> {
  return apiFetch(`/api/v1/saved-events?limit=${limit}`);
}

// ─── Infrastructure ───────────────────────────────────────────────────────────

export interface ServiceCheck {
  name: string;
  status: 'ok' | 'degraded' | 'error' | 'unknown';
  latency_ms: number | null;
  detail: string | null;
}

export interface InfrastructureResponse {
  services: ServiceCheck[];
}

export function apiGetInfrastructure(): Promise<InfrastructureResponse> {
  return apiFetch('/api/v1/infrastructure');
}

// ─── KPIs ─────────────────────────────────────────────────────────────────────

export interface EngagementKPIs {
  active_users_7d: number;
  active_users_30d: number;
  total_swipes_30d: number;
  right_swipes_30d: number;
  avg_right_swipe_rate: number;
  avg_dwell_ms: number;
  avg_dwell_liked_ms: number;
  avg_plans_per_active_user: number;
}

export interface SegmentStat {
  name: string;
  total: number;
  liked: number;
  like_rate: number;
}

export interface CityActivity {
  city: string;
  total_swipes: number;
  liked: number;
  like_rate: number;
}

export interface DailyActivity {
  date: string;
  swipes: number;
  likes: number;
}

export interface PlannerUsage {
  total_chat_swipes_30d: number;
  chat_right_rate: number;
}

export interface KPIsResponse {
  engagement: EngagementKPIs;
  top_segments: SegmentStat[];
  top_genres: SegmentStat[];
  top_cities: CityActivity[];
  daily_activity_30d: DailyActivity[];
  planner: PlannerUsage;
}

export function apiGetKPIs(): Promise<KPIsResponse> {
  return apiFetch('/api/v1/kpis');
}
