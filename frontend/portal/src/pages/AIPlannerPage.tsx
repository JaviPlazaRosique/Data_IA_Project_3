import { useState, useRef, useEffect } from 'react';
import TopNav from '../components/layout/TopNav';
import BottomNav from '../components/layout/BottomNav';
import { itineraryMapImage } from '../data/mockData';
import { useLang } from '../context/LanguageContext';
import { SectionLabel } from '../components/np/Primitives';
import { apiSendAgentMessage, apiListRecommendations, type ClusterRecommendationRead } from '../api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  cards?: { id: string; icon: string; label: string; title: string; imageUrl?: string; badge?: string }[];
}

const SEGMENT_ICON: Record<string, string> = {
  Music: 'music_note',
  Sports: 'sports',
  Arts_Theatre: 'theater_comedy',
  Family: 'family_restroom',
};

function RecCard({ rec }: { rec: ClusterRecommendationRead }) {
  const icon = SEGMENT_ICON[rec.segmento ?? ''] ?? 'event';
  const dateLabel = rec.fecha_evento
    ? new Date(rec.fecha_evento).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })
    : null;
  const recommendationBadge = rec.recommendation_reason
    ?? (rec.cluster_source === 'cold_start' ? 'Plan destacado' : null);

  return (
    <div className="bg-surface-container rounded-2xl border border-outline-variant/10 hover:bg-surface-container-high transition-colors overflow-hidden flex flex-col">
      <div className="bg-primary/10 flex items-center justify-center h-24">
        <span className="material-symbols-outlined text-5xl text-primary">{icon}</span>
      </div>
      <div className="p-4 flex flex-col gap-1 flex-1">
        <p className="text-xs font-black uppercase tracking-wide text-on-surface-variant">
          {rec.genero ?? rec.segmento ?? '—'}
        </p>
        <p className="text-sm font-semibold leading-snug line-clamp-2 flex-1">
          {rec.event_name ?? 'Evento'}
        </p>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-on-surface-variant pt-1">
          {dateLabel && (
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-xs">calendar_today</span>
              {dateLabel}
            </span>
          )}
          {rec.ciudad && (
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-xs">location_on</span>
              {rec.ciudad}
            </span>
          )}
          {rec.recinto_nombre && (
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-xs">stadium</span>
              <span className="truncate max-w-[120px]">{rec.recinto_nombre}</span>
            </span>
          )}
        </div>
        {recommendationBadge && (
          <span className="mt-1 self-start text-[10px] font-bold uppercase tracking-wide bg-secondary/10 text-secondary px-2 py-0.5 rounded-full">
            {recommendationBadge}
          </span>
        )}
      </div>
    </div>
  );
}

