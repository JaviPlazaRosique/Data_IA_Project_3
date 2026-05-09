import { useEffect, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiGetAnalytics, apiGetEventSwipeStats, type AnalyticsResponse, type EventSwipeStats } from '../../api';
import { SkeletonTable } from '../Skeleton';

function iso30DaysAgo(): string {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return d.toISOString().slice(0, 10);
}

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

export function AnalyticsTab({ refreshTick }: { refreshTick?: number }) {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [eventStats, setEventStats] = useState<EventSwipeStats[]>([]);
  const [loadingMain, setLoadingMain] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState(iso30DaysAgo());
  const [endDate, setEndDate] = useState(isoToday());
  const [appliedStart, setAppliedStart] = useState(iso30DaysAgo());
  const [appliedEnd, setAppliedEnd] = useState(isoToday());

  function loadMain(s: string, e: string) {
    setLoadingMain(true);
    setError(null);
    apiGetAnalytics(s, e)
      .then(setData)
      .catch((err: unknown) => setError(String(err)))
      .finally(() => setLoadingMain(false));
  }

  function loadEvents() {
    setLoadingEvents(true);
    apiGetEventSwipeStats(25)
      .then(setEventStats)
      .catch(() => {})
      .finally(() => setLoadingEvents(false));
  }

  useEffect(() => {
    loadMain(appliedStart, appliedEnd);
    loadEvents();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTick]);

  function applyDates() {
    setAppliedStart(startDate);
    setAppliedEnd(endDate);
    loadMain(startDate, endDate);
  }

  const maxEvents = eventStats[0]?.total ?? 1;

  return (
    <div className="flex flex-col gap-6">
      {/* Swipe totals */}
      {data && (
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
      )}

      {/* Date range + chart */}
      <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 flex flex-col gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs text-gray-500 uppercase tracking-wider">Daily Swipes</span>
          <div className="flex items-center gap-2 ml-auto flex-wrap">
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-violet-500"
            />
            <span className="text-gray-600 text-xs">→</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-violet-500"
            />
            <button
              onClick={applyDates}
              className="bg-violet-700 hover:bg-violet-600 text-white text-xs px-3 py-1.5 rounded"
            >
              Apply
            </button>
          </div>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {loadingMain ? (
          <div className="h-64 flex items-center justify-center text-gray-500 text-sm">Loading…</div>
        ) : data && data.daily_swipes.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.daily_swipes} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#6b7280', fontSize: 11 }}
                tickFormatter={(v: string) => v.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} width={36} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#9ca3af', fontSize: 12 }}
                itemStyle={{ fontSize: 12 }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
              <Line type="monotone" dataKey="left" stroke="#f87171" strokeWidth={2} dot={false} name="Left" />
              <Line type="monotone" dataKey="right" stroke="#34d399" strokeWidth={2} dot={false} name="Right" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-sm">No swipe data for selected range.</p>
        )}
      </div>

      {/* Per-event swipe table */}
      <div className="flex flex-col gap-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">Top Events by Swipes</p>
        {loadingEvents ? (
          <SkeletonTable rows={6} cols={5} />
        ) : eventStats.length === 0 ? (
          <p className="text-gray-500 text-sm">No event swipe data available.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 uppercase bg-gray-900">
                <tr>
                  <th className="px-4 py-3">Event ID</th>
                  <th className="px-4 py-3 text-red-400">Left</th>
                  <th className="px-4 py-3 text-emerald-400">Right</th>
                  <th className="px-4 py-3">Total</th>
                  <th className="px-4 py-3">Like Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {eventStats.map((e) => (
                  <tr key={e.event_id} className="bg-gray-950 hover:bg-gray-900/50">
                    <td className="px-4 py-2.5 text-gray-300 font-mono text-xs max-w-48 truncate">{e.event_id}</td>
                    <td className="px-4 py-2.5 text-red-400">{e.left.toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-emerald-400">{e.right.toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-gray-400">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-violet-500 rounded-full"
                            style={{ width: `${(e.total / maxEvents) * 100}%` }}
                          />
                        </div>
                        {e.total.toLocaleString()}
                      </div>
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${e.right_ratio >= 50 ? 'bg-emerald-500' : 'bg-red-500'}`}
                            style={{ width: `${e.right_ratio}%` }}
                          />
                        </div>
                        <span className={`text-xs ${e.right_ratio >= 50 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {e.right_ratio}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
