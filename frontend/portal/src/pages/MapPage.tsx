import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  APIProvider,
  Map as GMap,
  AdvancedMarker,
  useMap,
} from '@vis.gl/react-google-maps';
import { MarkerClusterer } from '@googlemaps/markerclusterer';
import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import EventCalendar from '../components/event/EventCalendar';
import {
  apiListEventCategories,
  apiListEvents,
  apiSaveEvent,
  cleanLabel,
  type EventCatalogItem,
} from '../api';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LanguageContext';

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

function buildEventDescription(event: EventCatalogItem): string {
  const parts: string[] = [];
  if (event.artista_nombre) {
    parts.push(`Join ${event.artista_nombre} for an unforgettable live experience.`);
  }
  const segmento = cleanLabel(event.segmento);
  const genero = cleanLabel(event.genero);
  const subgenero = cleanLabel(event.subgenero);
  const genreBits = [genero, subgenero].filter(Boolean).join(' / ');
  if (genreBits) parts.push(`Genre: ${genreBits}.`);
  if (segmento) parts.push(`Category: ${segmento}.`);
  if (event.recinto_nombre || event.ciudad || event.direccion) {
    parts.push(
      `Taking place at ${[event.recinto_nombre, event.direccion, event.ciudad].filter(Boolean).join(', ')}.`,
    );
  }
  return parts.length > 0
    ? parts.join(' ')
    : `Discover ${event.nombre ?? 'this event'} and plan your night out.`;
}

type PinCategory = 'music' | 'food' | 'art';

const segmentoToCategory = (s: string | null): PinCategory => {
  const c = cleanLabel(s);
  if (c === 'Music') return 'music';
  if (c === 'Arts & Theatre' || c === 'Film') return 'art';
  return 'food';
};

const hasCoords = (
  e: EventCatalogItem,
): e is EventCatalogItem & { latitud: number; longitud: number } =>
  e.latitud != null && e.longitud != null;

type MappableEvent = EventCatalogItem & { latitud: number; longitud: number };

type EventGroup = {
  key: string;
  primary: MappableEvent;
  items: MappableEvent[];
};

function groupKey(e: EventCatalogItem): string {
  return [
    (e.nombre ?? '').trim().toLowerCase(),
    (e.recinto_nombre ?? '').trim().toLowerCase(),
    (e.ciudad ?? '').trim().toLowerCase(),
  ].join('|');
}

