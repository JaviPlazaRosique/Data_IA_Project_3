const layers = [
  {
    title: 'Auth',
    color: 'border-blue-800 bg-blue-950/40',
    items: [
      { name: 'Firebase Authentication', desc: 'Email/password, Google, Microsoft OAuth. ID tokens verified on every API call.' },
    ],
  },
  {
    title: 'Frontend',
    color: 'border-violet-800 bg-violet-950/40',
    items: [
      { name: 'Portal (React + Vite)', desc: 'User-facing app — map, swipe, recommendations, AI planner. Deployed on Cloud Run (static).' },
      { name: 'Admin Panel (React + Vite)', desc: 'This app. Admin-only dashboard. Separate deploy.' },
    ],
  },
  {
    title: 'Backend APIs',
    color: 'border-indigo-800 bg-indigo-950/40',
    items: [
      { name: 'Portal API (FastAPI)', desc: 'User auth, events, saved events, swipe events, AI planner, recommendations.' },
      { name: 'Admin API (FastAPI)', desc: 'Admin-only stats, user management, event catalog read, analytics.' },
    ],
  },
  {
    title: 'Data Stores',
    color: 'border-cyan-800 bg-cyan-950/40',
    items: [
      { name: 'Cloud SQL (PostgreSQL)', desc: 'Users, saved events. Private via VPC connector. Accessed via asyncpg.' },
      { name: 'Firestore', desc: 'Event catalog ("eventos" collection). Written by ingestion pipeline, read by APIs.' },
      { name: 'Cloud Storage (GCS)', desc: 'User avatar images.' },
    ],
  },
  {
    title: 'Analytics & ML',
    color: 'border-amber-800 bg-amber-950/40',
    items: [
      { name: 'Pub/Sub', desc: 'Swipe events published in real time to "swipe-events" topic.' },
      { name: 'BigQuery', desc: 'Swipe events, user preferences, fct_swipes mart. ML recommendations table in recomendacion_planes_marts.' },
      { name: 'Vertex AI Agent Engine', desc: 'RAG-powered itinerary planner. Invoked via AI Planner chat.' },
    ],
  },
  {
    title: 'Infrastructure',
    color: 'border-gray-700 bg-gray-900/40',
    items: [
      { name: 'Cloud Run', desc: 'All services containerised and deployed here.' },
      { name: 'Cloud Tasks', desc: 'Schedules post-event rating emails.' },
      { name: 'VPC Connector', desc: 'Connects Cloud Run services to private Cloud SQL.' },
    ],
  },
];

export function ArchitectureTab() {
  return (
    <div className="flex flex-col gap-4 max-w-3xl">
      {layers.map((layer) => (
        <div key={layer.title} className={`rounded-xl border p-4 ${layer.color}`}>
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">{layer.title}</p>
          <div className="flex flex-col gap-2">
            {layer.items.map((item) => (
              <div key={item.name}>
                <p className="text-sm font-semibold text-white">{item.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
