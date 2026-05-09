import { useEffect, useState } from 'react';
import { apiGetStats, type StatsResponse } from '../../api';

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 flex flex-col gap-1 border border-gray-800">
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      <span className="text-3xl font-bold text-white">
        {typeof value === 'number' && value < 0 ? '—' : value.toLocaleString()}
      </span>
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
    </div>
  );
}

export function OverviewTab() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGetStats()
      .then(setStats)
      .catch((e: unknown) => setError(String(e)));
  }, []);

  if (error) return <p className="text-red-400 text-sm">{error}</p>;
  if (!stats) return <p className="text-gray-500 text-sm">Loading…</p>;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <StatCard label="Total Users" value={stats.total_users} />
      <StatCard label="Active Users" value={stats.active_users} />
      <StatCard label="Events" value={stats.total_events} sub="Firestore catalog" />
      <StatCard label="Saved Events" value={stats.total_saved_events} />
      <StatCard label="Total Swipes" value={stats.total_swipes} sub={stats.total_swipes < 0 ? 'BigQuery unavailable' : undefined} />
    </div>
  );
}
