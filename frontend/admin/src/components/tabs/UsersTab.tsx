import { useEffect, useState } from 'react';
import { apiListUsers, apiPatchUser, type AdminUserRead } from '../../api';

function Badge({ on, label }: { on: boolean; label: string }) {
  return (
    <span
      className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium ${
        on ? 'bg-emerald-900 text-emerald-300' : 'bg-gray-800 text-gray-500'
      }`}
    >
      {label}
    </span>
  );
}

export function UsersTab() {
  const [users, setUsers] = useState<AdminUserRead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const limit = 50;

  function load(p: number, q: string) {
    setLoading(true);
    setError(null);
    apiListUsers(p, limit, q || undefined)
      .then((res) => {
        setUsers(res.items);
        setTotal(res.total);
        setPage(p);
      })
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(1, ''); }, []);

  async function toggle(user: AdminUserRead, field: 'is_active' | 'is_admin') {
    try {
      const updated = await apiPatchUser(user.id, { [field]: !user[field] });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (e: unknown) {
      alert(String(e));
    }
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-3 items-center">
        <input
          type="text"
          placeholder="Search by email or username…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load(1, search)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-violet-500 w-72"
        />
        <button
          onClick={() => load(1, search)}
          className="bg-violet-700 hover:bg-violet-600 text-white text-sm px-4 py-2 rounded-lg"
        >
          Search
        </button>
        <span className="text-gray-500 text-xs ml-auto">{total} users total</span>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-500 uppercase bg-gray-900">
            <tr>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Joined</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading…</td>
              </tr>
            ) : users.map((u) => (
              <tr key={u.id} className="bg-gray-950 hover:bg-gray-900/50">
                <td className="px-4 py-3 font-medium text-white">{u.username}</td>
                <td className="px-4 py-3 text-gray-400">{u.email}</td>
                <td className="px-4 py-3">
                  <Badge on={u.is_active} label={u.is_active ? 'Active' : 'Inactive'} />
                </td>
                <td className="px-4 py-3">
                  {u.is_admin && <Badge on label="Admin" />}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggle(u, 'is_active')}
                      className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300"
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button
                      onClick={() => toggle(u, 'is_admin')}
                      className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300"
                    >
                      {u.is_admin ? 'Remove Admin' : 'Make Admin'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex gap-2 items-center justify-end">
          <button
            disabled={page <= 1}
            onClick={() => load(page - 1, search)}
            className="text-xs px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-xs text-gray-500">Page {page} / {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => load(page + 1, search)}
            className="text-xs px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
