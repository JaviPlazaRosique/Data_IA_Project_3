import { useEffect, useState } from 'react';
import { apiGetInfrastructure, type ServiceCheck } from '../../api';

const STATUS_CONFIG = {
  ok: { label: 'OK', color: 'text-emerald-400', dot: 'bg-emerald-400', border: 'border-emerald-900' },
  degraded: { label: 'Degraded', color: 'text-yellow-400', dot: 'bg-yellow-400', border: 'border-yellow-900' },
  error: { label: 'Error', color: 'text-red-400', dot: 'bg-red-400', border: 'border-red-900' },
  unknown: { label: 'Unknown', color: 'text-gray-400', dot: 'bg-gray-500', border: 'border-gray-800' },
};

const SERVICE_META: Record<string, { label: string; icon: string; description: string }> = {
  'admin-api': { label: 'Admin API', icon: 'admin_panel_settings', description: 'Cloud Run · Admin backend' },
  'portal-api': { label: 'Portal API', icon: 'cloud', description: 'Cloud Run · Portal backend' },
  cloudsql: { label: 'Cloud SQL', icon: 'storage', description: 'PostgreSQL · Base de datos principal' },
  firestore: { label: 'Firestore', icon: 'database', description: 'NoSQL · Catálogo de eventos' },
  bigquery: { label: 'BigQuery', icon: 'analytics', description: 'Data warehouse analítico' },
};

function ServiceCard({ svc }: { svc: ServiceCheck }) {
  const cfg = STATUS_CONFIG[svc.status] ?? STATUS_CONFIG.unknown;
  const meta = SERVICE_META[svc.name] ?? { label: svc.name, icon: 'settings', description: '' };

  return (
    <div className={`bg-gray-900 rounded-xl p-5 border ${cfg.border} flex flex-col gap-3`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-[22px] text-gray-400">{meta.icon}</span>
          <div>
            <p className="text-sm font-semibold text-white">{meta.label}</p>
            <p className="text-xs text-gray-500">{meta.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className={`w-2 h-2 rounded-full ${cfg.dot} animate-pulse`} />
          <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-500">
        {svc.latency_ms !== null && (
          <span>
            <span className="text-gray-300 font-medium">{svc.latency_ms} ms</span> latencia
          </span>
        )}
        {svc.detail && (
          <span className="text-red-400 truncate max-w-[200px]" title={svc.detail}>
            {svc.detail}
          </span>
        )}
      </div>
    </div>
  );
}

function OverallBadge({ services }: { services: ServiceCheck[] }) {
  const hasError = services.some((s) => s.status === 'error');
  const hasDegraded = services.some((s) => s.status === 'degraded');
  const allOk = !hasError && !hasDegraded;

  if (allOk) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-900/40 border border-emerald-800">
        <span className="w-2 h-2 rounded-full bg-emerald-400" />
        <span className="text-xs font-medium text-emerald-300">Todos los servicios operativos</span>
      </div>
    );
  }
  if (hasError) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-900/40 border border-red-800">
        <span className="w-2 h-2 rounded-full bg-red-400" />
        <span className="text-xs font-medium text-red-300">Incidencia detectada</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-900/40 border border-yellow-800">
      <span className="w-2 h-2 rounded-full bg-yellow-400" />
      <span className="text-xs font-medium text-yellow-300">Servicio degradado</span>
    </div>
  );
}

interface Props {
  refreshTick?: number;
}

export function InfrastructureTab({ refreshTick }: Props) {
  const [data, setData] = useState<{ services: ServiceCheck[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiGetInfrastructure()
      .then((d) => { setData(d); setLastUpdated(new Date()); })
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [refreshTick]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <p className="text-xs text-gray-500">Estado en tiempo real de los servicios GCP</p>
          {lastUpdated && (
            <p className="text-xs text-gray-600">
              Actualizado {lastUpdated.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </p>
          )}
        </div>
        {data && <OverallBadge services={data.services} />}
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {loading && !data && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-gray-900 rounded-xl p-5 border border-gray-800 h-24 animate-pulse" />
          ))}
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data.services.map((svc) => (
            <ServiceCard key={svc.name} svc={svc} />
          ))}
        </div>
      )}

      <div className="mt-2 p-4 bg-gray-900/50 rounded-xl border border-gray-800">
        <p className="text-xs text-gray-500 font-medium mb-3 uppercase tracking-wider">Servicios GCP del proyecto</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs text-gray-400">
          {[
            { icon: 'cloud', label: 'Cloud Run', detail: 'portal-api · admin-api' },
            { icon: 'storage', label: 'Cloud SQL', detail: 'PostgreSQL (europe-west1)' },
            { icon: 'database', label: 'Firestore', detail: 'Catálogo de eventos' },
            { icon: 'analytics', label: 'BigQuery', detail: 'recomendacion_planes' },
            { icon: 'hub', label: 'Pub/Sub', detail: 'swipe-events' },
            { icon: 'schedule', label: 'Cloud Scheduler', detail: 'Ingesta diaria · dbt pipeline' },
            { icon: 'water', label: 'Dataflow', detail: 'Flex Template ingesta' },
            { icon: 'model_training', label: 'Vertex AI', detail: 'Agent Engine RAG' },
            { icon: 'account_tree', label: 'Cloud Workflows', detail: 'dbt + clustering' },
            { icon: 'task', label: 'Cloud Run Jobs', detail: 'dbt · clustering' },
            { icon: 'send', label: 'Cloud Tasks', detail: 'Valoraciones email' },
            { icon: 'folder', label: 'Cloud Storage', detail: 'Frontends · Dataflow · Staging' },
          ].map((s) => (
            <div key={s.label} className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[14px] text-gray-600">{s.icon}</span>
              <span>
                <span className="text-gray-300">{s.label}</span>
                <span className="text-gray-600"> · {s.detail}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
