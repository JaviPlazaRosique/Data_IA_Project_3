import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import SideNav from '../components/layout/SideNav';
import BottomNav from '../components/layout/BottomNav';
import { chatMessages, quickActions, itineraryMapImage, userAvatarUrl } from '../data/mockData';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  cards?: { id: string; icon: string; label: string; title: string; imageUrl?: string; badge?: string }[];
}

export default function AIPlannerPage() {
  const [messages, setMessages] = useState<Message[]>(chatMessages);
  const [input, setInput] = useState('');
  const [showItinerary, setShowItinerary] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'user',
        content: input,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex overflow-hidden h-screen bg-surface">
      <SideNav activeItem="AI Assistant" />

      <main className="flex-1 min-w-0 md:ml-64 flex flex-col h-full bg-surface overflow-hidden relative">
        {/* Top Nav */}
        <header className="flex justify-between items-center w-full px-4 md:px-8 py-4 bg-surface z-40 border-b border-outline-variant/10">
          <div className="flex items-center gap-8">
            <h1 className="text-2xl font-bold tracking-tighter text-on-surface font-headline">The Electric Curator</h1>
            <nav className="hidden lg:flex items-center gap-6">
              {[
                { label: 'Discover', path: '/' },
                { label: 'Map', path: '/map' },
                { label: 'Planner', path: '/planner', active: true },
                { label: 'Dashboard', path: '/profile' },
              ].map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`text-sm font-medium transition-colors duration-300 ${
                    link.active ? 'text-primary border-b-2 border-primary pb-1' : 'text-on-surface/70 hover:text-tertiary'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <button className="material-symbols-outlined p-2 text-on-surface/70 hover:text-tertiary transition-transform active:scale-95">
              notifications
            </button>
            <Link to="/profile">
              <img src={userAvatarUrl} alt="Profile" className="w-8 h-8 rounded-full object-cover border border-primary/30" />
            </Link>
          </div>
        </header>

        {/* Planning Canvas */}
        <div className="flex flex-1 overflow-hidden min-w-0 w-full">
          {/* Chat Panel */}
          <section className="flex-1 min-w-0 w-full flex flex-col bg-surface relative overflow-hidden">
            <div className="flex-1 overflow-y-auto overflow-x-hidden py-6 space-y-6">
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
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="px-4 md:px-8 py-6 pb-20 md:pb-6 bg-surface/80 backdrop-blur-xl border-t border-outline-variant/10">
              <div className="flex gap-2 mb-4 overflow-x-auto pb-2 no-scrollbar">
                {quickActions.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => setInput(action.label)}
                    className={`flex-shrink-0 whitespace-nowrap px-4 py-2 rounded-full border text-xs font-medium hover:bg-surface-container-high transition-all flex items-center gap-2 ${
                      action.isPrimary
                        ? 'border-primary/30 text-primary bg-primary/5 font-bold hover:bg-primary/10'
                        : 'border-outline-variant/20'
                    }`}
                  >
                    <span className="material-symbols-outlined text-sm">{action.icon}</span>
                    {action.label}
                  </button>
                ))}
              </div>
              <div className="relative group">
                <div className="absolute inset-0 bg-primary/10 blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity" />
                <div className="relative bg-surface-container-lowest rounded-2xl flex items-center px-4 border border-outline-variant/20 focus-within:border-secondary transition-all">
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 bg-transparent border-none focus:outline-none text-sm py-4 text-on-surface placeholder:text-on-surface-variant/50"
                    placeholder="Tell the Curator your desires..."
                  />
                  <button
                    onClick={handleSend}
                    className="w-10 h-10 bg-primary text-on-primary rounded-xl flex items-center justify-center hover:opacity-90 active:scale-95 transition-all"
                  >
                    <span className="material-symbols-outlined">send</span>
                  </button>
                </div>
              </div>
            </div>
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

              {/* Map Preview */}
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

              {/* Weather & Crowd */}
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

              {/* Budget */}
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

              {/* Vibe Sync */}
              <div className="space-y-4">
                <h3 className="text-xs font-black uppercase tracking-widest text-on-surface-variant">Vibe Sync</h3>
                <div className="space-y-3">
                  {[
                    { left: 'Chaos', right: 'Order', pos: 'left-1/4', color: 'bg-tertiary shadow-[0_0_8px_#ff946e]' },
                    { left: 'Public', right: 'Hidden', pos: 'right-1/3', color: 'bg-primary shadow-[0_0_8px_#b6a0ff]' },
                  ].map((vibe, i) => (
                    <div key={i} className="flex items-center gap-4">
                      <span className="text-[10px] w-12 font-bold opacity-50 uppercase">{vibe.left}</span>
                      <div className="flex-1 h-1 bg-surface-container-highest rounded-full relative">
                        <div className={`absolute -top-1 w-3 h-3 rounded-full ${vibe.pos} ${vibe.color}`} />
                      </div>
                      <span className="text-[10px] w-12 font-bold opacity-50 uppercase text-right">{vibe.right}</span>
                    </div>
                  ))}
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
            <p className="text-xs font-medium text-on-surface/40">© 2024 The Electric Curator. Powered by Neon Nocturne.</p>
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
