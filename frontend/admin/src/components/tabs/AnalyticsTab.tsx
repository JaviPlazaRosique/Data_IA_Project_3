import { useEffect, useState } from 'react';
import { apiGetAnalytics, type AnalyticsResponse } from '../../api';

function Bar({ label, left, right, maxVal }: { label: string; left: number; right: number; maxVal: number }) {
  const leftPct = maxVal > 0 ? (left / maxVal) * 100 : 0;
  const rightPct = maxVal > 0 ? (right / maxVal) * 100 : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-gray-500 w-20 shrink-0 text-right">{label}</span>
      <div className="flex-1 flex flex-col gap-0.5">
        <div className="flex items-center gap-1">
          <div className="bg-red-500/70 rounded-sm h-2" style={{ width: `${leftPct}%`, minWidth: left > 0 ? 2 : 0 }} />
          <span className="text-gray-400">{left}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="bg-emerald-500/70 rounded-sm h-2" style={{ width: `${rightPct}%`, minWidth: right > 0 ? 2 : 0 }} />
          <span className="text-gray-400">{right}</span>
        </div>
      </div>
    </div>
  );
}

export function AnalyticsTab() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGetAnalytics()
      .then(setData)
      .catch((e: unknown) => setError(String(e)));
  }, []);

  if (error) return <p className="text-red-400 text-sm">{error}</p>;
  if (!data) return <p className="text-gray-500 text-sm">Loading…</p>;

  const maxDaily = Math.max(...data.daily_swipes.map((d) => Math.max(d.left, d.right)), 1);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 max-w-xs">
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Swipe Left</p>
          <p className="text-2xl font-bold text-red-400">{data.swipe_totals.left.toLocaleString()}</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Swipe Right</p>
          <p className="text-2xl font-bold text-emerald-400">{data.swipe_totals.right.toLocaleString()}</p>
        </div>
      </div>

      {data.daily_swipes.length > 0 ? (
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">Last 30 Days</p>
          <div className="flex gap-4 text-xs mb-3">
            <span className="flex items-center gap-1"><span className="w-3 h-2 rounded-sm bg-red-500/70 inline-block" /> Left</span>
            <span className="flex items-center gap-1"><span className="w-3 h-2 rounded-sm bg-emerald-500/70 inline-block" /> Right</span>
          </div>
          <div className="flex flex-col gap-1 max-h-96 overflow-y-auto">
            {data.daily_swipes.map((d) => (
              <Bar key={d.date} label={d.date.slice(5)} left={d.left} right={d.right} maxVal={maxDaily} />
            ))}
          </div>
        </div>
      ) : (
        <p className="text-gray-500 text-sm">No swipe data in BigQuery yet.</p>
      )}
    </div>
  );
}
