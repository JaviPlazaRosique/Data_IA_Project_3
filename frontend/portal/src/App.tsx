import { lazy, Suspense, useState } from 'react';
import { HashRouter, Link, Routes, Route } from 'react-router-dom';
import { isServerAvailable } from './config';
import ServerOfflineBanner from './components/ServerOfflineBanner';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

function StorageNotice() {
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem('storage_notice_seen') === '1'
  );
  if (dismissed) return null;
  return (
    <div className="fixed bottom-20 md:bottom-0 inset-x-0 z-40 flex items-center justify-between gap-4 bg-surface-container border-t border-outline-variant/20 px-4 py-3 text-xs text-on-surface-variant">
      <span>
        This site uses session storage for authentication only. No tracking cookies.{' '}
        <Link to="/privacy" className="text-primary font-bold hover:underline">Privacy Notice</Link>
      </span>
      <button
        onClick={() => { localStorage.setItem('storage_notice_seen', '1'); setDismissed(true); }}
        className="shrink-0 font-bold text-on-surface hover:text-primary transition-colors px-3 py-1 rounded-full border border-outline-variant/20"
      >
        OK
      </button>
    </div>
  );
}

const DiscoverPage = lazy(() => import('./pages/DiscoverPage'));
const AIPlannerPage = lazy(() => import('./pages/AIPlannerPage'));
const EventDetailsPage = lazy(() => import('./pages/EventDetailsPage'));
const MapPage = lazy(() => import('./pages/MapPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));
const OnboardingPage = lazy(() => import('./pages/OnboardingPage'));

export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        {!isServerAvailable() && <ServerOfflineBanner />}
        <StorageNotice />
        <Suspense fallback={<div className="min-h-screen bg-surface" />}>
          <Routes>
            <Route path="/" element={<DiscoverPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/event/:id" element={<EventDetailsPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/planner"
              element={
                <ProtectedRoute>
                  <AIPlannerPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Suspense>
      </AuthProvider>
    </HashRouter>
  );
}
