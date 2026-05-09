import { useEffect, useState } from 'react';
import { apiGetSavedEvents, type SavedEventsAdminResponse } from '../../api';
import { SkeletonTable } from '../Skeleton';

export function SavedEventsTab({ refreshTick }: { refreshTick?: number }) {
  const [data, setData] = useState<SavedEventsAdminResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiGetSavedEvents(25)
      .then(setData)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [refreshTick]);

  if (error) return <p className="text-red-400 text-sm">{error}</p>;

  const maxSaves = data?.top_events[0]?.save_count ?? 1;

  return (
    <div className="flex flex-col gap-6">
      {data && (
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 inline-flex flex-col gap-1 self-start">
          <span className="text-xs text-gray-500 uppercase tracking-wider">Total Saves</span>
          <span className="text-3xl font-bold text-white">{data.total.toLocaleString()}</span>
        </div>
      )}

      <div className="flex flex-col gap-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">Most Saved Events</p>
        {loading && !data ? (
          <SkeletonTable rows={8} cols={4} />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 uppercase bg-gray-900">
                <tr>
                  <th className="px-4 py-3">Event</th>
                  <th className="px-4 py-3">Venue</th>
                  <th className="px-4 py-3">Event ID</th>
                  <th className="px-4 py-3">Saves</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {data?.top_events.map((e) => (
                  <tr key={e.event_id} className="bg-gray-950 hover:bg-gray-900/50">
                    <td className="px-4 py-3 font-medium text-white max-w-48 truncate">
                      {e.event_title ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-400 max-w-36 truncate">
                      {e.event_venue ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs max-w-32 truncate">
                      {e.event_id}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-24 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-violet-500 rounded-full"
                            style={{ width: `${(e.save_count / maxSaves) * 100}%` }}
                          />
                        </div>
                        <span className="text-violet-300 font-semibold text-sm">{e.save_count}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">Recent Saves</p>
        {loading && !data ? (
          <SkeletonTable rows={5} cols={3} />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 uppercase bg-gray-900">
                <tr>
                  <th className="px-4 py-3">Event</th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Saved At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {data?.recent_saves.map((r, i) => (
                  <tr key={i} className="bg-gray-950 hover:bg-gray-900/50">
                    <td className="px-4 py-3 text-white max-w-48 truncate">
                      {r.event_title ?? r.event_id}
                    </td>
                    <td className="px-4 py-3 text-gray-400">{r.user_email}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(r.saved_at).toLocaleString()}
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
