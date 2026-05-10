import { useEffect, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell,
  Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';
import { apiGetKPIs, type KPIsResponse, type SegmentStat, type CityActivity } from '../../api';
import { SkeletonCard } from '../Skeleton';

const VIOLET = '#7c3aed';
const EMERALD = '#10b981';
const PALETTE = [VIOLET, '#6d28d9', '#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#8b5cf6', '#14b8a6'];

function KPICard({
  label, value, unit, sub, icon, highlight,
}: {
  label: string; value: number | string; unit?: string; sub?: string; icon: string; highlight?: boolean;
}) {
  const isUnavailable = typeof value === 'number' && value < 0;
  return (
    <div className={`bg-gray-900 rounded-xl p-5 flex flex-col gap-1.5 border ${highlight ? 'border-violet-800' : 'border-gray-800'}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="material-symbols-outlined text-[16px] text-gray-500">{icon}</span>
        <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      </div>
      <div className="flex items-end gap-1">
        <span className="text-3xl font-bold text-white">
          {isUnavailable ? '—' : (typeof value === 'number' ? value.toLocaleString('es-ES') : value)}
        </span>
        {!isUnavailable && unit && <span className="text-sm text-gray-400 mb-0.5">{unit}</span>}
      </div>
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
    </div>
  );
}

function HorizontalBar({ items, valueKey, nameKey, colorKey }: {
  items: (SegmentStat | CityActivity)[];
  valueKey: 'total' | 'total_swipes';
  nameKey: 'name' | 'city';
  colorKey?: 'like_rate';
}) {
  if (!items.length) return <p className="text-gray-600 text-sm">Sin datos</p>;
  const maxVal = Math.max(...items.map((i) => (i as unknown as Record<string, number>)[valueKey]));
  return (
    <div className="flex flex-col gap-2">
      {items.map((item, idx) => {
        const val = (item as unknown as Record<string, number>)[valueKey];
        const name = (item as unknown as Record<string, string>)[nameKey];
        const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
        const likeRate = item.like_rate;
        return (
          <div key={name} className="flex items-center gap-3">
            <span className="text-xs text-gray-400 w-28 truncate shrink-0" title={name}>{name}</span>
            <div className="flex-1 bg-gray-800 rounded-full h-2 overflow-hidden">
              <div
                className="h-2 rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, backgroundColor: PALETTE[idx % PALETTE.length] }}
              />
            </div>
            <span className="text-xs text-gray-300 w-12 text-right">{val.toLocaleString('es-ES')}</span>
            {colorKey && (
              <span className="text-xs w-12 text-right" style={{ color: likeRate >= 50 ? EMERALD : likeRate >= 30 ? '#f59e0b' : '#ef4444' }}>
                {likeRate}%
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function SectionTitle({ icon, title, sub }: { icon: string; title: string; sub?: string }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="material-symbols-outlined text-[18px] text-violet-400">{icon}</span>
      <div>
        <p className="text-sm font-semibold text-white">{title}</p>
        {sub && <p className="text-xs text-gray-500">{sub}</p>}
      </div>
    </div>
  );
}

interface Props {
  refreshTick?: number;
}

export function KPIsTab({ refreshTick }: Props) {
  const [data, setData] = useState<KPIsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiGetKPIs()
      .then(setData)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [refreshTick]);

  if (error) return <p className="text-red-400 text-sm">{error}</p>;

  if (loading && !data) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  if (!data) return null;

  const { engagement, top_segments, top_genres, top_cities, daily_activity_30d, planner } = data;

  const bqUnavailable = engagement.active_users_30d < 0;

  return (
    <div className="flex flex-col gap-8">
      {bqUnavailable && (
        <div className="px-4 py-3 bg-yellow-900/30 border border-yellow-800 rounded-lg text-xs text-yellow-300">
          BigQuery no disponible — mostrando datos parciales
        </div>
      )}

      {/* Engagement KPIs */}
      <div>
        <SectionTitle icon="people" title="Usuarios activos" sub="Últimos 7 y 30 días" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Activos 7d" value={engagement.active_users_7d} icon="person" highlight />
          <KPICard label="Activos 30d" value={engagement.active_users_30d} icon="group" highlight />
          <KPICard
            label="Tasa de like (30d)"
            value={bqUnavailable ? '—' : `${engagement.avg_right_swipe_rate}`}
            unit="%"
            icon="thumb_up"
            sub="% swipes hacia la derecha"
          />
          <KPICard
            label="Planes por usuario"
            value={bqUnavailable ? '—' : engagement.avg_plans_per_active_user}
            icon="event_note"
            sub="Media de swipes por usuario activo"
          />
        </div>
      </div>

      {/* Swipes KPIs */}
      <div>
        <SectionTitle icon="swipe" title="Actividad de swipes" sub="Últimos 30 días" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Total swipes" value={engagement.total_swipes_30d} icon="touch_app" />
          <KPICard label="Planes guardados" value={engagement.right_swipes_30d} icon="favorite" sub="Swipes derecha" />
          <KPICard
            label="Tiempo visto (avg)"
            value={bqUnavailable ? '—' : Math.round(engagement.avg_dwell_ms / 1000)}
            unit="s"
            icon="timer"
            sub="Tiempo medio por evento"
          />
          <KPICard
            label="Tiempo si gusta"
            value={bqUnavailable ? '—' : Math.round(engagement.avg_dwell_liked_ms / 1000)}
            unit="s"
            icon="timer"
            sub="Tiempo medio en eventos que gustan"
          />
        </div>
      </div>

      {/* AI Planner */}
      <div>
        <SectionTitle icon="smart_toy" title="AI Planner" sub="Uso del agente IA en los últimos 30 días" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Swipes desde chat" value={planner.total_chat_swipes_30d} icon="chat" />
          <KPICard
            label="Like rate (chat)"
            value={planner.chat_right_rate < 0 ? '—' : planner.chat_right_rate}
            unit="%"
            icon="thumb_up"
            sub="Tasa de aceptación de recomendaciones IA"
            highlight
          />
        </div>
      </div>

      {/* Daily trend */}
      {daily_activity_30d.length > 0 && (
        <div>
          <SectionTitle icon="show_chart" title="Actividad diaria" sub="Swipes y likes últimos 30 días" />
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={daily_activity_30d} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  tickFormatter={(v: string) => v.slice(5)}
                />
                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#9ca3af' }}
                />
                <Line type="monotone" dataKey="swipes" stroke={VIOLET} strokeWidth={2} dot={false} name="Swipes" />
                <Line type="monotone" dataKey="likes" stroke={EMERALD} strokeWidth={2} dot={false} name="Likes" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Segments & Genres */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <SectionTitle icon="category" title="Top segmentos" sub="30 días · total swipes y % like" />
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            {top_segments.length > 0 ? (
              <HorizontalBar items={top_segments} valueKey="total" nameKey="name" colorKey="like_rate" />
            ) : (
              <p className="text-gray-600 text-sm">Sin datos de BigQuery</p>
            )}
            {top_segments.length > 0 && (
              <p className="text-xs text-gray-600 mt-3">% de color = tasa de like del segmento</p>
            )}
          </div>
        </div>

        <div>
          <SectionTitle icon="music_note" title="Top géneros" sub="30 días · total swipes y % like" />
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            {top_genres.length > 0 ? (
              <HorizontalBar items={top_genres} valueKey="total" nameKey="name" colorKey="like_rate" />
            ) : (
              <p className="text-gray-600 text-sm">Sin datos de BigQuery</p>
            )}
          </div>
        </div>
      </div>

      {/* Cities */}
      {top_cities.length > 0 && (
        <div>
          <SectionTitle icon="location_on" title="Actividad por ciudad" sub="30 días · swipes y % like" />
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={top_cities} layout="vertical" margin={{ top: 0, right: 20, left: 60, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 10 }} />
                <YAxis dataKey="city" type="category" tick={{ fill: '#9ca3af', fontSize: 11 }} width={55} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#9ca3af' }}
                  formatter={(v, name) => [typeof v === 'number' ? v.toLocaleString('es-ES') : v, name === 'total_swipes' ? 'Swipes' : 'Likes']}
                />
                <Bar dataKey="total_swipes" radius={[0, 4, 4, 0]} name="Swipes">
                  {top_cities.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