export default function AIPlannerPage() {
  const { t } = useLang();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [agentSessionId, setAgentSessionId] = useState(
    () => `planner-${globalThis.crypto?.randomUUID?.() ?? Date.now().toString()}`
  );
  const [showItinerary, setShowItinerary] = useState(false);
  const [mode, setMode] = useState<'surprise' | 'idea' | null>(null);
  const [surpriseRecs, setSurpriseRecs] = useState<ClusterRecommendationRead[]>([]);
  const [surpriseLoading, setSurpriseLoading] = useState(false);
  const [surpriseError, setSurpriseError] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleSelectMode(selected: 'surprise' | 'idea') {
    setMode(selected);
    if (selected === 'surprise') {
      setSurpriseRecs([]);
      setSurpriseError(false);
      setSurpriseLoading(true);
      apiListRecommendations(10)
        .then(setSurpriseRecs)
        .catch(() => setSurpriseError(true))
        .finally(() => setSurpriseLoading(false));
    }
  }

  function handleBack() {
    setMode(null);
    setMessages([]);
    setSurpriseRecs([]);
    setSurpriseError(false);
  }

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isSending) return;
    const timestamp = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    const newMsg: Message = { id: Date.now().toString(), role: 'user', content: text, timestamp };
    const updated = [...messages, newMsg];
    setMessages(updated);
    setInput('');

    if (!mode) setMode('idea');

    setIsSending(true);
    try {
      const response = await apiSendAgentMessage({ message: text, session_id: agentSessionId });
      setAgentSessionId(response.session_id);
      setMessages([...updated, {
        id: `${Date.now()}-assistant`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch {
      setMessages([...updated, {
        id: `${Date.now()}-assistant-error`,
        role: 'assistant',
        content: 'No he podido conectar con el asistente ahora mismo. Prueba otra vez en unos segundos.',
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col overflow-hidden h-screen bg-surface">
      <TopNav />

      <main className="flex-1 min-w-0 flex flex-col bg-surface overflow-hidden relative">
        <div className="flex flex-1 overflow-hidden min-w-0 w-full">

          {/* ── Vista principal ── */}
          <section className="flex-1 min-w-0 w-full flex flex-col bg-surface relative overflow-hidden">

            {/* ── Pantalla inicial: elegir modo ── */}
            {mode === null && (
              <div className="flex flex-col items-center justify-center h-full px-4 md:px-8 pt-12 pb-8 gap-10">
                <div className="text-center space-y-3">
                  <SectionLabel>{t.nav.planner}</SectionLabel>
                  <h2 className="font-serif text-3xl md:text-4xl tracking-tight mt-3">{t.planner_greeting}</h2>
                  <p className="text-on-surface-variant text-sm max-w-xs mx-auto">{t.planner_sub}</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 w-full max-w-sm">
                  <button
                    onClick={() => handleSelectMode('surprise')}
                    className="flex-1 flex flex-col items-center gap-3 bg-primary text-on-primary rounded-[2rem] px-6 py-8 hover:opacity-90 active:scale-95 transition-all shadow-lg"
                  >
                    <span className="material-symbols-outlined text-4xl">auto_awesome</span>
                    <span className="font-bold text-lg">Sorpresa</span>
                    <span className="text-xs opacity-75 text-center">Déjame elegir por ti</span>
                  </button>
                  <button
                    onClick={() => handleSelectMode('idea')}
                    className="flex-1 flex flex-col items-center gap-3 bg-surface-container-low border border-outline-variant/20 rounded-[2rem] px-6 py-8 hover:bg-surface-container-high active:scale-95 transition-all"
                  >
                    <span className="material-symbols-outlined text-4xl text-secondary">edit_note</span>
                    <span className="font-bold text-lg">Mi idea</span>
                    <span className="text-xs text-on-surface-variant text-center">Cuéntame qué tienes en mente</span>
                  </button>
                </div>
              </div>
            )}

            {/* ── Vista Sorpresa: grid de recomendaciones ── */}
            {mode === 'surprise' && (
              <div className="flex flex-col flex-1 overflow-hidden">
                {/* Cabecera */}
                <div className="flex items-center gap-3 px-4 md:px-8 pt-6 pb-4 border-b border-outline-variant/10">
                  <button
                    onClick={handleBack}
                    className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors"
                  >
                    <span className="material-symbols-outlined text-base">arrow_back</span>
                  </button>
                  <span className="material-symbols-outlined text-primary">auto_awesome</span>
                  <div>
                    <p className="font-bold text-sm">Elegido para ti</p>
                    <p className="text-xs text-on-surface-variant">Basado en tus gustos y los de tu grupo</p>
                  </div>
                </div>

                {/* Contenido */}
                <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 pb-24 md:pb-6">
                  {surpriseLoading && (
                    <div className="flex flex-col items-center justify-center h-48 gap-4 text-on-surface-variant">
                      <span className="w-3 h-3 rounded-full bg-primary animate-pulse" />
                      <p className="text-sm">Buscando planes para ti...</p>
                    </div>
                  )}
                  {surpriseError && (
                    <div className="flex flex-col items-center justify-center h-48 gap-4">
                      <span className="material-symbols-outlined text-3xl text-error">error_outline</span>
                      <p className="text-sm text-on-surface-variant text-center">
                        No se pudieron cargar las recomendaciones.<br />Prueba de nuevo en unos segundos.
                      </p>
                      <button
                        onClick={() => handleSelectMode('surprise')}
                        className="px-4 py-2 rounded-full border border-outline-variant/30 text-sm hover:bg-surface-container-high transition-colors"
                      >
                        Reintentar
                      </button>
                    </div>
                  )}
                  {!surpriseLoading && !surpriseError && surpriseRecs.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-48 gap-4 text-on-surface-variant">
                      <span className="material-symbols-outlined text-3xl">inbox</span>
                      <p className="text-sm text-center">Aún no tenemos recomendaciones personalizadas.<br />¡Haz swipe para que aprendamos tus gustos!</p>
                    </div>
                  )}
                  {!surpriseLoading && surpriseRecs.length > 0 && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                      {surpriseRecs.map((rec) => (
                        <RecCard key={rec.event_id} rec={rec} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── Vista Chat (Mi idea) ── */}
            {mode === 'idea' && (
              <div className="flex flex-col flex-1 overflow-hidden">
                <div className="flex-1 overflow-y-auto overflow-x-hidden py-6 space-y-6">
                  {messages.length === 0 && (
                    <div className="flex items-center gap-3 px-4 md:px-8">
                      <button
                        onClick={handleBack}
                        className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors"
                      >
                        <span className="material-symbols-outlined text-base">arrow_back</span>
                      </button>
                      <div>
                        <SectionLabel>{t.nav.planner}</SectionLabel>
                        <h2 className="font-serif text-2xl md:text-3xl tracking-tight mt-1">{t.planner_greeting}</h2>
                        <p className="text-on-surface-variant text-sm mt-1 max-w-xl">{t.planner_sub}</p>
                      </div>
                    </div>
                  )}
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-4 w-full px-4 md:px-8 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                          msg.role === 'assistant'
                            ? 'bg-primary-container'
                            : 'bg-surface-container-highest border border-outline-variant/20'
                        }`}
                      >
                        <span className={`material-symbols-outlined ${msg.role === 'assistant' ? 'text-on-primary-container' : 'text-tertiary'}`}>
                          {msg.role === 'assistant' ? 'smart_toy' : 'person'}
                        </span>
                      </div>
                      <div className={`space-y-4 min-w-0 max-w-[85%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                        <div
                          className={`p-4 rounded-2xl border backdrop-blur-md ${
                            msg.role === 'assistant'
                              ? 'bg-surface-container-high rounded-tl-none border-outline-variant/15'
                              : 'bg-primary/10 rounded-tr-none border-primary/20'
                          }`}
                        >
                          <p className="text-sm leading-relaxed text-on-surface break-words">{msg.content}</p>
                        </div>
                        {msg.timestamp && (
                          <span className="text-[10px] text-on-surface-variant px-1 uppercase tracking-widest">
                            {msg.role === 'assistant' ? 'Assistant' : 'You'} • {msg.timestamp}
                          </span>
                        )}
                        {msg.cards && (
                          <div className="flex gap-3 mt-2 overflow-x-auto pb-2 no-scrollbar w-full min-w-0">
                            {msg.cards.map((card) => (
                              <div
                                key={card.id}
                                onClick={() => setShowItinerary(true)}
                                className="flex-shrink-0 w-48 bg-surface-container rounded-2xl border border-outline-variant/10 hover:bg-surface-container-high transition-colors cursor-pointer overflow-hidden"
                              >
                                {card.imageUrl && (
                                  <div className="h-28 overflow-hidden relative">
                                    <img src={card.imageUrl} alt={card.title} className="w-full h-full object-cover" />
                                    {card.badge && (
                                      <span className="absolute top-2 right-2 bg-tertiary text-on-tertiary-fixed px-2 py-0.5 rounded-full text-[10px] font-bold">
                                        {card.badge}
                                      </span>
                                    )}
                                  </div>
                                )}
                                <div className="p-4">
                                  <span className={`material-symbols-outlined text-xl mb-2 ${card.icon === 'restaurant' ? 'text-tertiary' : 'text-primary'}`}>
                                    {card.icon}
                                  </span>
                                  <h4 className="text-xs font-bold uppercase tracking-tight text-on-surface-variant mb-1">{card.label}</h4>
                                  <p className="text-sm font-semibold">{card.title}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {isSending && (
                    <div className="flex gap-4 w-full px-4 md:px-8">
                      <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-primary-container">
                        <span className="material-symbols-outlined text-on-primary-container">smart_toy</span>
                      </div>
                      <div className="p-4 rounded-2xl rounded-tl-none border border-outline-variant/15 bg-surface-container-high">
                        <div className="flex items-center gap-2 text-sm text-on-surface-variant">
                          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                          Pensando en planes reales...
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="px-4 md:px-8 py-6 pb-20 md:pb-6 bg-surface/80 backdrop-blur-xl border-t border-outline-variant/10">
                  <div className="relative group">
                    <div className="absolute inset-0 bg-primary/10 blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity" />
                    <div className="relative bg-surface-container-lowest rounded-2xl flex items-center px-4 border border-outline-variant/20 focus-within:border-secondary transition-all">
                      <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="flex-1 bg-transparent border-none focus:outline-none text-sm py-4 text-on-surface placeholder:text-on-surface-variant/50"
                        placeholder={t.planner_placeholder}
                      />
                      <button
                        onClick={handleSend}
                        disabled={isSending}
                        className="w-10 h-10 bg-primary text-on-primary rounded-xl flex items-center justify-center hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:active:scale-100"
                      >
                        <span className="material-symbols-outlined">{isSending ? 'hourglass_top' : 'send'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Right Panel: Current Itinerary */}
          {showItinerary && (
            <aside className="fixed inset-0 z-[200] xl:relative xl:inset-auto xl:z-auto flex w-full xl:w-[420px] bg-surface-container-low border-l border-outline-variant/10 flex-col">
              <div className="p-8 space-y-8 overflow-y-auto">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="inline-block px-3 py-1 bg-tertiary/10 text-tertiary text-[10px] font-black uppercase tracking-[0.2em] rounded-full">
                      Current Itinerary
                    </div>
                    <button
                      onClick={() => setShowItinerary(false)}
                      className="w-8 h-8 flex items-center justify-center rounded-full bg-surface-container-high hover:bg-surface-container-highest transition-colors text-on-surface/60"
                    >
                      <span className="material-symbols-outlined text-base">close</span>
                    </button>
                  </div>
                  <h2 className="text-3xl font-extrabold font-headline leading-tight">Neon Noir Tokyo</h2>
                  <div className="flex items-center gap-4 text-on-surface-variant text-sm">
                    <div className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-sm">calendar_today</span>
                      <span>Nov 24, 2024</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-sm">location_on</span>
                      <span>Shibuya, Tokyo</span>
                    </div>
                  </div>
                </div>

                <div className="relative h-48 bg-surface-container-high rounded-3xl overflow-hidden group">
                  <img
                    src={itineraryMapImage}
                    alt="Tokyo Shibuya map"
                    className="w-full h-full object-cover opacity-60 group-hover:scale-105 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-surface-container-low via-transparent to-transparent" />
                  <div className="absolute bottom-4 left-4 flex items-center gap-2 bg-surface/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-outline-variant/20">
                    <span className="material-symbols-outlined text-xs text-primary">navigation</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider">3 Stops Planned</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-surface-container p-5 rounded-3xl border border-outline-variant/10">
                    <div className="flex justify-between items-start mb-2">
                      <span className="material-symbols-outlined text-secondary">cloudy_snowing</span>
                      <span className="text-xs font-bold text-on-surface-variant">14°C</span>
                    </div>
                    <p className="text-xs text-on-surface-variant">Light Mist</p>
                    <p className="text-sm font-bold">Bring a coat</p>
                  </div>
                  <div className="bg-surface-container p-5 rounded-3xl border border-outline-variant/10">
                    <div className="flex justify-between items-start mb-2">
                      <span className="material-symbols-outlined text-tertiary">trending_up</span>
                      <span className="text-xs font-bold text-on-surface-variant">Busy</span>
                    </div>
                    <p className="text-xs text-on-surface-variant">Crowd Density</p>
                    <p className="text-sm font-bold">High (Peak)</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <h3 className="text-xs font-black uppercase tracking-widest text-on-surface-variant">Budget Allocation</h3>
                    <span className="text-lg font-bold text-on-surface">$1,450 / $2,000</span>
                  </div>
                  <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-primary to-tertiary w-[72%] rounded-full shadow-[0_0_15px_rgba(182,160,255,0.4)]" />
                  </div>
                  <div className="flex justify-between text-[10px] text-on-surface-variant uppercase font-bold">
                    <span>$0</span>
                    <span>Limit $2k</span>
                  </div>
                </div>

                <button className="w-full py-5 bg-on-surface text-surface-container-lowest font-black rounded-3xl hover:opacity-90 active:scale-[0.98] transition-all font-headline uppercase tracking-widest text-sm">
                  Finalize Experience
                </button>
              </div>
            </aside>
          )}
        </div>

        <footer className="hidden md:flex w-full py-6 border-t border-outline-variant/20 bg-surface">
          <div className="max-w-7xl mx-auto flex justify-between items-center px-8 w-full">
            <p className="text-xs font-medium text-on-surface/40">© 2024 NextPlan. Hecho por Neon Nocturne.</p>
            <div className="flex gap-6">
              {['Privacy Policy', 'Terms of Service', 'Open-Meteo Data', 'Contact'].map((link) => (
                <a key={link} href="#" className="text-xs font-medium text-on-surface/40 hover:text-primary transition-opacity">
                  {link}
                </a>
              ))}
            </div>
          </div>
        </footer>
      </main>
      <BottomNav />
    </div>
  );
}
