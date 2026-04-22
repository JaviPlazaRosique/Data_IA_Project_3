import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { useAuth } from '../context/AuthContext';
import {
  apiListEventReviews,
  apiCreateReview,
  apiUpdateReview,
  apiGetEvent,
  apiListEvents,
  type EventReviewRead,
  type EventCatalogItem,
} from '../api';

// Seeded images specific to this event
const heroImg = 'https://picsum.photos/seed/festival-night/1400/700';
const mapImg = 'https://picsum.photos/seed/city-map/800/500';
const reviewerAvatarImg = 'https://picsum.photos/seed/avatar-club/80/80';

function buildSchedule(items: EventCatalogItem[]): string[] {
  const byDate = new Map<string, Set<string>>();
  for (const ev of items) {
    const date = (ev.fecha ?? '').trim();
    const time = (ev.hora ?? '').trim();
    if (!date && !time) continue;
    const key = date || '—';
    if (!byDate.has(key)) byDate.set(key, new Set());
    if (time) byDate.get(key)!.add(time);
  }
  return Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, times]) => {
      const hours = Array.from(times).sort();
      return hours.length ? `${date} · ${hours.join(', ')}` : date;
    });
}

const weatherMetrics = [
  { label: 'Precipitation', value: '2%' },
  { label: 'Humidity', value: '45%' },
  { label: 'Wind', value: '12 km/h' },
  { label: 'UV Index', value: '0 Low' },
];

