import { useEffect, useState } from 'react';
import { apiListEvents, type EventAdminRead } from '../../api';

export function EventsTab() {
  const [events, setEvents] = useState<EventAdminRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ciudad, setCiudad] = useState('');
  const [segmento, setSegmento] = useState('');

  function load() {
    setLoading(true);
    setError(null);
    apiListEvents(200, ciudad || undefined, segmento || undefined)
      .then(setEvents)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-3 flex-wrap items-center">
        <input
          type="text"
          placeholder="City filter…"
          value={ciudad}
          onChange={(e) => setCiudad(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-violet-500 w-40"
        />
        <input
          type="text"
          placeholder="Category filter…"
          value={segmento}
          onChange={(e) => setSegmento(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-violet-500 w-40"
        />
        <button
          onClick={load}
          className="bg-violet-700 hover:bg-violet-600 text-white text-sm px-4 py-2 rounded-lg"
        >
          Filter
        </button>
        <span className="text-gray-500 text-xs ml-auto">{events.length} events</span>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-500 uppercase bg-gray-900">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Venue</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">Loading…</td>
              </tr>
            ) : events.map((e) => (
              <tr key={e.id} className="bg-gray-950 hover:bg-gray-900/50">
                <td className="px-4 py-3 font-medium text-white max-w-48 truncate">{e.nombre ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400">{e.ciudad ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400">{e.segmento ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400">{e.fecha ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400 max-w-36 truncate">{e.recinto_nombre ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400">
                  {e.precio_min != null ? `€${e.precio_min}` : '—'}
                  {e.precio_max != null && e.precio_max !== e.precio_min ? `–€${e.precio_max}` : ''}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{e.estado ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
