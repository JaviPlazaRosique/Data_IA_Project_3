import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ToastProvider, useToast } from '../components/Toast';
import { OverviewTab } from '../components/tabs/OverviewTab';
import { EventsTab } from '../components/tabs/EventsTab';
import { AnalyticsTab } from '../components/tabs/AnalyticsTab';
import { SavedEventsTab } from '../components/tabs/SavedEventsTab';
import { InfrastructureTab } from '../components/tabs/InfrastructureTab';
import { KPIsTab } from '../components/tabs/KPIsTab';

const TABS = [
  { id: 'overview', label: 'Overview', icon: 'dashboard', key: '1' },
  { id: 'kpis', label: 'KPIs', icon: 'leaderboard', key: '2' },
  { id: 'infrastructure', label: 'Infraestructura', icon: 'dns', key: '3' },
  { id: 'events', label: 'Eventos', icon: 'event', key: '4' },
  { id: 'analytics', label: 'Analytics', icon: 'bar_chart', key: '5' },
  { id: 'saved-events', label: 'Planes guardados', icon: 'bookmark', key: '6' },
] as const;

type TabId = (typeof TABS)[number]['id'];

const REFRESH_OPTIONS = [
  { label: 'Off', value: 0 },
  { label: '30s', value: 30_000 },
  { label: '1m', value: 60_000 },
  { label: '5m', value: 300_000 },
];

function DashboardInner() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [refreshTick, setRefreshTick] = useState(0);
  const [refreshInterval, setRefreshInterval] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function navigateTo(tab: string) {
    setActiveTab(tab as TabId);
  }

  function manualRefresh() {
    setRefreshTick((t) => t + 1);
    toast('Actualizado', 'info');
  }

  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(() => setRefreshTick((t) => t + 1), refreshInterval);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [refreshInterval]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (e.key === 'r' || e.key === 'R') { manualRefresh(); return; }
      const tab = TABS.find((t) => t.key === e.key);
      if (tab) setActiveTab(tab.id);
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <header className="border-b border-gray-800 px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs text-gray-500 uppercase tracking-widest">NextPlan</span>
          <span className="text-gray-700">·</span>
          <span className="text-sm font-semibold text-white">Admin</span>
        </div>
        <div className="flex items-center gap-3 ml-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-gray-500">Refresh:</span>
            <div className="flex rounded overflow-hidden border border-gray-700">
              {REFRESH_OPTIONS.map((opt) => (
                <button
                  key={opt.label}
                  onClick={() => setRefreshInterval(opt.value)}
                  className={`text-xs px-2 py-1 transition-colors ${
                    refreshInterval === opt.value
                      ? 'bg-violet-700 text-white'
                      : 'bg-gray-900 text-gray-400 hover:text-white'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <button
              onClick={manualRefresh}
              title="Refrescar (R)"
              className="text-gray-500 hover:text-white transition-colors text-sm"
            >
              <span className="material-symbols-outlined text-[16px]">refresh</span>
            </button>
          </div>
          {user && <span className="text-xs text-gray-500">{user.email}</span>}
          <button
            onClick={handleLogout}
            className="text-xs text-gray-500 hover:text-white transition-colors"
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        <nav className="w-56 border-r border-gray-800 p-4 flex flex-col gap-1 shrink-0">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left ${
                activeTab === tab.id
                  ? 'bg-violet-900/50 text-violet-200'
                  : 'text-gray-400 hover:text-white hover:bg-gray-900'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">{tab.icon}</span>
              <span className="flex-1">{tab.label}</span>
              <span className="text-gray-700 text-xs">{tab.key}</span>
            </button>
          ))}
          <div className="mt-auto pt-4 text-xs text-gray-700 px-3">
            1-6 cambiar tab · R refrescar
          </div>
        </nav>

        <main className="flex-1 p-6 overflow-y-auto">
          <h2 className="text-lg font-bold text-white mb-5">
            {TABS.find((t) => t.id === activeTab)?.label}
          </h2>
          {activeTab === 'overview' && (
            <OverviewTab onNavigate={navigateTo} refreshTick={refreshTick} />
          )}
          {activeTab === 'kpis' && <KPIsTab refreshTick={refreshTick} />}
          {activeTab === 'infrastructure' && <InfrastructureTab refreshTick={refreshTick} />}
          {activeTab === 'events' && <EventsTab />}
          {activeTab === 'analytics' && <AnalyticsTab refreshTick={refreshTick} />}
          {activeTab === 'saved-events' && <SavedEventsTab refreshTick={refreshTick} />}
        </main>
      </div>
    </div>
  );
}

export function DashboardPage() {
  return (
    <ToastProvider>
      <DashboardInner />
    </ToastProvider>
  );
}
