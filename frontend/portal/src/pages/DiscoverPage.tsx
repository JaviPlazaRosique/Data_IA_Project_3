import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { categories, heroEvent } from '../data/mockData';
import { apiListEvents, type EventCatalogItem } from '../api';
import { useLang } from '../context/LanguageContext';
import { SectionLabel } from '../components/np/Primitives';

const EVENT_IMAGE_FALLBACK = 'https://picsum.photos/seed/event-placeholder/600/340';

type EventGroup = { key: string; items: EventCatalogItem[] };

function groupEvents(events: EventCatalogItem[]): EventGroup[] {
  const map = new Map<string, EventGroup>();
  for (const ev of events) {
    const key = [
      (ev.nombre ?? '').trim().toLowerCase(),
      (ev.recinto_nombre ?? '').trim().toLowerCase(),
      (ev.ciudad ?? '').trim().toLowerCase(),
    ].join('|');
    const existing = map.get(key);
    if (existing) existing.items.push(ev);
    else map.set(key, { key, items: [ev] });
  }
  for (const g of map.values()) {
    g.items.sort((a, b) => {
      const av = a.fecha_utc ?? `${a.fecha ?? ''} ${a.hora ?? ''}`;
      const bv = b.fecha_utc ?? `${b.fecha ?? ''} ${b.hora ?? ''}`;
      return av.localeCompare(bv);
    });
  }
  return Array.from(map.values());
}

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

