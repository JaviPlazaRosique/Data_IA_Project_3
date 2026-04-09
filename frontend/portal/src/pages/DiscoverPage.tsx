import { useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { featuredEvents, categories, heroEvent } from '../data/mockData';

export default function DiscoverPage() {
  const [aiDismissed, setAiDismissed] = useState(false);

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <TopNav />

      <main className="min-h-screen">
        {/* Hero Section */}
        <section className="relative pt-12 pb-24 px-4 md:px-8 hero-gradient">
          <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-8 md:gap-16">
            <div className="flex-1 space-y-8">
              <div className="space-y-4">
                <span className="text-tertiary font-bold tracking-widest text-xs uppercase font-label">
                  The Digital Concierge
                </span>
                <h1 className="text-4xl sm:text-6xl md:text-8xl font-black font-headline leading-[0.9] tracking-tighter text-on-surface">
                  Curation <br />
                  <span className="text-primary">Evolved.</span>
                </h1>
                <p className="text-on-surface-variant text-lg max-w-md font-body leading-relaxed">
                  A late-night portal to the city's most exclusive happenings. Managed by AI, refined by your taste.
                </p>
              </div>
              <div className="flex flex-wrap gap-4 pt-4">
                <Link
                  to="/planner"
                  className="bg-tertiary text-on-tertiary-fixed px-8 py-4 rounded-full font-bold flex items-center gap-2 hover:scale-95 transition-transform"
                >
                  <span className="material-symbols-outlined">auto_awesome</span>
                  Surprise Me
                </Link>
                <button className="bg-surface-container-high text-on-surface px-8 py-4 rounded-full font-bold border border-outline-variant/20 hover:bg-surface-container-highest transition-colors">
                  Explore All
                </button>
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
              {categories.map((cat, i) => (
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
              <h2 className="text-2xl md:text-4xl font-bold font-headline tracking-tight">Curated for Tonight</h2>
              <div className="h-[2px] flex-1 bg-outline-variant/20" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {featuredEvents.map((event) => (
                <div key={event.id} className="bg-surface-container-high rounded-3xl overflow-hidden group">
                  <div className="aspect-video relative overflow-hidden">
                    <img
                      src={event.imageUrl}
                      alt={event.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute top-4 right-4 glass-effect px-3 py-1.5 rounded-full flex items-center gap-2">
                      <span className={`material-symbols-outlined text-sm ${
                        event.weatherIcon === 'cloud' ? 'text-secondary'
                        : event.weatherIcon === 'water_drop' ? 'text-primary'
                        : 'text-tertiary'
                      }`}>
                        {event.weatherIcon}
                      </span>
                      <span className="text-xs font-bold text-on-surface">{event.weather}</span>
                    </div>
                  </div>
                  <div className="p-8 space-y-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-2xl font-bold font-headline">{event.title}</h4>
                        <p className="text-on-surface-variant font-body">{event.venue}</p>
                      </div>
                      <span className="text-tertiary font-bold">{event.price}</span>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {event.tags.map((tag) => (
                        <span key={tag} className="bg-surface-variant px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase opacity-80">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <Link
                      to="/event/1"
                      className={`block w-full py-4 rounded-full border border-outline-variant/20 font-bold text-center hover:bg-primary hover:text-on-primary transition-all ${
                        event.disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''
                      }`}
                    >
                      {event.buttonLabel}
                    </Link>
                  </div>
                </div>
              ))}
            </div>
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
