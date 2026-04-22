import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  apiListEvents,
  apiListSavedEvents,
  apiSaveEvent,
  type EventCatalogItem,
} from '../api';

const IMAGE_FALLBACK = 'https://picsum.photos/seed/quick-match/600/800';

type SwipeDir = 'left' | 'right';

function dedupe(events: EventCatalogItem[]): EventCatalogItem[] {
  const seen = new Map<string, EventCatalogItem>();
  for (const ev of events) {
    const key = [
      (ev.nombre ?? '').trim().toLowerCase(),
      (ev.recinto_nombre ?? '').trim().toLowerCase(),
      (ev.ciudad ?? '').trim().toLowerCase(),
    ].join('|');
    if (!seen.has(key)) seen.set(key, ev);
  }
  return Array.from(seen.values());
}

export default function QuickMatch() {
  const [events, setEvents] = useState<EventCatalogItem[]>([]);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState<{ x: number; y: number } | null>(null);
  const [exiting, setExiting] = useState<SwipeDir | null>(null);
  const [liked, setLiked] = useState<string[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const startRef = useRef<{ x: number; y: number } | null>(null);
  const pointerIdRef = useRef<number | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([apiListEvents({ limit: 50 }), apiListSavedEvents().catch(() => [])])
      .then(([data, saved]) => {
        const savedSet = new Set(saved.map((s) => s.event_id));
        setSavedIds(savedSet);
        const deduped = dedupe(data).filter((ev) => !savedSet.has(ev.id));
        setEvents(deduped);
        setIndex(0);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load events'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const current = events[index] ?? null;
  const upcoming = useMemo(() => events.slice(index + 1, index + 3), [events, index]);

  const advance = useCallback(
    async (dir: SwipeDir) => {
      if (!current || exiting) return;
      setExiting(dir);
      if (dir === 'right') {
        setLiked((prev) => [...prev, current.id]);
        if (!savedIds.has(current.id)) {
          setSavedIds((prev) => new Set(prev).add(current.id));
          apiSaveEvent({
            event_id: current.id,
            event_title: current.nombre,
            event_venue: current.recinto_nombre,
            event_date: current.fecha,
            event_time: current.hora,
            event_image_url: current.imagen_evento ?? current.artista_imagen,
          }).catch(() => {
            /* network/offline — ignore */
          });
        }
      }
      setTimeout(() => {
        setIndex((i) => i + 1);
        setDrag(null);
        setExiting(null);
        startRef.current = null;
      }, 260);
    },
    [current, exiting],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') advance('left');
      else if (e.key === 'ArrowRight') advance('right');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [advance]);

  const onPointerDown = (e: React.PointerEvent) => {
    if (exiting) return;
    pointerIdRef.current = e.pointerId;
    (e.target as Element).setPointerCapture(e.pointerId);
    startRef.current = { x: e.clientX, y: e.clientY };
    setDrag({ x: 0, y: 0 });
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!startRef.current || pointerIdRef.current !== e.pointerId) return;
    setDrag({
      x: e.clientX - startRef.current.x,
      y: e.clientY - startRef.current.y,
    });
  };

  const onPointerUp = (e: React.PointerEvent) => {
    if (pointerIdRef.current !== e.pointerId) return;
    pointerIdRef.current = null;
    const d = drag;
    startRef.current = null;
    if (!d) return;
    const threshold = 110;
    if (d.x > threshold) {
      advance('right');
    } else if (d.x < -threshold) {
      advance('left');
    } else {
      setDrag(null);
    }
  };

  const cardOffset = drag ?? { x: 0, y: 0 };
  const rotation = cardOffset.x / 18;
  const likeOpacity = Math.min(Math.max(cardOffset.x / 120, 0), 1);
  const nopeOpacity = Math.min(Math.max(-cardOffset.x / 120, 0), 1);

  const exitTransform =
    exiting === 'right'
      ? 'translate(140%, -30%) rotate(25deg)'
      : exiting === 'left'
        ? 'translate(-140%, -30%) rotate(-25deg)'
        : null;

  return (
    <div className="bg-surface-container-low rounded-[2rem] p-6 md:p-10 relative overflow-hidden">
      <div className="flex items-start justify-between mb-6 md:mb-8 gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-bold font-headline tracking-tight flex items-center gap-3">
            <span className="material-symbols-outlined text-primary">style</span>
            Quick Match
          </h2>
          <p className="text-on-surface-variant text-sm mt-1">
            Swipe right to save, left to skip. {liked.length > 0 && `${liked.length} saved this session.`}
          </p>
        </div>
        <button
          onClick={load}
          className="p-3 rounded-full border border-outline-variant/20 hover:border-primary transition-colors"
          aria-label="Reload deck"
          title="Reload deck"
        >
          <span className="material-symbols-outlined text-primary">refresh</span>
        </button>
      </div>

      <div className="relative mx-auto w-full max-w-[360px] md:max-w-[420px] aspect-[3/4]">
        {loading ? (
          <div className="absolute inset-0 rounded-[2rem] bg-surface-container-high animate-pulse" />
        ) : error ? (
          <div className="absolute inset-0 rounded-[2rem] bg-surface-container-high flex items-center justify-center p-8 text-center text-on-surface-variant text-sm">
            {error}
          </div>
        ) : !current ? (
          <div className="absolute inset-0 rounded-[2rem] bg-surface-container-high flex flex-col items-center justify-center p-8 text-center gap-4">
            <span className="material-symbols-outlined text-5xl text-primary">done_all</span>
            <p className="text-on-surface-variant text-sm">
              No more events in the deck. Come back later or reload.
            </p>
            <button
              onClick={load}
              className="bg-primary text-on-primary font-bold px-6 py-2 rounded-full text-sm"
            >
              Reload
            </button>
          </div>
        ) : (
          <>
            {upcoming
              .map((ev, i) => {
                const depth = i + 1;
                const image = ev.imagen_evento ?? ev.artista_imagen ?? IMAGE_FALLBACK;
                const title = ev.nombre ?? 'Evento';
                const locationLine = [ev.recinto_nombre, ev.ciudad].filter(Boolean).join(' • ');
                return (
                  <div
                    key={ev.id}
                    className="absolute inset-0 bg-surface-container-highest rounded-[2rem] border border-outline-variant/10 overflow-hidden shadow-xl"
                    style={{
                      transform: `translateY(${depth * 10}px) scale(${1 - depth * 0.04})`,
                      opacity: 1 - depth * 0.25,
                      zIndex: 0,
                    }}
                  >
                    <img
                      src={image}
                      alt={title}
                      draggable={false}
                      className="w-full h-full object-cover pointer-events-none select-none"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/40 to-transparent" />
                    <div className="absolute bottom-0 left-0 right-0 p-5 pointer-events-none">
                      <h4 className="text-lg font-headline font-extrabold leading-tight truncate">
                        {title}
                      </h4>
                      {locationLine && (
                        <p className="text-on-surface/60 text-xs truncate">{locationLine}</p>
                      )}
                    </div>
                  </div>
                );
              })
              .reverse()}

            <Card
              event={current}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerUp}
              style={{
                transform:
                  exitTransform ??
                  `translate(${cardOffset.x}px, ${cardOffset.y}px) rotate(${rotation}deg)`,
                transition:
                  exiting || !drag ? 'transform 260ms cubic-bezier(0.22, 1, 0.36, 1)' : 'none',
                zIndex: 10,
              }}
              likeOpacity={likeOpacity}
              nopeOpacity={nopeOpacity}
            />
          </>
        )}
      </div>

      {/* Action buttons */}
      {current && (
        <div className="mt-8 flex items-center justify-center gap-4">
          <button
            onClick={() => advance('left')}
            className="w-14 h-14 md:w-16 md:h-16 rounded-full bg-surface-container-high flex items-center justify-center text-error border border-error/20 active:scale-90 transition-transform shadow-xl"
            aria-label="Skip"
          >
            <span className="material-symbols-outlined text-2xl md:text-3xl">close</span>
          </button>
          <button
            onClick={load}
            className="w-11 h-11 rounded-full bg-surface-container flex items-center justify-center text-secondary border border-outline-variant/10 active:scale-90 transition-transform"
            aria-label="Reload"
          >
            <span className="material-symbols-outlined">restart_alt</span>
          </button>
          <button
            onClick={() => advance('right')}
            className="w-14 h-14 md:w-16 md:h-16 rounded-full bg-surface-container-high flex items-center justify-center text-tertiary border border-tertiary/20 active:scale-90 transition-transform shadow-xl"
            aria-label="Save"
          >
            <span
              className="material-symbols-outlined text-2xl md:text-3xl"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              favorite
            </span>
          </button>
        </div>
      )}
    </div>
  );
}

function Card({
  event,
  style,
  likeOpacity,
  nopeOpacity,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onPointerCancel,
}: {
  event: EventCatalogItem;
  style: React.CSSProperties;
  likeOpacity: number;
  nopeOpacity: number;
  onPointerDown: (e: React.PointerEvent) => void;
  onPointerMove: (e: React.PointerEvent) => void;
  onPointerUp: (e: React.PointerEvent) => void;
  onPointerCancel: (e: React.PointerEvent) => void;
}) {
  const image = event.imagen_evento ?? event.artista_imagen ?? IMAGE_FALLBACK;
  const title = event.nombre ?? 'Evento';
  const locationLine = [event.recinto_nombre, event.ciudad].filter(Boolean).join(' • ');
  const dateLine = [event.fecha, event.hora].filter(Boolean).join(' · ');
  const tags = [event.segmento, event.genero].filter((t): t is string => !!t);

  return (
    <div
      className="absolute inset-0 rounded-[2rem] overflow-hidden shadow-2xl bg-surface-container-highest border border-outline-variant/10 cursor-grab active:cursor-grabbing touch-none"
      style={style}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerCancel}
    >
      <img
        src={image}
        alt={title}
        draggable={false}
        className="w-full h-full object-cover pointer-events-none select-none"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/30 to-transparent" />

      <div
        className="absolute top-6 left-6 border-4 border-tertiary text-tertiary px-4 py-2 rounded-xl font-black text-2xl tracking-widest uppercase rotate-[-12deg] pointer-events-none"
        style={{ opacity: likeOpacity }}
      >
        Save
      </div>
      <div
        className="absolute top-6 right-6 border-4 border-error text-error px-4 py-2 rounded-xl font-black text-2xl tracking-widest uppercase rotate-[12deg] pointer-events-none"
        style={{ opacity: nopeOpacity }}
      >
        Skip
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-6 space-y-2 pointer-events-none">
        {tags.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {tags.map((t) => (
              <span
                key={t}
                className="bg-surface-container-lowest/60 backdrop-blur-md text-primary font-bold text-[10px] px-3 py-1 rounded-full border border-primary/20 uppercase tracking-widest"
              >
                {t}
              </span>
            ))}
          </div>
        )}
        <h3 className="text-2xl md:text-3xl font-headline font-extrabold leading-tight">
          {title}
        </h3>
        {locationLine && (
          <p className="text-on-surface/70 text-sm flex items-center gap-1">
            <span className="material-symbols-outlined text-sm">location_on</span>
            {locationLine}
          </p>
        )}
        {dateLine && (
          <p className="text-on-surface/70 text-sm flex items-center gap-1">
            <span className="material-symbols-outlined text-sm">calendar_today</span>
            {dateLine}
          </p>
        )}
      </div>
    </div>
  );
}