export default function DiscoverPage() {
  const { t, lang } = useLang();
  const [aiDismissed, setAiDismissed] = useState(false);
  const [events, setEvents] = useState<EventCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiListEvents({ limit: 10 })
      .then((data) => setEvents(data))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load events'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <TopNav />

      <main className="min-h-screen">
        {/* Hero Section */}
        <section className="relative pt-12 pb-24 px-4 md:px-8 hero-gradient">
          <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-8 md:gap-16">
            <div className="flex-1 space-y-8">
              <div className="space-y-4">
                <SectionLabel>Madrid · {t.tonight}</SectionLabel>
                <h1 className="font-serif text-5xl md:text-7xl lg:text-8xl leading-[0.95] tracking-tight text-on-surface">
                  {lang === 'es' ? (
                    <>
                      Planes para
                      <br />
                      <span className="italic text-primary">esta noche</span>,<br />
                      afinados al clima.
                    </>
                  ) : (
                    <>
                      Plans for
                      <br />
                      <span className="italic text-primary">tonight</span>,<br />
                      tuned to the weather.
                    </>
                  )}
                </h1>
                <p className="text-on-surface-variant text-lg max-w-md font-body leading-relaxed">
                  {t.brand_tagline}
                </p>
              </div>
              <div className="flex flex-wrap gap-4 pt-4">
                <Link
                  to="/planner"
                  className="bg-tertiary text-on-tertiary-fixed px-8 py-4 rounded-full font-bold flex items-center gap-2 hover:scale-95 transition-transform"
                >
                  <span className="material-symbols-outlined">auto_awesome</span>
                  {t.cta_plan}
                </Link>
                <Link
                  to="/map"
                  className="bg-surface-container-high text-on-surface px-8 py-4 rounded-full font-bold border border-outline-variant/20 hover:bg-surface-container-highest transition-colors"
                >
                  {t.cta_explore}
                </Link>
              </div>
            </div>

            <div className="flex-1 w-full relative">
              <div className="aspect-[4/5] rounded-[2rem] overflow-hidden bg-surface-container-low shadow-2xl relative">
                <img
                  src={heroEvent.imageUrl}
                  alt="Live event"
                  className="w-full h-full object-cover opacity-80"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-surface to-transparent opacity-60" />
                <div className="absolute bottom-8 left-8 right-8 glass-effect p-6 rounded-2xl">
                  <div className="flex justify-between items-end">
                    <div>
                      <h3 className="text-xl font-bold font-headline">{heroEvent.title}</h3>
                      <p className="text-sm text-on-surface/70 font-label">{heroEvent.subtitle}</p>
                    </div>
                    <div className="bg-primary/20 px-3 py-1 rounded-full text-primary text-xs font-bold flex items-center gap-1">
                      <span className="material-symbols-outlined text-sm">wb_sunny</span>
                      {heroEvent.temp}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Categories Bento Grid */}
        <section className="py-24 px-4 md:px-8 bg-surface-container-low">
          <div className="max-w-7xl mx-auto space-y-12">
            <div className="flex flex-col md:flex-row justify-between items-end gap-4">
              <div className="space-y-2">
                <h2 className="text-2xl md:text-4xl font-bold font-headline tracking-tight">Sonic &amp; Visual Pillars</h2>
                <p className="text-on-surface-variant font-body">Categorized by the frequency of your curiosity.</p>
              </div>
              <div className="bg-surface-container-lowest p-1 rounded-full border border-outline-variant/15">
                <div className="flex gap-2 p-1">
                  <button className="bg-surface-container-high px-4 py-2 rounded-full text-xs font-bold text-primary">Grid</button>
                  <button className="px-4 py-2 rounded-full text-xs font-bold text-on-surface/50 hover:text-on-surface transition-colors">List</button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 md:h-[600px]">
              {categories.slice(0, 5).map((cat, i) => (
                <div
                  key={cat.id}
                  className={`${i === 0 || i === 3 ? 'md:col-span-2' : ''} group relative rounded-3xl overflow-hidden bg-surface-container cursor-pointer min-h-[240px]`}
                >
                  <img
                    src={cat.imageUrl}
                    alt={cat.label}
                    className="absolute inset-0 w-full h-full object-cover opacity-50 group-hover:scale-110 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-tr from-surface via-transparent to-transparent" />
                  <div className="absolute bottom-8 left-8">
                    <span className={`${cat.color} font-bold text-xs uppercase tracking-widest font-label`}>{cat.vibe}</span>
                    <h3 className="text-3xl font-black font-headline">{cat.label}</h3>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Curated Events */}
        <section className="py-24 px-4 md:px-8">
          <div className="max-w-7xl mx-auto space-y-12">
            <div className="flex items-center gap-4">
              <h2 className="font-serif text-3xl md:text-4xl tracking-tight">{t.curated}</h2>
              <div className="h-[2px] flex-1 bg-outline-variant/20" />
            </div>
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="bg-surface-container-high rounded-3xl overflow-hidden animate-pulse"
                  >
                    <div className="aspect-video bg-surface-variant/30" />
                    <div className="p-8 space-y-4">
                      <div className="h-6 bg-surface-variant/30 rounded w-3/4" />
                      <div className="h-4 bg-surface-variant/30 rounded w-1/2" />
                      <div className="h-10 bg-surface-variant/30 rounded-full" />
                    </div>
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="bg-surface-container-high rounded-3xl p-12 text-center text-on-surface-variant">
                No pudimos cargar los eventos. Intenta recargar la página.
              </div>
            ) : events.length === 0 ? (
              <div className="bg-surface-container-high rounded-3xl p-12 text-center text-on-surface-variant">
                No hay eventos disponibles todavía. Vuelve pronto.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {groupEvents(events).map((group) => {
                  const first = group.items[0];
                  const title = first.nombre ?? 'Evento';
                  const venue = [first.recinto_nombre, first.ciudad].filter(Boolean).join(' • ');
                  const image = first.imagen_evento ?? first.artista_imagen ?? EVENT_IMAGE_FALLBACK;
                  const tags = [first.segmento, first.genero].filter(
                    (t): t is string => !!t,
                  );
                  const schedule = buildScheduleEntries(group.items);
                  return (
                    <div
                      key={group.key}
                      className="bg-surface-container-high rounded-3xl overflow-hidden group"
                    >
                      <div className="aspect-video relative overflow-hidden">
                        <img
                          src={image}
                          alt={title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      </div>
                      <div className="p-8 space-y-4">
                        <div>
                          <h4 className="text-2xl font-bold font-headline">{title}</h4>
                          {venue && (
                            <p className="text-on-surface-variant font-body">{venue}</p>
                          )}
                        </div>
                        {schedule.length > 0 && (
                          <ul className="space-y-1">
                            {schedule.map((entry) => (
                              <li
                                key={entry.date}
                                className="text-sm text-on-surface-variant/80 font-label flex items-start gap-2"
                              >
                                <span className="material-symbols-outlined text-sm">event</span>
                                <span className="flex flex-wrap items-center gap-x-1">
                                  <span>{entry.date}</span>
                                  {entry.slots.length > 0 && <span>·</span>}
                                  {entry.slots.map((slot, idx) => (
                                    <span key={slot.time}>
                                      {slot.url ? (
                                        <a
                                          href={slot.url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          onClick={(e) => e.stopPropagation()}
                                          className="text-primary hover:underline"
                                        >
                                          {slot.time}
                                        </a>
                                      ) : (
                                        <span>{slot.time}</span>
                                      )}
                                      {idx < entry.slots.length - 1 && ', '}
                                    </span>
                                  ))}
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                        {tags.length > 0 && (
                          <div className="flex gap-2 flex-wrap">
                            {tags.map((tag) => (
                              <span
                                key={tag}
                                className="bg-surface-variant px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase opacity-80"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        <Link
                          to={`/event/${first.id}`}
                          className="block w-full py-4 rounded-full border border-outline-variant/20 font-bold text-center hover:bg-primary hover:text-on-primary transition-all"
                        >
                          {t.see_details}
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      </main>

      {/* AI Assistant Float */}
      {!aiDismissed && (
        <div className="fixed bottom-12 right-12 z-[100] hidden md:block">
          <div className="glass-effect rounded-3xl p-6 w-80 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-on-primary">
                <span className="material-symbols-outlined">smart_toy</span>
              </div>
              <div>
                <p className="text-xs font-bold text-primary font-label">Curator AI</p>
                <p className="text-[10px] text-on-surface/60 font-body">Finding your perfect match...</p>
              </div>
            </div>
            <div className="bg-surface-container-lowest p-4 rounded-2xl">
              <p className="text-sm font-body leading-relaxed text-on-surface/90">
                "Based on your love for deep house and clear skies, I've highlighted{' '}
                <span className="text-secondary">Rooftop Drift</span> for tonight."
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setAiDismissed(true)}
                className="flex-1 bg-surface-container-high py-2 rounded-xl text-xs font-bold hover:bg-surface-container-highest transition-colors"
              >
                Dismiss
              </button>
              <Link
                to="/planner"
                className="flex-1 bg-primary py-2 rounded-xl text-xs font-bold text-on-primary text-center hover:opacity-90 transition-opacity"
              >
                Tell Me More
              </Link>
            </div>
          </div>
        </div>
      )}

      <BottomNav />
      <Footer />
    </div>
  );
}
