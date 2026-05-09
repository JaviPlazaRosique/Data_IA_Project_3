import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { OverviewTab } from '../components/tabs/OverviewTab';
import { UsersTab } from '../components/tabs/UsersTab';
import { EventsTab } from '../components/tabs/EventsTab';
import { AnalyticsTab } from '../components/tabs/AnalyticsTab';
import { ArchitectureTab } from '../components/tabs/ArchitectureTab';

const TABS = [
  { id: 'overview', label: 'Overview', icon: 'dashboard' },
  { id: 'users', label: 'Users', icon: 'group' },
  { id: 'events', label: 'Events', icon: 'event' },
  { id: 'analytics', label: 'Analytics', icon: 'bar_chart' },
  { id: 'architecture', label: 'Architecture', icon: 'hub' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500 uppercase tracking-widest">The Electric Curator</span>
          <span className="text-gray-700">·</span>
          <span className="text-sm font-semibold text-white">Admin</span>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-xs text-gray-500">{user.email}</span>
          )}
          <button
            onClick={handleLogout}
            className="text-xs text-gray-500 hover:text-white transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <nav className="w-52 border-r border-gray-800 p-4 flex flex-col gap-1 shrink-0">
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
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <main className="flex-1 p-6 overflow-y-auto">
          <h2 className="text-lg font-bold text-white mb-5">
            {TABS.find((t) => t.id === activeTab)?.label}
          </h2>
          {activeTab === 'overview' && <OverviewTab />}
          {activeTab === 'users' && <UsersTab />}
          {activeTab === 'events' && <EventsTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
          {activeTab === 'architecture' && <ArchitectureTab />}
        </main>
      </div>
    </div>
  );
}
