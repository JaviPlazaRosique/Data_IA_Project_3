import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import SideNav from '../components/layout/SideNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { apiListEvents, apiSaveEvent, type EventCatalogItem } from '../api';
import { useAuth } from '../context/AuthContext';

const CITY_COORDS: Record<string, [number, number]> = {
  madrid: [40.4168, -3.7038],
  barcelona: [41.3851, 2.1734],
  valencia: [39.4699, -0.3763],
  sevilla: [37.3891, -5.9845],
  seville: [37.3891, -5.9845],
  'palma de mallorca': [39.5696, 2.6502],
  mallorca: [39.5696, 2.6502],
  malaga: [36.7213, -4.4214],
  bilbao: [43.263, -2.935],
  zaragoza: [41.6488, -0.8891],
};

const CITY_ZOOM = 12;

const geocodeCache = new Map<string, [number, number] | null>();

async function geocodeCity(query: string): Promise<[number, number] | null> {
  const key = query.trim().toLowerCase();
  if (!key) return null;
  if (geocodeCache.has(key)) return geocodeCache.get(key) ?? null;
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`,
      { headers: { 'Accept-Language': 'en' } },
    );
    if (!res.ok) {
      geocodeCache.set(key, null);
      return null;
    }
    const data = (await res.json()) as Array<{ lat: string; lon: string }>;
    if (!Array.isArray(data) || data.length === 0) {
      geocodeCache.set(key, null);
      return null;
    }
    const coords: [number, number] = [parseFloat(data[0].lat), parseFloat(data[0].lon)];
    geocodeCache.set(key, coords);
    return coords;
  } catch {
    return null;
  }
}

const EVENT_IMAGE_FALLBACK = 'https://picsum.photos/seed/event-placeholder/200/200';

type PinCategory = 'music' | 'food' | 'art';

const segmentoToCategory = (s: string | null): PinCategory => {
  if (s === 'Music') return 'music';
  if (s === 'Arts & Theatre' || s === 'Film') return 'art';
  return 'food';
};

const hasCoords = (
  e: EventCatalogItem,
): e is EventCatalogItem & { latitud: number; longitud: number } =>
  e.latitud != null && e.longitud != null;

// Fix default marker icon paths broken by Vite bundling
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom colored SVG pin icons
const makePin = (color: string) =>
  L.divIcon({
    className: '',
    html: `<div style="
      width:36px;height:36px;
      background:${color};
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      border:3px solid rgba(255,255,255,0.25);
      box-shadow:0 0 18px ${color}99;
    "></div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -38],
  });

const pins = {
  music: makePin('#b6a0ff'),
  food: makePin('#ff946e'),
  art: makePin('#8a99fe'),
};

const categories = ['Concerts', 'Art', 'Dining'];

// Fly to a location when an event is selected
function MapFlyTo({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  map.flyTo([lat, lng], 15, { duration: 1.2 });
  return null;
}

function BoundsWatcher({ onChange }: { onChange: (b: L.LatLngBounds) => void }) {
  const map = useMap();
  useEffect(() => {
    onChange(map.getBounds());
  }, [map, onChange]);
  useMapEvents({
    moveend: () => onChange(map.getBounds()),
  });
  return null;
}

function InitialView({
  preferredLocation,
  preferredLat,
  preferredLng,
  events,
}: {
  preferredLocation: string | null;
  preferredLat: number | null;
  preferredLng: number | null;
  events: Array<{ latitud: number; longitud: number }>;
}) {
  const map = useMap();
  const positionedRef = useRef(false);
  const geoAttemptedRef = useRef(false);

  useEffect(() => {
    if (positionedRef.current) return;
    let cancelled = false;

    async function resolve() {
      if (preferredLat != null && preferredLng != null) {
        map.setView([preferredLat, preferredLng], CITY_ZOOM);
        positionedRef.current = true;
        return;
      }

      if (preferredLocation) {
        const key = preferredLocation
          .trim()
          .toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '');
        let coords: [number, number] | null = CITY_COORDS[key] ?? null;
        if (!coords) coords = await geocodeCity(preferredLocation);
        if (cancelled || positionedRef.current) return;
        if (coords) {
          map.setView(coords, CITY_ZOOM);
          positionedRef.current = true;
          return;
        }
      }

      if (!geoAttemptedRef.current && navigator.geolocation) {
        geoAttemptedRef.current = true;
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            if (positionedRef.current) return;
            map.setView([pos.coords.latitude, pos.coords.longitude], CITY_ZOOM);
            positionedRef.current = true;
          },
          () => {
            if (positionedRef.current || events.length === 0) return;
            map.fitBounds(
              L.latLngBounds(
                events.map((e) => [e.latitud, e.longitud] as [number, number]),
              ),
              { padding: [40, 40] },
            );
            positionedRef.current = true;
          },
        );
        return;
      }

      if (events.length > 0) {
        map.fitBounds(
          L.latLngBounds(events.map((e) => [e.latitud, e.longitud] as [number, number])),
          { padding: [40, 40] },
        );
        positionedRef.current = true;
      }
    }

    resolve();
    return () => {
      cancelled = true;
    };
  }, [preferredLocation, preferredLat, preferredLng, events, map]);

  return null;
}