function groupMappableEvents(events: MappableEvent[]): EventGroup[] {
  const map = new Map<string, EventGroup>();
  for (const ev of events) {
    const key = groupKey(ev);
    const g = map.get(key);
    if (g) g.items.push(ev);
    else map.set(key, { key, primary: ev, items: [ev] });
  }
  for (const g of map.values()) {
    g.items.sort((a, b) => {
      const av = a.fecha_utc ?? `${a.fecha ?? ''} ${a.hora ?? ''}`;
      const bv = b.fecha_utc ?? `${b.fecha ?? ''} ${b.hora ?? ''}`;
      return av.localeCompare(bv);
    });
    g.primary = g.items[0];
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

const GMAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string;
const GMAPS_MAP_ID =
  (import.meta.env.VITE_GOOGLE_MAPS_MAP_ID as string | undefined) || undefined;

// AdvancedMarkerElement requires a vector map, which only loads when a
// Cloud-based map style ID is provided. Without it the map renders raster
// tiles and AdvancedMarker.setMap throws "Cannot read properties of
// undefined (reading 'getRootNode')".
if (!GMAPS_MAP_ID && typeof window !== 'undefined') {
  // eslint-disable-next-line no-console
  console.warn(
    '[MapPage] VITE_GOOGLE_MAPS_MAP_ID is not set. Advanced markers will not render.',
  );
}

type Bounds = { south: number; west: number; north: number; east: number };

const PIN_COLOR: Record<PinCategory, string> = {
  music: '#b6a0ff',
  food: '#ff946e',
  art: '#8a99fe',
};

function CategoryPin({
  category,
  hovered,
}: {
  category: PinCategory;
  hovered: boolean;
}) {
  const color = PIN_COLOR[category];
  const size = hovered ? 52 : 36;
  return (
    <div
      style={{
        width: size,
        height: size,
        background: color,
        borderRadius: '50% 50% 50% 0',
        transform: 'rotate(-45deg) translateY(-50%)',
        border: `3px solid ${hovered ? '#ffffff' : 'rgba(255,255,255,0.25)'}`,
        boxShadow: `0 0 ${hovered ? 28 : 18}px ${color}${hovered ? 'ff' : '99'}`,
        transition: 'all 120ms ease',
      }}
    />
  );
}

const ALL_CATEGORIES = 'All';

const todayIso = () => {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

function MapFlyTo({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    if (!map) return;
    map.panTo({ lat, lng });
    map.setZoom(15);
  }, [lat, lng, map]);
  return null;
}

function BoundsWatcher({ onChange }: { onChange: (b: Bounds) => void }) {
  const map = useMap();
  useEffect(() => {
    if (!map) return;
    const emit = () => {
      const b = map.getBounds();
      if (!b) return;
      const sw = b.getSouthWest();
      const ne = b.getNorthEast();
      onChange({
        south: sw.lat(),
        west: sw.lng(),
        north: ne.lat(),
        east: ne.lng(),
      });
    };
    emit();
    const listener = map.addListener('idle', emit);
    return () => listener.remove();
  }, [map, onChange]);
  return null;
}

function ClusteredMarkers({
  groups,
  hoveredKey,
  setHoveredKey,
  onClick,
}: {
  groups: EventGroup[];
  hoveredKey: string | null;
  setHoveredKey: React.Dispatch<React.SetStateAction<string | null>>;
  onClick: (group: EventGroup) => void;
}) {
  const map = useMap();
  const clustererRef = useRef<MarkerClusterer | null>(null);
  const markersRef = useRef(
    new Map<string, google.maps.marker.AdvancedMarkerElement>(),
  );

  useEffect(() => {
    if (!map || clustererRef.current) return;
    clustererRef.current = new MarkerClusterer({ map });
    return () => {
      clustererRef.current?.clearMarkers();
      clustererRef.current = null;
    };
  }, [map]);

  const resync = useCallback(() => {
    const c = clustererRef.current;
    if (!c) return;
    c.clearMarkers();
    c.addMarkers(Array.from(markersRef.current.values()));
  }, []);

  const keysSig = useMemo(() => groups.map((g) => g.key).join('|'), [groups]);
  useEffect(() => {
    resync();
  }, [keysSig, resync]);

  // Just collect the refs. The keysSig effect performs a single
  // clear+add after each render commit, so we avoid clearing the
  // clusterer N times during ref attach/detach cycles.
  const setMarkerRef = useCallback(
    (
      marker: google.maps.marker.AdvancedMarkerElement | null,
      key: string,
    ) => {
      const cur = markersRef.current.get(key);
      if (marker === cur) return;
      if (marker) markersRef.current.set(key, marker);
      else markersRef.current.delete(key);
    },
    [],
  );

  return (
    <>
      {groups.map((group) => {
        const point = group.primary;
        const category = segmentoToCategory(point.segmento);
        const hovered = hoveredKey === group.key;
        const position = { lat: point.latitud, lng: point.longitud };
        return (
          <AdvancedMarker
            key={group.key}
            ref={(m) => setMarkerRef(m, group.key)}
            position={position}
            zIndex={hovered ? 1000 : undefined}
            onClick={() => onClick(group)}
          >
            <div
              onMouseEnter={() => setHoveredKey(group.key)}
              onMouseLeave={() =>
                setHoveredKey((k) => (k === group.key ? null : k))
              }
            >
              <CategoryPin category={category} hovered={hovered} />
            </div>
          </AdvancedMarker>
        );
      })}
    </>
  );
}

function EventDetailModal({
  event,
  occurrences,
  onClose,
  isLoggedIn,
}: {
  event: EventCatalogItem | null;
  occurrences: EventCatalogItem[];
  onClose: () => void;
  isLoggedIn: boolean;
}) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
    setSaved(false);
    setError(null);
    setShareOpen(false);
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
  const schedule = buildScheduleEntries(occurrences.length ? occurrences : [event]);
  const dateLine = [event.fecha, event.hora].filter(Boolean).join(' · ');
  const tags = [event.segmento, event.genero, event.subgenero]
    .map(cleanLabel)
    .filter(Boolean);

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
        event_url: event.url,
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
            {schedule.length > 0 ? (
              <EventCalendar entries={schedule} />
            ) : dateLine && (
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

          <p className="text-on-surface-variant text-sm leading-relaxed">
            {buildEventDescription(event)}
          </p>

          {error && (
            <div className="bg-error/10 text-error border border-error/20 rounded-lg px-3 py-2 text-xs">
              {error}
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Link
              to={`/event/${event.id}`}
              onClick={onClose}
              className="flex-1 bg-primary text-on-primary font-bold py-3 rounded-xl text-sm uppercase tracking-widest text-center hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px]">info</span>
              More info
            </Link>
            {event.url && (
              <a
                href={event.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 bg-surface-container-high text-on-surface font-bold py-3 rounded-xl text-sm uppercase tracking-widest text-center hover:bg-surface-variant transition-colors flex items-center justify-center gap-2"
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
            <div className="relative">
              <button
                onClick={() => setShareOpen((v) => !v)}
                className="w-full sm:w-auto bg-surface-container-high text-on-surface font-bold py-3 px-4 rounded-xl text-sm uppercase tracking-widest hover:bg-surface-variant transition-colors flex items-center justify-center gap-2"
                aria-label="Share"
                aria-expanded={shareOpen}
                title="Compartir"
              >
                <span className="material-symbols-outlined text-[18px]">share</span>
              </button>
              {shareOpen && shareData && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShareOpen(false)} />
                  <div className="absolute bottom-full mb-2 right-0 z-50 bg-surface-container-highest border border-outline-variant/20 rounded-2xl shadow-2xl p-3 min-w-[240px]">
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
        </div>
      </div>
    </div>
  );
}

export default function MapPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [categoryOptions, setCategoryOptions] = useState<string[]>([]);
  const [categoryMenuOpen, setCategoryMenuOpen] = useState(false);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const mobileFiltersRef = useRef<HTMLDivElement | null>(null);
  const categoryMenuRef = useRef<HTMLDivElement | null>(null);
  const [flyTarget, setFlyTarget] = useState<{ lat: number; lng: number } | null>(null);
  const [events, setEvents] = useState<EventCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [bounds, setBounds] = useState<Bounds | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<EventCatalogItem | null>(null);
  const [selectedOccurrences, setSelectedOccurrences] = useState<EventCatalogItem[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(todayIso);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const dateRef = useRef<string>(todayIso());
  const segmentosRef = useRef<string[]>([]);
  const dateInputRef = useRef<HTMLInputElement | null>(null);
  const inflightRef = useRef<AbortController | null>(null);
  const boundsRef = useRef<Bounds | null>(null);
  const initialFetchedRef = useRef(false);
  const [initialCenter, setInitialCenter] = useState<{ lat: number; lng: number; zoom: number } | null>(null);
  const initialResolvedRef = useRef(false);

  // Resolve starting map center: geolocation > saved city > Madrid.
  useEffect(() => {
    if (initialResolvedRef.current) return;
    let cancelled = false;

    function commit(lat: number, lng: number) {
      if (cancelled || initialResolvedRef.current) return;
      initialResolvedRef.current = true;
      setInitialCenter({ lat, lng, zoom: CITY_ZOOM });
    }

    async function resolveStart() {
      // 1. Geolocation
      if (navigator.geolocation) {
        try {
          const pos = await new Promise<GeolocationPosition>((res, rej) => {
            navigator.geolocation.getCurrentPosition(res, rej, { timeout: 8000 });
          });
          commit(pos.coords.latitude, pos.coords.longitude);
          return;
        } catch {
          /* fall through */
        }
      }
      if (cancelled || initialResolvedRef.current) return;

      // 2. Saved location coords
      const lat = user?.preferred_location_lat;
      const lng = user?.preferred_location_lng;
      if (lat != null && lng != null) {
        commit(lat, lng);
        return;
      }

      // 3. Saved city name → known coords or geocode
      if (user?.preferred_location) {
        const key = user.preferred_location
          .trim()
          .toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '');
        let coords: [number, number] | null = CITY_COORDS[key] ?? null;
        if (!coords) coords = await geocodeCity(user.preferred_location);
        if (cancelled || initialResolvedRef.current) return;
        if (coords) {
          commit(coords[0], coords[1]);
          return;
        }
      }

      // 4. Madrid fallback
      const [mLat, mLng] = CITY_COORDS.madrid;
      commit(mLat, mLng);
    }

    resolveStart();
    return () => {
      cancelled = true;
    };
  }, [user?.preferred_location, user?.preferred_location_lat, user?.preferred_location_lng]);

  const fetchEvents = useCallback(() => {
    inflightRef.current?.abort();
    const ctrl = new AbortController();
    inflightRef.current = ctrl;
    setLoading(true);
    const fecha = dateRef.current || undefined;
    const segmentos = segmentosRef.current.length ? segmentosRef.current : undefined;
    const b = boundsRef.current;
    const params: NonNullable<Parameters<typeof apiListEvents>[0]> = { limit: 1000 };
    if (b) {
      params.min_lat = b.south;
      params.max_lat = b.north;
      params.min_lng = b.west;
      params.max_lng = b.east;
    }
    if (fecha) params.fecha = fecha;
    if (segmentos) params.segmento = segmentos;
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

  // Track latest bounds (no auto-refetch on map move).
  useEffect(() => {
    boundsRef.current = bounds;
    // First fetch only fires once bounds are available, so the initial
    // viewport constrains the query.
    if (bounds && !initialFetchedRef.current) {
      initialFetchedRef.current = true;
      fetchEvents();
    }
  }, [bounds, fetchEvents]);

  // Scroll side panel to hovered card.
  useEffect(() => {
    if (!hoveredKey) return;
    const el = cardRefs.current.get(hoveredKey);
    if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [hoveredKey]);

  // Cleanup inflight on unmount.
  useEffect(() => {
    return () => {
      inflightRef.current?.abort();
    };
  }, []);

  // Refetch when selected date changes (after initial fetch).
  useEffect(() => {
    dateRef.current = selectedDate;
    if (initialFetchedRef.current) fetchEvents();
  }, [selectedDate, fetchEvents]);

  // Refetch when selected categories change (after initial fetch).
  useEffect(() => {
    segmentosRef.current = selectedCategories;
    if (initialFetchedRef.current) fetchEvents();
  }, [selectedCategories, fetchEvents]);

  const toggleCategory = useCallback((cat: string) => {
    if (cat === ALL_CATEGORIES) {
      setSelectedCategories([]);
      return;
    }
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat],
    );
  }, []);

  // Refetch available categories when date changes.
  useEffect(() => {
    const ctrl = new AbortController();
    const params: Parameters<typeof apiListEventCategories>[0] = {};
    if (selectedDate) params.fecha = selectedDate;
    apiListEventCategories(params, { signal: ctrl.signal })
      .then((cats) =>
        setCategoryOptions(
          cats
            .map((c) => cleanLabel(c))
            .filter((c): c is string => c !== null),
        ),
      )
      .catch(() => {
        /* leave previous options on failure */
      });
    return () => ctrl.abort();
  }, [selectedDate]);

  // Drop any selected categories that are no longer present in the viewport.
  useEffect(() => {
    if (!categoryOptions.length || !selectedCategories.length) return;
    const still = selectedCategories.filter((c) => categoryOptions.includes(c));
    if (still.length !== selectedCategories.length) setSelectedCategories(still);
  }, [categoryOptions, selectedCategories]);

  // Close mobile filters on outside click / Escape.
  useEffect(() => {
    if (!mobileFiltersOpen) return;
    const onDown = (e: Event) => {
      if (
        mobileFiltersRef.current &&
        !mobileFiltersRef.current.contains(e.target as Node)
      ) {
        setMobileFiltersOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileFiltersOpen(false);
    };
    document.addEventListener('pointerdown', onDown, true);
    document.addEventListener('touchstart', onDown, true);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onDown, true);
      document.removeEventListener('touchstart', onDown, true);
      document.removeEventListener('keydown', onKey);
    };
  }, [mobileFiltersOpen]);

  // Close category menu on outside click / Escape.
  useEffect(() => {
    if (!categoryMenuOpen) return;
    const onDown = (e: MouseEvent) => {
      if (
        categoryMenuRef.current &&
        !categoryMenuRef.current.contains(e.target as Node)
      ) {
        setCategoryMenuOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setCategoryMenuOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [categoryMenuOpen]);

  const mappableEvents = events.filter(hasCoords);
  const groupedEvents = groupMappableEvents(mappableEvents);

  const visibleGroups = bounds
    ? groupedEvents.filter((g) => {
        const { latitud: lat, longitud: lng } = g.primary;
        return (
          lat >= bounds.south &&
          lat <= bounds.north &&
          lng >= bounds.west &&
          lng <= bounds.east
        );
      })
    : groupedEvents;

  const openGroup = (g: EventGroup) => {
    setFlyTarget({ lat: g.primary.latitud, lng: g.primary.longitud });
    setSelectedEvent(g.primary);
    setSelectedOccurrences(g.items);
  };

  const handleEventClick = (groupKeyValue: string) => {
    const g = groupedEvents.find((x) => x.key === groupKeyValue);
    if (!g) return;
    openGroup(g);
  };

  return (
    <div className="bg-surface text-on-surface h-screen overflow-hidden flex flex-col">
      <TopNav />

      <main className="relative flex-1 min-h-0 flex flex-col">
        {/* Map + Side Panel */}
        <section className="relative flex-1 min-h-0 overflow-hidden flex flex-col md:flex-row">

          <div className="h-[45vh] md:h-auto md:flex-1 relative shrink-0">
            {initialCenter ? (
            <APIProvider apiKey={GMAPS_API_KEY}>
              <GMap
                defaultCenter={{ lat: initialCenter.lat, lng: initialCenter.lng }}
                defaultZoom={initialCenter.zoom}
                mapId={GMAPS_MAP_ID}
                disableDefaultUI
                gestureHandling="greedy"
                style={{ width: '100%', height: '100%' }}
              >
                {flyTarget && (
                  <MapFlyTo lat={flyTarget.lat} lng={flyTarget.lng} />
                )}
                <BoundsWatcher onChange={setBounds} />
                <ClusteredMarkers
                  groups={visibleGroups}
                  hoveredKey={hoveredKey}
                  setHoveredKey={setHoveredKey}
                  onClick={openGroup}
                />
              </GMap>
            </APIProvider>
            ) : (
              <div className="h-full w-full flex items-center justify-center bg-surface-container-low text-on-surface-variant">
                <span className="material-symbols-outlined animate-pulse text-3xl">my_location</span>
              </div>
            )}

            {/* Filter Bar – floating over the map (desktop) */}
            <div className="hidden md:block absolute top-6 left-6 z-[400] pointer-events-auto">
              <div className="bg-surface-variant/80 backdrop-blur-3xl rounded-full px-6 py-3 flex flex-wrap items-center gap-4 shadow-2xl border border-outline-variant/20">
                <div className="flex items-center gap-3 border-r border-outline-variant/20 pr-6">
                  <button
                    type="button"
                    onClick={() => dateInputRef.current?.showPicker?.()}
                    className="material-symbols-outlined text-primary text-lg hover:opacity-80 transition-opacity cursor-pointer"
                    aria-label="Open date picker"
                  >
                    calendar_today
                  </button>
                  <input
                    ref={dateInputRef}
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="bg-transparent border-none outline-none font-label text-sm font-semibold text-on-surface [color-scheme:dark] cursor-pointer [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
                  />
                  {selectedDate && (
                    <button
                      type="button"
                      onClick={() => setSelectedDate('')}
                      className="material-symbols-outlined text-on-surface-variant text-sm hover:text-on-surface transition-colors"
                      aria-label="Clear date filter"
                    >
                      close
                    </button>
                  )}
                </div>
                <div
                  ref={categoryMenuRef}
                  className="relative flex items-center gap-3 border-r border-outline-variant/20 pr-6"
                >
                  <button
                    type="button"
                    onClick={() => setCategoryMenuOpen((v) => !v)}
                    className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
                    aria-haspopup="listbox"
                    aria-expanded={categoryMenuOpen}
                  >
                    <span className="material-symbols-outlined text-secondary text-lg">
                      filter_alt
                    </span>
                    <span className="font-label text-sm font-semibold">
                      {selectedCategories.length === 0
                        ? ALL_CATEGORIES
                        : selectedCategories.length === 1
                        ? selectedCategories[0]
                        : `${selectedCategories.length} categories`}
                    </span>
                    <span className="material-symbols-outlined text-on-surface-variant text-sm">
                      {categoryMenuOpen ? 'expand_less' : 'expand_more'}
                    </span>
                  </button>
                  {categoryMenuOpen && (
                    <div
                      role="listbox"
                      aria-multiselectable="true"
                      className="absolute top-full left-0 mt-2 z-[500] bg-surface-container-high rounded-2xl border border-outline-variant/20 shadow-2xl min-w-[200px] max-h-[260px] overflow-y-auto py-2"
                    >
                      {[ALL_CATEGORIES, ...categoryOptions].map((cat) => {
                        const isAll = cat === ALL_CATEGORIES;
                        const selected = isAll
                          ? selectedCategories.length === 0
                          : selectedCategories.includes(cat);
                        return (
                          <button
                            key={cat}
                            role="option"
                            aria-selected={selected}
                            onClick={() => toggleCategory(cat)}
                            className={`w-full text-left px-4 py-2 text-xs font-semibold transition-colors flex items-center gap-2 ${
                              selected
                                ? 'text-primary bg-primary/10'
                                : 'text-on-surface hover:bg-surface-variant/50'
                            }`}
                          >
                            <span className="material-symbols-outlined text-base">
                              {selected ? 'check_box' : 'check_box_outline_blank'}
                            </span>
                            {cat}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Reload button (desktop) */}
            <button
              type="button"
              onClick={fetchEvents}
              disabled={loading}
              className="hidden md:flex absolute top-6 right-6 z-[400] bg-surface-container-high/90 backdrop-blur-xl rounded-full px-5 h-12 items-center gap-2 border border-outline-variant/20 shadow-xl hover:bg-surface-variant transition-colors disabled:opacity-50"
              aria-label="Reload events in this area"
              title="Reload events in this area"
            >
              <span
                className={`material-symbols-outlined text-primary text-xl ${loading ? 'animate-spin' : ''}`}
              >
                autorenew
              </span>
              <span className="font-label text-sm font-semibold text-on-surface">
                Reload events in this area
              </span>
            </button>

            {/* Mobile reload icon */}
            <button
              type="button"
              onClick={fetchEvents}
              disabled={loading}
              className="md:hidden absolute top-4 right-4 z-[400] bg-surface-container-high/90 backdrop-blur-xl rounded-full w-11 h-11 flex items-center justify-center border border-outline-variant/20 shadow-xl hover:bg-surface-variant transition-colors disabled:opacity-50"
              aria-label="Reload events in this area"
              title="Reload events in this area"
            >
              <span
                className={`material-symbols-outlined text-primary text-xl ${loading ? 'animate-spin' : ''}`}
              >
                autorenew
              </span>
            </button>

            {/* Mobile filter icon + dropdown */}
            <div ref={mobileFiltersRef} className="md:hidden absolute top-4 left-4 z-[450]">
              <button
                type="button"
                onClick={() => setMobileFiltersOpen((v) => !v)}
                className="bg-surface-variant/85 backdrop-blur-xl rounded-full w-11 h-11 flex items-center justify-center border border-outline-variant/20 shadow-xl hover:bg-surface-variant transition-colors"
                aria-label="Filters"
                aria-expanded={mobileFiltersOpen}
              >
                <span className="material-symbols-outlined text-primary text-xl">tune</span>
                {(selectedCategories.length > 0 || selectedDate) && (
                  <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-primary border-2 border-surface" />
                )}
              </button>
              {mobileFiltersOpen && (
                <div className="absolute top-full mt-2 left-0 w-72 bg-surface-container-high rounded-2xl border border-outline-variant/20 shadow-2xl p-4 space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="material-symbols-outlined text-primary text-base">calendar_today</span>
                      <span className="font-label text-xs font-bold uppercase tracking-wider text-on-surface-variant">Day</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="flex-1 bg-surface-container rounded-lg px-3 py-2 text-sm font-semibold text-on-surface [color-scheme:dark] outline-none border border-outline-variant/20"
                      />
                      {selectedDate && (
                        <button
                          type="button"
                          onClick={() => setSelectedDate('')}
                          className="material-symbols-outlined text-on-surface-variant text-base hover:text-on-surface"
                          aria-label="Clear date filter"
                        >
                          close
                        </button>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="material-symbols-outlined text-secondary text-base">filter_alt</span>
                      <span className="font-label text-xs font-bold uppercase tracking-wider text-on-surface-variant">Categories</span>
                    </div>
                    <div className="max-h-44 overflow-y-auto rounded-lg border border-outline-variant/20">
                      {[ALL_CATEGORIES, ...categoryOptions].map((cat) => {
                        const isAll = cat === ALL_CATEGORIES;
                        const selected = isAll
                          ? selectedCategories.length === 0
                          : selectedCategories.includes(cat);
                        return (
                          <button
                            key={cat}
                            onClick={() => toggleCategory(cat)}
                            className={`w-full text-left px-3 py-2 text-xs font-semibold flex items-center gap-2 transition-colors ${
                              selected ? 'text-primary bg-primary/10' : 'text-on-surface hover:bg-surface-variant/50'
                            }`}
                          >
                            <span className="material-symbols-outlined text-base">
                              {selected ? 'check_box' : 'check_box_outline_blank'}
                            </span>
                            {cat}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                </div>
              )}
            </div>

          </div>

          {/* Side Panel */}
          <div className="w-full md:w-[380px] flex-1 md:flex-none md:h-full min-h-0 bg-surface-container-low/95 backdrop-blur-2xl z-20 shadow-[-20px_0_40px_rgba(0,0,0,0.5)] flex flex-col overflow-y-auto border-l border-outline-variant/10 pb-20 md:pb-0">
            <div className="p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-serif text-xl">{t.map_title}</h2>
                <span className="bg-secondary/10 text-secondary px-3 py-1 rounded-full text-xs font-bold border border-secondary/20">
                  {visibleGroups.length} Active Now
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
              ) : visibleGroups.length === 0 ? (
                <div className="bg-surface-container-high rounded-xl p-6 text-center text-on-surface-variant text-sm">
                  No hay eventos en esta zona. Aleja el zoom o mueve el mapa.
                </div>
              ) : (
                visibleGroups.map((group) => {
                  const event = group.primary;
                  const title = event.nombre ?? 'Evento';
                  const image =
                    event.imagen_evento ?? event.artista_imagen ?? EVENT_IMAGE_FALLBACK;
                  const locationLine = [event.recinto_nombre, event.ciudad]
                    .filter(Boolean)
                    .join(' • ');
                  return (
                    <div
                      key={group.key}
                      ref={(el) => {
                        if (el) cardRefs.current.set(group.key, el);
                        else cardRefs.current.delete(group.key);
                      }}
                      onMouseEnter={() => setHoveredKey(group.key)}
                      onMouseLeave={() => setHoveredKey((k) => (k === group.key ? null : k))}
                      className={`group bg-surface-container-high rounded-xl p-4 mb-4 transition-colors hover:bg-surface-variant ${
                        hoveredKey === group.key ? 'ring-2 ring-primary' : ''
                      }`}
                    >
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={() => handleEventClick(group.key)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleEventClick(group.key);
                          }
                        }}
                        className="flex gap-4 cursor-pointer text-left"
                      >
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
                          <p className="text-on-surface-variant text-[11px] leading-snug line-clamp-2">
                            {buildEventDescription(event)}
                          </p>
                          {cleanLabel(event.segmento) && (
                            <span className="inline-block mt-2 bg-surface-container-lowest px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                              {cleanLabel(event.segmento)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

          </div>
        </section>
      </main>

      <Footer />

      <BottomNav />

      <EventDetailModal
        event={selectedEvent}
        occurrences={selectedOccurrences}
        onClose={() => {
          setSelectedEvent(null);
          setSelectedOccurrences([]);
        }}
        isLoggedIn={!!user}
      />
    </div>
  );
}
