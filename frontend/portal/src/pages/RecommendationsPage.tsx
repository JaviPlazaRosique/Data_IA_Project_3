import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import BottomNav from '../components/layout/BottomNav';
import Footer from '../components/layout/Footer';
import {
  apiListClusterRecommendations,
  cleanLabel,
  type ClusterRecommendationRead,
} from '../api';

const dateFormatter = new Intl.DateTimeFormat('es-ES', {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
});

function formatDate(value: string | null): string {
  if (!value) return 'Fecha por confirmar';
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return dateFormatter.format(parsed);
}

function sourceLabel(source: string): string {
  if (source === 'own_cluster') return 'Tu cluster';
  if (source === 'neighbor_cluster') return 'Cluster cercano';
  return source.replaceAll('_', ' ');
}

function recommendationReason(item: ClusterRecommendationRead): string {
  const category = [cleanLabel(item.segmento), cleanLabel(item.genero)]
    .filter(Boolean)
    .join(' / ');
  const base = item.cluster_source === 'own_cluster'
    ? 'Encaja con tus gustos principales'
    : 'Amplía tu radar desde gustos cercanos';
  return category ? `${base}: ${category}` : base;
}

function RecommendationSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      {Array.from({ length: 6 }, (_, index) => (
        <div key={index} className="h-72 rounded-[2rem] bg-surface-container-low animate-pulse" />
      ))}
    </div>
  );
}

function RecommendationCard({ item }: { item: ClusterRecommendationRead }) {
  const score = Math.round(item.recommendation_score * 100);
  return (
    <Link
      to={`/event/${item.event_id}`}
      className="group relative overflow-hidden rounded-[2rem] bg-surface-container-low border border-outline-variant/20 p-6 min-h-[18rem] flex flex-col justify-between hover:-translate-y-1 hover:border-tertiary/40 transition-all duration-300"
    >
      <div className="absolute -top-20 -right-16 h-48 w-48 rounded-full bg-tertiary/15 blur-3xl group-hover:bg-tertiary/25 transition-colors" />
      <div className="relative z-10">
        <div className="flex items-center justify-between gap-3 mb-8">
          <span className="inline-flex items-center gap-2 rounded-full bg-surface-container-high px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-tertiary">
            <span className="material-symbols-outlined text-sm">hub</span>
            {sourceLabel(item.cluster_source)}
          </span>
          <span className="rounded-full border border-outline-variant/30 px-3 py-1 text-[10px] font-bold text-on-surface-variant">
            #{item.recommendation_rank}
          </span>
        </div>
        <p className="text-xs font-bold uppercase tracking-[0.24em] text-on-surface-variant mb-3">
          {formatDate(item.fecha_evento)}
        </p>
        <h2 className="font-serif text-2xl leading-tight text-on-surface mb-4">
          {item.event_name ?? item.event_id}
        </h2>
        <p className="text-sm text-on-surface-variant leading-6">
          {recommendationReason(item)}
        </p>
      </div>
      <div className="relative z-10 flex items-end justify-between gap-4 pt-8">
        <div>
          <p className="text-sm font-bold text-on-surface">
            {[item.recinto_nombre, item.ciudad].filter(Boolean).join(' · ') || 'Ubicación por confirmar'}
          </p>
          {item.subgenero && cleanLabel(item.subgenero) && (
            <p className="text-xs text-on-surface-variant mt-1">{cleanLabel(item.subgenero)}</p>
          )}
        </div>
        <div className="shrink-0 text-right">
          <p className="text-[10px] uppercase tracking-widest text-on-surface-variant">match</p>
          <p className="text-2xl font-black text-tertiary">{score}</p>
        </div>
      </div>
    </Link>
  );
}

export default function RecommendationsPage() {
  const [items, setItems] = useState<ClusterRecommendationRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiListClusterRecommendations(30)
      .then((data) => {
        if (!cancelled) {
          setItems(data);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) setError('No he podido cargar tus recomendaciones clusterizadas.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <TopNav />
      <main className="px-4 md:px-12 pt-8 pb-28">
        <div className="max-w-7xl mx-auto">
          <section className="relative overflow-hidden rounded-[2.5rem] bg-surface-container-low px-6 py-10 md:px-12 md:py-14 mb-10 border border-outline-variant/20">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,148,110,0.22),transparent_34%),radial-gradient(circle_at_bottom_left,rgba(138,153,254,0.20),transparent_36%)]" />
            <div className="relative z-10 max-w-3xl">
              <span className="inline-flex items-center gap-2 rounded-full bg-surface/70 px-4 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-tertiary mb-6">
                <span className="material-symbols-outlined text-base">auto_awesome</span>
                Recomendaciones por cluster
              </span>
              <h1 className="font-serif text-4xl md:text-6xl leading-none tracking-tight mb-5">
                Planes elegidos por gente con gustos parecidos a los tuyos.
              </h1>
              <p className="text-on-surface-variant max-w-2xl leading-7">
                Cruzamos tus swipes con perfiles cercanos para proponerte eventos de tu cluster y de clusters vecinos.
              </p>
            </div>
          </section>

          {loading && <RecommendationSkeleton />}

          {!loading && error && (
            <div className="rounded-[2rem] bg-error/10 border border-error/20 p-8 text-error">
              <p className="font-bold">{error}</p>
              <p className="text-sm mt-2">Prueba de nuevo cuando el backend tenga acceso a BigQuery.</p>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="rounded-[2rem] bg-surface-container-low border border-outline-variant/20 p-10 text-center">
              <span className="material-symbols-outlined text-5xl text-on-surface-variant/40 mb-4">explore</span>
              <h2 className="text-2xl font-bold mb-2">Todavía no tengo suficientes señales.</h2>
              <p className="text-on-surface-variant mb-6">
                Haz algunos swipes y volveré con recomendaciones más afinadas.
              </p>
              <Link to="/swipe" className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-bold text-on-primary">
                Empezar a swipar
                <span className="material-symbols-outlined text-base">arrow_forward</span>
              </Link>
            </div>
          )}

          {!loading && !error && items.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {items.map((item) => (
                <RecommendationCard key={`${item.event_id}-${item.recommendation_rank}`} item={item} />
              ))}
            </div>
          )}
        </div>
      </main>
      <BottomNav />
      <Footer />
    </div>
  );
}
