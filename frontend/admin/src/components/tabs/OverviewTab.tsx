import { useEffect, useState } from 'react';
import { apiGetStats, type StatsResponse } from '../../api';
import { SkeletonCard } from '../Skeleton';

function Trend({ thisWeek, lastWeek }: { thisWeek: number; lastWeek: number }) {
  if (thisWeek < 0) return null;
  const delta = thisWeek - lastWeek;
  if (delta === 0) return <span className="text-xs text-gray-500">= vs last week</span>;
  const up = delta > 0;
  return (
    <span className={`text-xs ${up ? 'text-emerald-400' : 'text-red-400'}`}>
      {up ? '↑' : '↓'} {Math.abs(delta)} vs last week
    </span>
  );
}

interface StatCardProps {
  label: string;
  value: number | string;
  sub?: string;
  thisWeek?: number;
  lastWeek?: number;
  onClick?: () => void;
}

function StatCard({ label, value, sub, thisWeek, lastWeek, onClick }: StatCardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-gray-900 rounded-xl p-5 flex flex-col gap-1.5 border border-gray-800 ${
        onClick ? 'cursor-pointer hover:border-violet-700 hover:bg-gray-900/80 transition-colors' : ''
      }`}
    >
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      <span className="text-3xl font-bold text-white">
        {typeof value === 'number' && value < 0 ? '—' : (typeof value === 'number' ? value.toLocaleString() : value)}
      </span>
      {thisWeek !== undefined && lastWeek !== undefined && (
        <Trend thisWeek={thisWeek} lastWeek={lastWeek} />
      )}
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
      {onClick && <span className="text-xs text-violet-500 mt-1">View details →</span>}
    </div>
  );
}

interface OverviewTabProps {
  onNavigate?: (tab: string) => void;
  refreshTick?: number;
}

export function OverviewTab({ onNavigate, refreshTick }: OverviewTabProps) {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiGetStats()
      .then(setStats)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [refreshTick]);

  if (error) return <p className="text-red-400 text-sm">{error}</p>;

  if (loading && !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <StatCard
        label="Total Users"
        value={stats.total_users}
        thisWeek={stats.new_users_this_week}
        lastWeek={stats.new_users_last_week}
      />
      <StatCard
        label="Active Users"
        value={stats.active_users}
      />
      <StatCard
        label="Events"
        value={stats.total_events}
        sub="Firestore catalog"
        onClick={onNavigate ? () => onNavigate('events') : undefined}
      />
      <StatCard
        label="Saved Events"
        value={stats.total_saved_events}
        onClick={onNavigate ? () => onNavigate('saved-events') : undefined}
      />
      <StatCard
        label="Total Swipes"
        value={stats.total_swipes}
        sub={stats.total_swipes < 0 ? 'BigQuery unavailable' : undefined}
        thisWeek={stats.swipes_this_week}
        lastWeek={stats.swipes_last_week}
        onClick={onNavigate ? () => onNavigate('analytics') : undefined}
      />
    </div>
  );
}