export default function EventDetailsPage() {
  const { user } = useAuth();
  const { id: routeId } = useParams<{ id: string }>();
  const EVENT_ID = routeId ?? 'midnight-pulse-festival';
  const [rating, setRating] = useState(4);
  const [reviewText, setReviewText] = useState('');
  const [apiReviews, setApiReviews] = useState<EventReviewRead[]>([]);
  const [myReview, setMyReview] = useState<EventReviewRead | null>(null);
  const [event, setEvent] = useState<EventCatalogItem | null>(null);
  const [occurrences, setOccurrences] = useState<EventCatalogItem[]>([]);

  useEffect(() => {
    apiListEventReviews(EVENT_ID).then((data) => {
      setApiReviews(data);
      const mine = data.find((r) => r.user_id === user?.id) ?? null;
      setMyReview(mine);
      if (mine) {
        setRating(mine.rating);
        setReviewText(mine.review_text ?? '');
      }
    }).catch(() => {});
  }, [user, EVENT_ID]);

  useEffect(() => {
    if (!routeId) return;
    let cancelled = false;
    apiGetEvent(routeId)
      .then(async (ev) => {
        if (cancelled) return;
        setEvent(ev);
        try {
          const all = await apiListEvents({ limit: 500 });
          if (cancelled) return;
          const keyOf = (x: EventCatalogItem) =>
            [
              (x.nombre ?? '').trim().toLowerCase(),
              (x.recinto_nombre ?? '').trim().toLowerCase(),
              (x.ciudad ?? '').trim().toLowerCase(),
            ].join('|');
          const target = keyOf(ev);
          const matches = all.filter((x) => keyOf(x) === target);
          matches.sort((a, b) => {
            const av = a.fecha_utc ?? `${a.fecha ?? ''} ${a.hora ?? ''}`;
            const bv = b.fecha_utc ?? `${b.fecha ?? ''} ${b.hora ?? ''}`;
            return av.localeCompare(bv);
          });
          setOccurrences(matches.length ? matches : [ev]);
        } catch {
          setOccurrences([ev]);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [routeId]);

  const schedule = buildSchedule(occurrences);

  async function handleSubmitReview() {
    if (!user) return;
    try {
      if (myReview) {
        const updated = await apiUpdateReview(myReview.id, { rating, review_text: reviewText || null });
        setMyReview(updated);
        setApiReviews((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      } else {
        const created = await apiCreateReview(EVENT_ID, { rating, review_text: reviewText || null });
        setMyReview(created);
        setApiReviews((prev) => [created, ...prev]);
      }
    } catch { /* silent */ }
  }

  return (
    <div className="bg-surface text-on-surface min-h-screen">
      <TopNav />

      <main className="relative min-h-screen">
        {/* Hero */}
        <section className="relative h-[60vh] w-full overflow-hidden">
          <img src={event?.imagen_evento ?? event?.artista_imagen ?? heroImg} alt={event?.nombre ?? 'Event'} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/40 to-transparent" />
          <div className="absolute bottom-0 left-0 w-full px-4 md:px-8 pb-12">
            <div className="max-w-7xl mx-auto flex flex-col items-start gap-4">
              <span className="bg-tertiary text-on-tertiary px-4 py-1 rounded-full text-xs font-bold font-label uppercase tracking-wider">
                Live Tonight
              </span>
              <h1 className="text-4xl sm:text-6xl md:text-8xl font-black font-headline tracking-tighter text-on-surface leading-none">
                {event?.nombre ?? 'Midnight Pulse Festival'}
              </h1>
              <div className="flex flex-wrap items-start gap-6 mt-4 text-on-surface-variant font-label text-sm">
                {schedule.length > 0 ? (
                  <div className="flex items-start gap-2">
                    <span className="material-symbols-outlined text-primary">calendar_month</span>
                    <ul className="space-y-1">
                      {schedule.map((line) => (
                        <li key={line}>{line}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-primary">calendar_month</span>
                      {event?.fecha ?? '—'}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-primary">schedule</span>
                      {event?.hora ?? '—'}
                    </div>
                  </>
                )}
                {(event?.recinto_nombre || event?.ciudad) && (
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">location_on</span>
                    {[event?.recinto_nombre, event?.ciudad].filter(Boolean).join(' • ')}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Bento Grid */}
        <section className="max-w-7xl mx-auto px-4 md:px-8 -mt-10 relative z-10 grid grid-cols-1 md:grid-cols-12 gap-6 pb-24">
          {/* Weather Panel */}
          <div
            className="md:col-span-8 glass-panel rounded-xl p-8 border border-outline-variant/20 overflow-hidden relative"
            style={{ background: 'linear-gradient(135deg, rgba(182,160,255,0.15) 0%, rgba(169,143,255,0.15) 100%)' }}
          >
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
              <div>
                <h2 className="text-2xl font-bold font-headline mb-1">Atmospheric Forecast</h2>
                <p className="text-on-surface-variant font-label text-sm">Real-time data powered by Open-Meteo</p>
              </div>
              <div className="flex items-center gap-4 bg-surface-container-lowest/50 p-4 rounded-xl">
                <span className="material-symbols-outlined text-secondary" style={{ fontSize: '3rem' }}>partly_cloudy_night</span>
                <div>
                  <div className="text-4xl font-black font-headline">18°C</div>
                  <div className="text-sm font-label text-on-surface-variant">Clear Skies</div>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              {weatherMetrics.map((m) => (
                <div key={m.label} className="bg-surface-container-low p-4 rounded-lg flex flex-col gap-1">
                  <span className="text-xs text-on-surface-variant uppercase font-bold tracking-widest">{m.label}</span>
                  <span className="text-lg font-bold">{m.value}</span>
                </div>
              ))}
            </div>
            <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl" />
          </div>

          {/* Booking Panel */}
          <div className="md:col-span-4 flex flex-col gap-6">
            <div className="bg-surface-container-high p-8 rounded-xl flex flex-col gap-6 border-l-4 border-tertiary shadow-xl">
              <h3 className="text-xl font-bold font-headline">Secure Your Entry</h3>
              <p className="text-sm text-on-surface-variant font-label leading-relaxed">
                Experience the pulse. Choose your preferred platform for guaranteed entry.
              </p>
              {event?.url ? (
                <a
                  href={event.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between bg-on-surface text-surface py-3 px-5 rounded-full font-bold hover:bg-tertiary transition-colors group"
                >
                  <span className="flex items-center gap-3">
                    <span className="material-symbols-outlined">confirmation_number</span>
                    Entradas
                  </span>
                  <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">open_in_new</span>
                </a>
              ) : (
                <button
                  disabled
                  className="flex items-center justify-between bg-surface-container-highest text-on-surface/50 py-3 px-5 rounded-full font-bold cursor-not-allowed"
                >
                  <span className="flex items-center gap-3">
                    <span className="material-symbols-outlined">confirmation_number</span>
                    Entradas no disponibles
                  </span>
                </button>
              )}
            </div>
            <div className="bg-surface-container rounded-xl p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                <span className="material-symbols-outlined">electric_bolt</span>
              </div>
              <div>
                <div className="text-sm font-bold">VIP Access</div>
                <div className="text-xs text-on-surface-variant">Includes backstage tour &amp; lounge</div>
              </div>
            </div>
          </div>

          {/* Map Section */}
          <div className="md:col-span-12 lg:col-span-7 bg-surface-container-low rounded-xl overflow-hidden min-h-[400px] relative">
            <div className="absolute top-6 left-6 z-10 glass-panel p-4 rounded-xl border border-outline-variant/20 max-w-xs">
              <h4 className="font-bold text-lg font-headline mb-1">Neon Valley Arena</h4>
              <p className="text-xs text-on-surface-variant font-label mb-3">404 Digital Avenue, Synth City, SC 90210</p>
              <button className="w-full bg-secondary text-on-secondary py-2 rounded-lg text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-2">
                <span className="material-symbols-outlined text-sm">directions</span>
                Get Directions
              </button>
            </div>
            <img
              src={mapImg}
              alt="Event location map"
              className="w-full h-full object-cover grayscale brightness-50 contrast-125 min-h-[400px]"
            />
            <div className="absolute inset-0 bg-primary/5 mix-blend-overlay" />
          </div>

          {/* Community Echo */}
          <div className="md:col-span-12 lg:col-span-5 bg-surface-container-highest rounded-xl p-8 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold font-headline">Community Echo</h3>
                <span className="bg-surface-container-lowest text-primary text-[10px] font-bold px-2 py-1 rounded">VIBE CHECK</span>
              </div>
              <div className="flex gap-2 mb-8">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setRating(star)}
                    className={`material-symbols-outlined ${star <= rating ? 'text-tertiary' : 'text-on-surface-variant'}`}
                    style={star <= rating ? { fontVariationSettings: "'FILL' 1" } : {}}
                  >
                    star
                  </button>
                ))}
              </div>
              <div className="space-y-4">
                {apiReviews.length === 0 && (
                  <p className="text-on-surface-variant/50 text-sm italic">No community reviews yet.</p>
                )}
                {apiReviews.map((review) => (
                  <div key={review.id} className="bg-surface-container-low/50 p-4 rounded-xl border border-outline-variant/10">
                    <div className="flex gap-1 text-tertiary mb-2">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <span
                          key={star}
                          className="material-symbols-outlined text-sm"
                          style={star <= review.rating ? { fontVariationSettings: "'FILL' 1" } : {}}
                        >
                          star
                        </span>
                      ))}
                    </div>
                    {review.review_text && (
                      <p className="text-sm font-label italic text-on-surface-variant mb-3">"{review.review_text}"</p>
                    )}
                    <div className="flex items-center gap-3">
                      <img src={reviewerAvatarImg} alt="reviewer" className="w-8 h-8 rounded-full object-cover border border-secondary/20" />
                      <span className="text-xs font-bold">{review.user_id === user?.id ? 'You' : `@user_${review.user_id.slice(0, 6)}`}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-8">
              <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-3 block">
                {myReview ? 'Update your review' : 'Rate this experience'}
              </label>
              <div className="flex gap-4">
                <input
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  className="flex-1 bg-surface-container-lowest border-none rounded-full px-6 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary text-on-surface placeholder:text-on-surface-variant/50"
                  placeholder="Share your pulse..."
                />
                <button
                  onClick={handleSubmitReview}
                  className="w-12 h-12 bg-primary text-on-primary rounded-full flex items-center justify-center hover:opacity-90 transition-opacity"
                >
                  <span className="material-symbols-outlined">send</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Link
        to="/planner"
        className="fixed bottom-24 md:bottom-8 right-8 w-16 h-16 bg-primary rounded-full shadow-2xl flex items-center justify-center text-on-primary z-50 hover:scale-105 transition-transform active:scale-95"
      >
        <span className="material-symbols-outlined">smart_toy</span>
      </Link>

      <BottomNav />
      <Footer />
    </div>
  );
}
