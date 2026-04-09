import { lazy, Suspense } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';

const DiscoverPage = lazy(() => import('./pages/DiscoverPage'));
const AIPlannerPage = lazy(() => import('./pages/AIPlannerPage'));
const EventDetailsPage = lazy(() => import('./pages/EventDetailsPage'));
const MapPage = lazy(() => import('./pages/MapPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));

export default function App() {
  return (
    <HashRouter>
      <Suspense fallback={<div className="min-h-screen bg-surface" />}>
        <Routes>
          <Route path="/" element={<DiscoverPage />} />
          <Route path="/planner" element={<AIPlannerPage />} />
          <Route path="/event/:id" element={<EventDetailsPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Routes>
      </Suspense>
    </HashRouter>
  );
}