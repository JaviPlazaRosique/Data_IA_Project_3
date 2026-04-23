import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import EventCalendar from '../components/event/EventCalendar';
import {
  apiGetEvent,
  apiListEvents,
  type EventCatalogItem,
} from '../api';

// Seeded images specific to this event
const heroImg = 'https://picsum.photos/seed/festival-night/1400/700';
const mapImg = 'https://picsum.photos/seed/city-map/800/500';

type ScheduleEntry = {
  date: string;
  slots: { time: string; url: string | null }[];
};

function buildScheduleEntries(items: EventCatalogItem[]): ScheduleEntry[] {
  const byDate = new Map<string, Map<string, string | null>>();
  for (const ev of items) {
    const date = (ev.fecha ?? '').trim() || '—';
    const time = (ev.hora ?? '').trim();
    if (!date && !time) continue;
    if (!byDate.has(date)) byDate.set(date, new Map());
    if (time && !byDate.get(date)!.has(time)) {
      byDate.get(date)!.set(time, ev.url ?? null);
    }
  }
  return Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, times]) => ({
      date,
      slots: Array.from(times.entries())
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([time, url]) => ({ time, url })),
    }));
}

const weatherMetrics = [
  { label: 'Precipitation', value: '2%' },
  { label: 'Humidity', value: '45%' },
  { label: 'Wind', value: '12 km/h' },
  { label: 'UV Index', value: '0 Low' },
];

export default function EventDetailsPage() {
  const { id: routeId } = useParams<{ id: string }>();
  const [event, setEvent] = useState<EventCatalogItem | null>(null);
  const [occurrences, setOccurrences] = useState<EventCatalogItem[]>([]);
  const [shareOpen, setShareOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const shareData = useMemo(() => {
    if (!event) return null;
    const title = event.nombre ?? 'Evento';
    const venue = [event.recinto_nombre, event.ciudad].filter(Boolean).join(' • ');
    const url = `${window.location.origin}/index.html#/event/${event.id}`;
    const text = venue ? `${title} — ${venue}` : title;
    return { title, text, url };
  }, [event]);

  const copyLink = useCallback(async () => {
    if (!shareData) return;
    try {
      await navigator.clipboard.writeText(shareData.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* ignore */ }
  }, [shareData]);

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

  const schedule = buildScheduleEntries(occurrences);

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
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">calendar_month</span>
                    <span>
                      {schedule.length} {schedule.length === 1 ? 'date' : 'dates'} available
                    </span>
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

          {/* Calendar Panel */}
          <div className="md:col-span-4">
            {schedule.length > 0 ? (
              <EventCalendar entries={schedule} />
            ) : (
              <div className="bg-surface-container-low rounded-2xl p-6 border border-outline-variant/20 h-full flex flex-col items-center justify-center text-center gap-2">
                <span className="material-symbols-outlined text-primary text-4xl">calendar_month</span>
                <div className="font-bold font-headline">{event?.fecha ?? 'TBA'}</div>
                <div className="text-sm text-on-surface-variant">{event?.hora ?? '—'}</div>
              </div>
            )}
          </div>

          {/* Map Section */}
          <div className="md:col-span-12 lg:col-span-8 bg-surface-container-low rounded-xl overflow-hidden min-h-[400px] relative">
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

          {/* Booking Panel (moved next to map) */}
          <div className="md:col-span-12 lg:col-span-4 flex flex-col gap-6">
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

              {/* Share */}
              <div className="relative">
                <button
                  onClick={() => setShareOpen((v) => !v)}
                  className="w-full flex items-center justify-between bg-surface-container-highest text-on-surface py-3 px-5 rounded-full font-bold hover:bg-surface-variant transition-colors group"
                  aria-label="Share"
                  aria-expanded={shareOpen}
                >
                  <span className="flex items-center gap-3">
                    <span className="material-symbols-outlined">share</span>
                    Compartir
                  </span>
                  <span className="material-symbols-outlined">
                    {shareOpen ? 'expand_less' : 'expand_more'}
                  </span>
                </button>
                {shareOpen && shareData && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShareOpen(false)} />
                    <div className="absolute top-full mt-3 left-0 right-0 z-50 bg-surface-container-highest border border-outline-variant/20 rounded-2xl shadow-2xl p-3">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant px-2 pb-2">
                        Share event
                      </p>
                      <div className="grid grid-cols-4 gap-2">
                        <a
                          href={`https://wa.me/?text=${encodeURIComponent(`${shareData.text} ${shareData.url}`)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={() => setShareOpen(false)}
                          className="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-surface-container transition-colors"
                          title="WhatsApp"
                        >
                          <div className="w-10 h-10 rounded-full bg-[#25D366] flex items-center justify-center text-white font-bold">W</div>
                          <span className="text-[10px]">WhatsApp</span>
                        </a>
                        <a
                          href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareData.url)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={() => setShareOpen(false)}
                          className="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-surface-container transition-colors"
                          title="Facebook"
                        >
                          <div className="w-10 h-10 rounded-full bg-[#1877F2] flex items-center justify-center text-white font-bold">f</div>
                          <span className="text-[10px]">Facebook</span>
                        </a>
                        <a
                          href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareData.text)}&url=${encodeURIComponent(shareData.url)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={() => setShareOpen(false)}
                          className="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-surface-container transition-colors"
                          title="X / Twitter"
                        >
                          <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center text-white font-bold">X</div>
                          <span className="text-[10px]">X</span>
                        </a>
                        <a
                          href={`https://t.me/share/url?url=${encodeURIComponent(shareData.url)}&text=${encodeURIComponent(shareData.text)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={() => setShareOpen(false)}
                          className="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-surface-container transition-colors"
                          title="Telegram"
                        >
                          <div className="w-10 h-10 rounded-full bg-[#0088cc] flex items-center justify-center text-white font-bold">T</div>
                          <span className="text-[10px]">Telegram</span>
                        </a>
                      </div>
                      <button
                        onClick={copyLink}
                        className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-surface-container hover:bg-surface-container-low text-sm font-medium transition-colors"
                      >
                        <span className="material-symbols-outlined text-base">
                          {copied ? 'check' : 'link'}
                        </span>
                        {copied ? 'Link copiado' : 'Copiar link'}
                      </button>
                    </div>
                  </>
                )}
              </div>
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
