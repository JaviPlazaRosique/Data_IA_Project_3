import { lazy, Suspense } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { isServerAvailable } from './config';
import ServerOfflineBanner from './components/ServerOfflineBanner';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

const DiscoverPage = lazy(() => import('./pages/DiscoverPage'));
const AIPlannerPage = lazy(() => import('./pages/AIPlannerPage'));
const EventDetailsPage = lazy(() => import('./pages/EventDetailsPage'));
const MapPage = lazy(() => import('./pages/MapPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));

export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        {!isServerAvailable() && <ServerOfflineBanner />}
        <Suspense fallback={<div className="min-h-screen bg-surface" />}>
          <Routes>
            <Route path="/" element={<DiscoverPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/event/:id" element={<EventDetailsPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
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
