import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import SideNav from '../components/layout/SideNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LanguageContext';
import { SectionLabel } from '../components/np/Primitives';
import QuickMatch from '../components/QuickMatch';
import {
  apiUpdateMe,
  apiListSavedEvents,
  apiUnsaveEvent,
  type SavedEventRead,
} from '../api';

const budgetOptions = ['€', '€€', '€€€', '€€€€'];
const favoriteCategories = ['Immersive Art', 'Techno Operas', 'Speakeasies'];

interface NominatimSuggestion {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  address?: {
    city?: string;
    town?: string;
    village?: string;
    municipality?: string;
    country?: string;
  };
}

function shortLabel(s: NominatimSuggestion): string {
  const city =
    s.address?.city ?? s.address?.town ?? s.address?.village ?? s.address?.municipality;
  const country = s.address?.country;
  return [city, country].filter(Boolean).join(', ') || s.display_name;
}

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const { t } = useLang();
  const [activeBudget, setActiveBudget] = useState(user?.preferred_budget ?? '€');
  const [locationDraft, setLocationDraft] = useState(user?.preferred_location ?? '');
  const [locationSuggestions, setLocationSuggestions] = useState<NominatimSuggestion[]>([]);
  const [locationOpen, setLocationOpen] = useState(false);
  const [savedEvents, setSavedEvents] = useState<SavedEventRead[]>([]);

  useEffect(() => {
    apiListSavedEvents()
      .then(setSavedEvents)
      .catch(() => { /* silent */ });
  }, []);

  useEffect(() => {
    setLocationDraft(user?.preferred_location ?? '');
  }, [user?.preferred_location]);

  useEffect(() => {
    const query = locationDraft.trim();
    if (query.length < 2 || query === (user?.preferred_location ?? '')) {
      setLocationSuggestions([]);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&addressdetails=1&accept-language=en`,
        { signal: controller.signal, headers: { 'Accept-Language': 'en' } },
      )
        .then((r) => (r.ok ? r.json() : []))
        .then((data: NominatimSuggestion[]) => {
          setLocationSuggestions(Array.isArray(data) ? data : []);
        })
        .catch(() => { /* aborted or network error */ });
    }, 300);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [locationDraft, user?.preferred_location]);

  async function handleBudgetChange(opt: string) {
    setActiveBudget(opt);
    try {
      const updated = await apiUpdateMe({ preferred_budget: opt });
      setUser(updated);
    } catch { /* silent */ }
  }

  async function selectSuggestion(s: NominatimSuggestion) {
    const label = shortLabel(s);
    setLocationDraft(label);
    setLocationSuggestions([]);
    setLocationOpen(false);
    try {
      const updated = await apiUpdateMe({
        preferred_location: label,
        preferred_location_lat: parseFloat(s.lat),
        preferred_location_lng: parseFloat(s.lon),
      });
      setUser(updated);
    } catch { /* silent */ }
  }

  async function clearLocation() {
    setLocationDraft('');
    setLocationSuggestions([]);
    setLocationOpen(false);
    try {
      const updated = await apiUpdateMe({
        preferred_location: null,
        preferred_location_lat: null,
        preferred_location_lng: null,
      });
      setUser(updated);
    } catch { /* silent */ }
  }

  async function handleUnsave(eventId: string) {
    try {
      await apiUnsaveEvent(eventId);
      setSavedEvents((prev) => prev.filter((e) => e.event_id !== eventId));
    } catch { /* silent */ }
  }

  return (
    <div className="bg-surface text-on-surface min-h-screen">
      <TopNav />
      <SideNav activeItem="Profile" />

      <main className="lg:ml-64 pt-6 pb-24 px-4 md:px-12">
        <div className="max-w-6xl mx-auto">
          {/* Hero Header */}
          <header className="mb-12 relative">
            <div className="absolute -top-20 -left-20 w-96 h-96 bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
              <div className="flex items-center gap-6">
                <div className="relative group">
                  <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-surface-container-high shadow-2xl bg-surface-container-high flex items-center justify-center">
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={user.full_name ?? user?.username} className="w-full h-full object-cover" />
                    ) : (
                      <span className="material-symbols-outlined text-5xl text-on-surface-variant">account_circle</span>
                    )}
                  </div>
                  <div className="absolute bottom-0 right-0 bg-tertiary text-on-tertiary p-1.5 rounded-full shadow-lg border-2 border-surface">
                    <span className="material-symbols-outlined text-sm block">edit</span>
                  </div>
                </div>
                <div>
                  <SectionLabel>{t.profile_title}</SectionLabel>
                  <h1 className="font-serif text-3xl md:text-5xl tracking-tight text-on-surface mb-2 mt-2">
                    {user?.full_name ?? user?.username}
                  </h1>
                  <div className="flex items-center gap-3">
                    <span className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border border-primary/30">
                      {user?.is_verified ? 'Verified Member' : 'Member'}
                    </span>
                    {user?.preferred_location && (
                      <span className="text-on-surface-variant text-sm flex items-center gap-1">
                        <span className="material-symbols-outlined text-base">location_on</span>
                        {user.preferred_location}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <Link
                to="/planner"
                className="bg-primary text-on-primary font-bold px-8 py-3 rounded-full hover:scale-95 active:opacity-80 transition-transform flex items-center gap-2 w-fit"
              >
                <span className="material-symbols-outlined text-xl">bolt</span>
                Surprise Me
              </Link>
            </div>
          </header>

          {/* Quick Match — Tinder-style event swipe */}
          <section className="mb-12">
            <QuickMatch onSaved={(s) => setSavedEvents((prev) => prev.some((e) => e.event_id === s.event_id) ? prev : [s, ...prev])} />
          </section>

          {/* Grid Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left: Preferences */}
            <section className="lg:col-span-4 space-y-8">
              <div className="bg-surface-container-low p-8 rounded-[2rem] relative group">
                <div className="absolute inset-0 rounded-[2rem] overflow-hidden pointer-events-none">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full group-hover:bg-primary/10 transition-colors" />
                </div>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">tune</span>
                  {t.profile_prefs}
                </h2>
                <div className="space-y-6">
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Budget Range</label>
                    <div className="bg-surface-container-lowest p-1 rounded-full flex gap-1">
                      {budgetOptions.map((opt) => (
                        <button
                          key={opt}
                          onClick={() => handleBudgetChange(opt)}
                          className={`flex-1 py-2 text-xs font-bold rounded-full transition-colors ${
                            activeBudget === opt
                              ? 'bg-surface-container-high text-primary'
                              : 'text-on-surface/40 hover:text-on-surface'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Favorite Categories</label>
                    <div className="flex flex-wrap gap-2">
                      {favoriteCategories.map((cat) => (
                        <span key={cat} className="bg-surface-container-high px-4 py-2 rounded-xl text-sm font-medium border border-outline-variant/10">
                          {cat}
                        </span>
                      ))}
                      <button className="bg-primary/10 text-primary border border-primary/20 px-3 py-2 rounded-xl text-sm">
                        <span className="material-symbols-outlined text-base align-middle">add</span>
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Preferred Location</label>
                    <div className="relative">
                      <div className="bg-surface-container-lowest flex items-center gap-3 p-3 rounded-xl">
                        <span className="material-symbols-outlined text-secondary">location_on</span>
                        <input
                          type="text"
                          value={locationDraft}
                          onChange={(e) => { setLocationDraft(e.target.value); setLocationOpen(true); }}
                          onFocus={() => setLocationOpen(true)}
                          onBlur={() => setTimeout(() => setLocationOpen(false), 150)}
                          placeholder="Type a city, then pick from the list…"
                          className="flex-1 bg-transparent text-sm font-medium focus:outline-none placeholder:text-on-surface-variant/40"
                        />
                        {user?.preferred_location && (
                          <button
                            onMouseDown={(e) => { e.preventDefault(); clearLocation(); }}
                            className="material-symbols-outlined text-on-surface-variant text-sm cursor-pointer hover:text-error transition-colors"
                            title="Clear preferred location"
                          >close</button>
                        )}
                      </div>
                      {locationOpen && locationSuggestions.length > 0 && (
                        <ul className="absolute z-10 top-full left-0 right-0 mt-1 bg-surface-container-high rounded-xl border border-outline-variant/10 shadow-xl overflow-hidden">
                          {locationSuggestions.map((s) => (
                            <li key={s.place_id}>
                              <button
                                onMouseDown={(e) => { e.preventDefault(); selectSuggestion(s); }}
                                className="w-full text-left px-4 py-2.5 text-sm hover:bg-surface-variant/40 transition-colors flex items-start gap-2"
                              >
                                <span className="material-symbols-outlined text-secondary/70 text-base mt-0.5">location_on</span>
                                <span className="flex-1">
                                  <span className="block font-medium">{shortLabel(s)}</span>
                                  <span className="block text-[11px] text-on-surface-variant/60 truncate">{s.display_name}</span>
                                </span>
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Curator Insight */}
              <div className="glass-panel p-8 rounded-[2rem]">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-tertiary">auto_awesome</span>
                  Curator Insight
                </h2>
                <p className="text-on-surface-variant text-sm leading-relaxed mb-6">
                  "Elena, your recent visits suggest a growing interest in{' '}
                  <span className="text-primary">Neon-Retroism</span>. We've adjusted your dashboard to prioritize high-contrast sensory experiences."
                </p>
                <div className="h-1 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary w-2/3" />
                </div>
                <p className="text-[10px] text-on-surface-variant mt-2 text-right uppercase tracking-tighter">
                  Profile Alignment: 67% Complete
                </p>
              </div>
            </section>

            {/* Right: History & Saved */}
            <section className="lg:col-span-8 space-y-12">
              {/* Saved Events */}
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-extrabold tracking-tight flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>bookmark</span>
                    {t.profile_saved}
                  </h2>
                  <a href="#" className="text-primary text-sm font-bold hover:underline">View All</a>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {savedEvents.length === 0 && (
                    <p className="text-on-surface-variant/50 text-sm italic col-span-2">No saved events yet.</p>
                  )}
                  {savedEvents.map((event) => (
                    <div key={event.id} className="bg-surface-container-high rounded-[1.5rem] overflow-hidden group hover:translate-y-[-4px] transition-transform duration-300">
                      <div className="h-48 w-full overflow-hidden relative">
                        {event.event_image_url ? (
                          <img
                            src={event.event_image_url}
                            alt={event.event_title ?? event.event_id}
                            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                          />
                        ) : (
                          <div className="w-full h-full bg-surface-container-highest flex items-center justify-center">
                            <span className="material-symbols-outlined text-4xl text-on-surface-variant/30">event</span>
                          </div>
                        )}
                        {event.event_date && (
                          <div className="absolute top-4 left-4 bg-surface/80 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                            {event.event_date}
                          </div>
                        )}
                        <button
                          onClick={() => handleUnsave(event.event_id)}
                          className="absolute top-4 right-4 w-8 h-8 bg-surface/80 backdrop-blur-md rounded-full flex items-center justify-center text-on-surface-variant hover:text-error transition-colors"
                          title="Remove bookmark"
                        >
                          <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                      </div>
                      <div className="p-6">
                        <h3 className="text-lg font-bold mb-1">{event.event_title ?? event.event_id}</h3>
                        <p className="text-on-surface-variant text-xs mb-4">
                          {[event.event_venue, event.event_time].filter(Boolean).join(' • ')}
                        </p>
                        <button className="w-full border border-outline-variant/30 py-2.5 rounded-full text-xs font-bold hover:bg-on-surface hover:text-surface transition-colors">
                          Book Now
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </section>
          </div>
        </div>
      </main>

      {/* AI Chat Float */}
      <div className="fixed bottom-20 md:bottom-8 right-8 z-[60]">
        <Link
          to="/planner"
          className="glass-panel w-16 h-16 rounded-2xl flex items-center justify-center text-primary shadow-2xl hover:scale-110 active:scale-95 transition-all relative"
        >
          <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-tertiary rounded-full animate-pulse border-2 border-surface" />
        </Link>
      </div>

      <BottomNav />
      <Footer />
    </div>
  );
}
