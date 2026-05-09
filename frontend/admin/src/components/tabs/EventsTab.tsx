import { useEffect, useMemo, useState } from 'react';
import { apiListEvents, type EventAdminRead } from '../../api';

type SortKey = 'nombre' | 'ciudad' | 'segmento' | 'fecha';
type SortDir = 'asc' | 'desc';

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="text-gray-700 ml-1">↕</span>;
  return <span className="text-violet-400 ml-1">{dir === 'asc' ? '↑' : '↓'}</span>;
}

export function EventsTab() {
  const [events, setEvents] = useState<EventAdminRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ciudad, setCiudad] = useState('');
  const [segmento, setSegmento] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('nombre');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  function load() {
    setLoading(true);
    setError(null);
    apiListEvents(500, ciudad || undefined, segmento || undefined)
      .then(setEvents)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('asc'); }
  }

  function toggleGroup(name: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  const grouped = useMemo(() => {
    const map = new Map<string, EventAdminRead[]>();
    for (const e of events) {
      const key = e.nombre ?? '—';
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(e);
    }

    for (const list of map.values()) {
      list.sort((a, b) => (a.fecha ?? '').localeCompare(b.fecha ?? ''));
    }

    const groups = [...map.entries()];
    groups.sort(([nameA, listA], [nameB, listB]) => {
      let a: string;
      let b: string;
      if (sortKey === 'nombre') { a = nameA; b = nameB; }
      else if (sortKey === 'fecha') { a = listA[0]?.fecha ?? ''; b = listB[0]?.fecha ?? ''; }
      else if (sortKey === 'ciudad') { a = listA[0]?.ciudad ?? ''; b = listB[0]?.ciudad ?? ''; }
      else { a = listA[0]?.segmento ?? ''; b = listB[0]?.segmento ?? ''; }
      const cmp = a.localeCompare(b);
      return sortDir === 'asc' ? cmp : -cmp;
    });

    return groups;
  }, [events, sortKey, sortDir]);

  function thProps(key: SortKey) {
    return {
      className: 'px-4 py-3 cursor-pointer select-none hover:text-white whitespace-nowrap',
      onClick: () => toggleSort(key),
    };
  }

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
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setExpanded(new Set(grouped.map(([name]) => name)))}
            className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-400"
          >
            Expand all
          </button>
          <button
            onClick={() => setExpanded(new Set())}
            className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-400"
          >
            Collapse all
          </button>
          <span className="text-gray-500 text-xs">
            {events.length} events · {grouped.length} groups
          </span>
        </div>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-500 uppercase bg-gray-900">
            <tr>
              <th {...thProps('nombre')}>
                Name <SortIcon active={sortKey === 'nombre'} dir={sortDir} />
              </th>
              <th {...thProps('ciudad')}>
                City <SortIcon active={sortKey === 'ciudad'} dir={sortDir} />
              </th>
              <th {...thProps('segmento')}>
                Category <SortIcon active={sortKey === 'segmento'} dir={sortDir} />
              </th>
              <th {...thProps('fecha')}>
                Date <SortIcon active={sortKey === 'fecha'} dir={sortDir} />
              </th>
              <th className="px-4 py-3">Venue</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading…</td>
              </tr>
            ) : grouped.map(([groupName, items]) => {
              const isOpen = expanded.has(groupName);
              const first = items[0];
              return (
                <>
                  <tr
                    key={`g-${groupName}`}
                    className="bg-gray-900 hover:bg-gray-800/80 cursor-pointer"
                    onClick={() => toggleGroup(groupName)}
                  >
                    <td className="px-4 py-3 font-semibold text-white">
                      <div className="flex items-center gap-2 max-w-48">
                        <span className="text-gray-500 text-xs shrink-0">{isOpen ? '▾' : '▸'}</span>
                        <span className="truncate">{groupName}</span>
                        <span className="text-xs text-gray-500 font-normal shrink-0">({items.length})</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-400">{first?.ciudad ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-400">{first?.segmento ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-400">{first?.fecha ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-400 max-w-36 truncate">{first?.recinto_nombre ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{first?.estado ?? '—'}</td>
                  </tr>
                  {isOpen && items.map((e) => (
                    <tr key={e.id} className="bg-gray-950 hover:bg-gray-900/30">
                      <td className="py-2 pl-12 pr-4 text-gray-400 max-w-48 truncate">{e.nombre ?? '—'}</td>
                      <td className="px-4 py-2 text-gray-500">{e.ciudad ?? '—'}</td>
                      <td className="px-4 py-2 text-gray-500">{e.segmento ?? '—'}</td>
                      <td className="px-4 py-2 text-gray-500">{e.fecha ?? '—'}</td>
                      <td className="px-4 py-2 text-gray-500 max-w-36 truncate">{e.recinto_nombre ?? '—'}</td>
                      <td className="px-4 py-2 text-gray-600 text-xs">{e.estado ?? '—'}</td>
                    </tr>
                  ))}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