function EventDetailModal({
  event,
  onClose,
  isLoggedIn,
}: {
  event: EventCatalogItem | null;
  onClose: () => void;
  isLoggedIn: boolean;
}) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSaved(false);
    setError(null);
  }, [event?.id]);

  useEffect(() => {
    if (!event) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [event, onClose]);

  if (!event) return null;

  const title = event.nombre ?? 'Evento';
  const image =
    event.imagen_evento ?? event.artista_imagen ?? EVENT_IMAGE_FALLBACK;
  const locationLine = [event.recinto_nombre, event.ciudad]
    .filter(Boolean)
    .join(' • ');
  const dateLine = [event.fecha, event.hora].filter(Boolean).join(' · ');
  const tags = [event.segmento, event.genero, event.subgenero].filter(Boolean);

  async function onSave() {
    if (!event) return;
    setSaving(true);
    setError(null);
    try {
      await apiSaveEvent({
        event_id: event.id,
        event_title: event.nombre,
        event_venue: event.recinto_nombre,
        event_date: event.fecha,
        event_time: event.hora,
        event_image_url: event.imagen_evento ?? event.artista_imagen,
      });
      setSaved(true);
    } catch {
      setError('No se pudo guardar el evento.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="bg-surface-container-low rounded-[1.5rem] max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-outline-variant/20 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="absolute top-4 right-4 z-10 bg-surface-container-high rounded-full w-9 h-9 flex items-center justify-center text-on-surface hover:bg-surface-variant transition-colors"
          onClick={onClose}
          aria-label="Close"
        >
          <span className="material-symbols-outlined text-lg">close</span>
        </button>

        <div className="w-full h-56 overflow-hidden rounded-t-[1.5rem]">
          <img src={image} alt={title} className="w-full h-full object-cover" />
        </div>

        <div className="p-6 space-y-4">
          <div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {tags.map((t) => (
                  <span
                    key={t as string}
                    className="bg-primary/10 text-primary px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border border-primary/20"
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}
            <h2 className="font-headline font-bold text-2xl leading-tight">{title}</h2>
            {event.artista_nombre && (
              <p className="text-on-surface-variant text-sm mt-1">{event.artista_nombre}</p>
            )}
          </div>

          <div className="space-y-2">
            {locationLine && (
              <div className="flex items-center gap-2 text-on-surface-variant text-sm">
                <span className="material-symbols-outlined text-[18px] text-secondary">location_on</span>
                <span>{locationLine}</span>
              </div>
            )}
            {dateLine && (
              <div className="flex items-center gap-2 text-on-surface-variant text-sm">
                <span className="material-symbols-outlined text-[18px] text-tertiary">event</span>
                <span>{dateLine}</span>
              </div>
            )}
            {event.estado && (
              <div className="flex items-center gap-2 text-on-surface-variant text-sm">
                <span className="material-symbols-outlined text-[18px] text-primary">info</span>
                <span>{event.estado}</span>
              </div>
            )}
          </div>

          {error && (
            <div className="bg-error/10 text-error border border-error/20 rounded-lg px-3 py-2 text-xs">
              {error}
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            {event.url && (
              <a
                href={event.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 bg-primary text-on-primary font-bold py-3 rounded-xl text-sm uppercase tracking-widest text-center hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">open_in_new</span>
                Entradas
              </a>
            )}
            {isLoggedIn && (
              <button
                onClick={onSave}
                disabled={saving || saved}
                className="flex-1 bg-surface-container-high text-on-surface font-bold py-3 rounded-xl text-sm uppercase tracking-widest hover:bg-surface-variant transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">
                  {saved ? 'bookmark_added' : 'bookmark'}
                </span>
                {saved ? 'Guardado' : saving ? 'Guardando…' : 'Guardar'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MapPage() {
  const { user } = useAuth();
  const [activeCategory, setActiveCategory] = useState('Concerts');
  const [flyTarget, setFlyTarget] = useState<{ lat: number; lng: number } | null>(null);
  const [events, setEvents] = useState<EventCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [bounds, setBounds] = useState<L.LatLngBounds | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<EventCatalogItem | null>(null);
  const boundsRef = useRef<L.LatLngBounds | null>(null);
  const inflightRef = useRef<AbortController | null>(null);
  const startPollingRef = useRef<(() => void) | null>(null);

  const fetchEvents = useCallback(() => {
    inflightRef.current?.abort();
    const ctrl = new AbortController();
    inflightRef.current = ctrl;
    const b = boundsRef.current;
    const params = b
      ? {
          min_lat: b.getSouth(),
          max_lat: b.getNorth(),
          min_lng: b.getWest(),
          max_lng: b.getEast(),
        }
      : { limit: 50 };
    apiListEvents(params, { signal: ctrl.signal })
      .then((data) => {
        if (!ctrl.signal.aborted) setEvents(data);
      })
      .catch(() => {
        /* aborted or failed — keep previous events */
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false);
      });
  }, []);

  // Defer first fetch until the map has positioned (bounds set by InitialView).
  // Poll every 60s afterwards. Fallback kicks in if positioning never resolves.
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;
    let started = false;

    const start = () => {
      if (started) return;
      started = true;
      fetchEvents();
      intervalId = setInterval(fetchEvents, 60_000);
    };

    startPollingRef.current = start;
    const fallbackId = setTimeout(start, 3000);

    return () => {
      clearTimeout(fallbackId);
      if (intervalId) clearInterval(intervalId);
      inflightRef.current?.abort();
      startPollingRef.current = null;
    };
  }, [fetchEvents]);

  // Refetch events whenever the map viewport changes (debounced).
  useEffect(() => {
    boundsRef.current = bounds;
    if (!bounds) return;
    startPollingRef.current?.();
    const debounceId = setTimeout(fetchEvents, 300);
    return () => clearTimeout(debounceId);
  }, [bounds, fetchEvents]);

  const mappableEvents = events.filter(hasCoords);

  const visibleEvents = bounds
    ? mappableEvents.filter((e) => bounds.contains([e.latitud, e.longitud]))
    : mappableEvents;

  const handleEventClick = (eventId: string) => {
    const point = mappableEvents.find((p) => p.id === eventId);
    if (!point) return;
    setFlyTarget({ lat: point.latitud, lng: point.longitud });
    setSelectedEvent(point);
  };

  const mapCenter: [number, number] = [40.42, -3.7];

  return (
    <div className="bg-surface text-on-surface min-h-screen">
      <SideNav activeItem="Explore" />

      <main className="md:ml-64 relative min-h-screen flex flex-col overflow-hidden">
        {/* Top Nav */}
        <header className="bg-surface flex justify-between items-center w-full px-4 md:px-8 py-4 z-50 border-b border-outline-variant/10">
          <div className="flex items-center gap-8">
            <h1 className="text-2xl font-bold tracking-tighter text-on-surface font-headline">NextPlan</h1>
            <nav className="hidden lg:flex gap-6 items-center">
              {[
                { label: 'Home', path: '/', active: false },
                { label: 'AI Chat', path: '/planner', active: false },
                { label: 'Explore', path: '/map', active: true },
                { label: 'Profile', path: '/profile', active: false },
              ].map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`font-label text-sm transition-colors duration-300 ${
                    link.active ? 'text-primary border-b-2 border-primary pb-1' : 'text-on-surface/70 hover:text-tertiary'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative hidden sm:block">
              <input
                className="bg-surface-container-lowest border-none rounded-full px-5 py-2 text-sm w-64 focus:outline-none focus:ring-1 focus:ring-secondary text-on-surface placeholder:text-on-surface-variant/50"
                placeholder="Search experiences..."
              />
              <span className="material-symbols-outlined absolute right-3 top-2 text-on-surface-variant text-sm">search</span>
            </div>
            <button className="text-on-surface hover:text-primary transition-colors">
              <span className="material-symbols-outlined">notifications</span>
            </button>
          </div>
        </header>

        {/* Map + Side Panel */}
        <section className="flex-1 relative flex flex-col md:flex-row md:h-[calc(100vh-65px)]">

          {/* ── Real Leaflet Map ── */}
          <div className="h-[55vh] md:h-auto md:flex-1 relative">
            <MapContainer
              center={mapCenter}
              zoom={13}
              style={{ width: '100%', height: '100%' }}
              zoomControl={false}
            >
              {/* CartoDB Dark Matter tiles — dark map for free */}
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
              />

              {flyTarget && <MapFlyTo lat={flyTarget.lat} lng={flyTarget.lng} />}
              <BoundsWatcher onChange={setBounds} />
              <InitialView
                preferredLocation={user?.preferred_location ?? null}
                preferredLat={user?.preferred_location_lat ?? null}
                preferredLng={user?.preferred_location_lng ?? null}
                events={mappableEvents}
              />

              <MarkerClusterGroup chunkedLoading>
                {visibleEvents.map((point) => {
                  const category = segmentoToCategory(point.segmento);
                  return (
                    <Marker
                      key={point.id}
                      position={[point.latitud, point.longitud]}
                      icon={pins[category]}
                      eventHandlers={{
                        click: () => setSelectedEvent(point),
                      }}
                    >
                      <Popup className="curator-popup">
                        <div style={{ background: '#1e1f25', color: '#faf8fe', padding: '12px 14px', borderRadius: '12px', minWidth: '200px', fontFamily: 'Manrope, sans-serif' }}>
                          <p style={{ fontSize: '11px', fontWeight: 700, opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '4px' }}>
                            {point.segmento ?? category}
                          </p>
                          <p style={{ fontSize: '14px', fontWeight: 800, marginBottom: '2px' }}>
                            {point.nombre ?? 'Evento'}
                          </p>
                          <p style={{ fontSize: '12px', opacity: 0.7, marginBottom: '8px' }}>
                            {[point.recinto_nombre, point.ciudad].filter(Boolean).join(' • ')}
                          </p>
                          <button
                            onClick={() => setSelectedEvent(point)}
                            style={{
                              background: '#b6a0ff',
                              color: '#1e1f25',
                              border: 'none',
                              borderRadius: '8px',
                              padding: '6px 10px',
                              fontSize: '11px',
                              fontWeight: 800,
                              textTransform: 'uppercase',
                              letterSpacing: '0.08em',
                              cursor: 'pointer',
                              width: '100%',
                            }}
                          >
                            Ver detalles
                          </button>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </MarkerClusterGroup>
            </MapContainer>

            {/* Filter Bar – floating over the map */}
            <div className="absolute top-6 left-6 z-[400] pointer-events-auto">
              <div className="bg-surface-variant/80 backdrop-blur-3xl rounded-full px-6 py-3 flex flex-wrap items-center gap-4 shadow-2xl border border-outline-variant/20">
                <div className="flex items-center gap-3 border-r border-outline-variant/20 pr-6">
                  <span className="material-symbols-outlined text-primary text-lg">calendar_today</span>
                  <span className="font-label text-sm font-semibold">Tonight, Dec 14</span>
                </div>
                <div className="flex items-center gap-3 border-r border-outline-variant/20 pr-6">
                  <span className="material-symbols-outlined text-secondary text-lg">filter_alt</span>
                  <div className="flex gap-2">
                    {categories.map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setActiveCategory(cat)}
                        className={`px-3 py-1 rounded-full text-xs transition-colors ${
                          activeCategory === cat
                            ? 'bg-surface-container-high border border-primary/20 text-primary'
                            : 'bg-surface-container-high text-on-surface-variant hover:text-on-surface'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-tertiary text-lg">payments</span>
                  <span className="font-label text-sm font-semibold">Under $50</span>
                </div>
              </div>
            </div>

            {/* Weather Overlay – bottom-left corner of the map */}
            <div className="absolute bottom-6 left-6 z-[400]">
              <div className="bg-surface-container-high/90 backdrop-blur-xl p-4 rounded-xl border border-outline-variant/15 flex items-center gap-4 shadow-xl">
                <div className="flex flex-col">
                  <span className="text-xs text-on-surface-variant font-medium uppercase tracking-widest">Berlin Mitte</span>
                  <span className="text-2xl font-headline font-bold">2°C</span>
                </div>
                <div className="h-10 w-px bg-outline-variant/20" />
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-3xl">cloudy_snowing</span>
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold">Light Snow</span>
                    <span className="text-[10px] text-on-surface-variant">Wind: 12 km/h</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="absolute bottom-6 right-6 z-[400]">
              <div className="bg-surface-container-high/90 backdrop-blur-xl px-5 py-3 rounded-xl border border-outline-variant/15 flex flex-col gap-2 shadow-xl">
                {[
                  { color: '#b6a0ff', label: 'Music' },
                  { color: '#ff946e', label: 'Food' },
                  { color: '#8a99fe', label: 'Art' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ background: item.color, boxShadow: `0 0 6px ${item.color}` }} />
                    <span className="text-xs font-semibold text-on-surface-variant">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Side Panel */}
          <div className="w-full md:w-[380px] bg-surface-container-low/95 backdrop-blur-2xl z-20 shadow-[-20px_0_40px_rgba(0,0,0,0.5)] flex flex-col overflow-y-auto border-l border-outline-variant/10 pb-20 md:pb-0">
            <div className="p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-headline font-bold">Nearby Experiences</h2>
                <span className="bg-secondary/10 text-secondary px-3 py-1 rounded-full text-xs font-bold border border-secondary/20">
                  {visibleEvents.length} Active Now
                </span>
              </div>

              {loading ? (
                [0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="bg-surface-container-high rounded-xl p-4 mb-4 animate-pulse"
                  >
                    <div className="flex gap-4">
                      <div className="w-24 h-24 rounded-lg bg-surface-variant/30 flex-shrink-0" />
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-surface-variant/30 rounded w-3/4" />
                        <div className="h-3 bg-surface-variant/30 rounded w-1/2" />
                        <div className="h-3 bg-surface-variant/30 rounded w-1/3" />
                      </div>
                    </div>
                  </div>
                ))
              ) : events.length === 0 ? (
                <div className="bg-surface-container-high rounded-xl p-6 text-center text-on-surface-variant text-sm">
                  No hay eventos disponibles todavía.
                </div>
              ) : visibleEvents.length === 0 ? (
                <div className="bg-surface-container-high rounded-xl p-6 text-center text-on-surface-variant text-sm">
                  No hay eventos en esta zona. Aleja el zoom o mueve el mapa.
                </div>
              ) : (
                visibleEvents.map((event) => {
                  const title = event.nombre ?? 'Evento';
                  const image =
                    event.imagen_evento ?? event.artista_imagen ?? EVENT_IMAGE_FALLBACK;
                  const locationLine = [event.recinto_nombre, event.ciudad]
                    .filter(Boolean)
                    .join(' • ');
                  const dateLine = [event.fecha, event.hora].filter(Boolean).join(' · ');
                  return (
                    <button
                      key={event.id}
                      onClick={() => handleEventClick(event.id)}
                      className="w-full text-left group bg-surface-container-high rounded-xl p-4 mb-4 transition-colors hover:bg-surface-variant cursor-pointer"
                    >
                      <div className="flex gap-4">
                        <div className="w-24 h-24 rounded-lg overflow-hidden flex-shrink-0">
                          <img
                            src={image}
                            alt={title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-headline font-bold text-sm leading-tight group-hover:text-primary transition-colors truncate mb-1">
                            {title}
                          </h3>
                          {locationLine && (
                            <div className="flex items-center gap-1 text-on-surface-variant text-[11px] mb-1">
                              <span className="material-symbols-outlined text-[14px]">
                                location_on
                              </span>
                              <span className="truncate">{locationLine}</span>
                            </div>
                          )}
                          {dateLine && (
                            <div className="flex items-center gap-1 text-on-surface-variant text-[11px]">
                              <span className="material-symbols-outlined text-[14px]">
                                event
                              </span>
                              <span>{dateLine}</span>
                            </div>
                          )}
                          {event.segmento && (
                            <span className="inline-block mt-2 bg-surface-container-lowest px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                              {event.segmento}
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>

            <div className="mt-auto p-8 border-t border-outline-variant/10">
              <Link
                to="/planner"
                className="w-full bg-tertiary text-on-tertiary font-black py-4 rounded-xl text-sm uppercase tracking-widest hover:scale-[0.98] active:opacity-80 transition-all flex items-center justify-center gap-3 shadow-[0_0_30px_rgba(255,148,110,0.3)]"
              >
                <span className="material-symbols-outlined">casino</span>
                Surprise Me
              </Link>
            </div>
          </div>
        </section>

        <Footer />
      </main>

      <BottomNav />

      <EventDetailModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        isLoggedIn={!!user}
      />
    </div>
  );
}
