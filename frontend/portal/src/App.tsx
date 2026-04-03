import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DiscoverPage from './pages/DiscoverPage';
import AIPlannerPage from './pages/AIPlannerPage';
import EventDetailsPage from './pages/EventDetailsPage';
import MapPage from './pages/MapPage';
import ProfilePage from './pages/ProfilePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DiscoverPage />} />
        <Route path="/planner" element={<AIPlannerPage />} />
        <Route path="/event/:id" element={<EventDetailsPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
    </BrowserRouter>
  );
}
