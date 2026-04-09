import { useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import SideNav from '../components/layout/SideNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { savedEvents, historyEvents, profileAvatarUrl } from '../data/mockData';

const budgetOptions = ['€', '€€', '€€€', '€€€€'];
const favoriteCategories = ['Immersive Art', 'Techno Operas', 'Speakeasies'];
const locations = [
  { icon: 'apartment', name: 'Mitte District' },
  { icon: 'water', name: 'Kreuzberg Waterfront' },
];

export default function ProfilePage() {
  const [activeBudget, setActiveBudget] = useState('€');
  const [reviewText, setReviewText] = useState('');
  const [pendingRating, setPendingRating] = useState(0);

  return (
    <div className="bg-surface text-on-surface min-h-screen">
      <TopNav />
      <SideNav activeItem="Settings" />

      <main className="lg:ml-64 pt-6 pb-24 px-4 md:px-12">
        <div className="max-w-6xl mx-auto">
          {/* Hero Header */}
          <header className="mb-12 relative">
            <div className="absolute -top-20 -left-20 w-96 h-96 bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
              <div className="flex items-center gap-6">
                <div className="relative group">
                  <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-surface-container-high shadow-2xl">
                    <img src={profileAvatarUrl} alt="Elena Vance" className="w-full h-full object-cover" />
                  </div>
                  <div className="absolute bottom-0 right-0 bg-tertiary text-on-tertiary p-1.5 rounded-full shadow-lg border-2 border-surface">
                    <span className="material-symbols-outlined text-sm block">edit</span>
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl md:text-5xl font-extrabold tracking-tight text-on-surface mb-2">Elena Vance</h1>
                  <div className="flex items-center gap-3">
                    <span className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border border-primary/30">
                      Premium Member
                    </span>
                    <span className="text-on-surface-variant text-sm flex items-center gap-1">
                      <span className="material-symbols-outlined text-base">location_on</span>
                      Berlin, Germany
                    </span>
                  </div>
                </div>
              </div>
              <Link
                to="/planner"
                className="bg-primary text-on-primary font-bold px-8 py-3 rounded-full hover:scale-95 active:opacity-80 transition-transform flex items-center gap-2 w-fit"
              >
                <span className="material-symbols-outlined text-xl">bolt</span>
                Surprise Me
              </Link>
            </div>
          </header>

          {/* Grid Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left: Preferences */}
            <section className="lg:col-span-4 space-y-8">
              <div className="bg-surface-container-low p-8 rounded-[2rem] relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full group-hover:bg-primary/10 transition-colors" />
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">tune</span>
                  Preferences
                </h2>
                <div className="space-y-6">
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Budget Range</label>
                    <div className="bg-surface-container-lowest p-1 rounded-full flex gap-1">
                      {budgetOptions.map((opt) => (
                        <button
                          key={opt}
                          onClick={() => setActiveBudget(opt)}
                          className={`flex-1 py-2 text-xs font-bold rounded-full transition-colors ${
                            activeBudget === opt
                              ? 'bg-surface-container-high text-primary'
                              : 'text-on-surface/40 hover:text-on-surface'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Favorite Categories</label>
                    <div className="flex flex-wrap gap-2">
                      {favoriteCategories.map((cat) => (
                        <span key={cat} className="bg-surface-container-high px-4 py-2 rounded-xl text-sm font-medium border border-outline-variant/10">
                          {cat}
                        </span>
                      ))}
                      <button className="bg-primary/10 text-primary border border-primary/20 px-3 py-2 rounded-xl text-sm">
                        <span className="material-symbols-outlined text-base align-middle">add</span>
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Preferred Locations</label>
                    <div className="space-y-3">
                      {locations.map((loc) => (
                        <div key={loc.name} className="bg-surface-container-lowest flex items-center justify-between p-3 rounded-xl">
                          <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-secondary">{loc.icon}</span>
                            <span className="text-sm font-medium">{loc.name}</span>
                          </div>
                          <span className="material-symbols-outlined text-on-surface-variant text-sm cursor-pointer hover:text-error transition-colors">close</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Curator Insight */}
              <div className="glass-panel p-8 rounded-[2rem]">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-tertiary">auto_awesome</span>
                  Curator Insight
                </h2>
                <p className="text-on-surface-variant text-sm leading-relaxed mb-6">
                  "Elena, your recent visits suggest a growing interest in{' '}
                  <span className="text-primary">Neon-Retroism</span>. We've adjusted your dashboard to prioritize high-contrast sensory experiences."
                </p>
                <div className="h-1 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary w-2/3" />
                </div>
                <p className="text-[10px] text-on-surface-variant mt-2 text-right uppercase tracking-tighter">
                  Profile Alignment: 67% Complete
                </p>
              </div>
            </section>

            {/* Right: History & Saved */}
            <section className="lg:col-span-8 space-y-12">
              {/* Saved Events */}
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-extrabold tracking-tight flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>bookmark</span>
                    Saved Events
                  </h2>
                  <a href="#" className="text-primary text-sm font-bold hover:underline">View All</a>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {savedEvents.map((event) => (
                    <div key={event.id} className="bg-surface-container-high rounded-[1.5rem] overflow-hidden group hover:translate-y-[-4px] transition-transform duration-300">
                      <div className="h-48 w-full overflow-hidden relative">
                        <img
                          src={event.imageUrl}
                          alt={event.title}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                        />
                        <div className="absolute top-4 left-4 bg-surface/80 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                          {event.date}
                        </div>
                      </div>
                      <div className="p-6">
                        <h3 className="text-lg font-bold mb-1">{event.title}</h3>
                        <p className="text-on-surface-variant text-xs mb-4">{event.venue} • {event.time}</p>
                        <button className="w-full border border-outline-variant/30 py-2.5 rounded-full text-xs font-bold hover:bg-on-surface hover:text-surface transition-colors">
                          Book Now
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* History */}
              <div className="space-y-6">
                <h2 className="text-2xl font-extrabold tracking-tight flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary">history</span>
                  Experience History
                </h2>
                <div className="space-y-4">
                  {historyEvents.map((event) => (
                    <div
                      key={event.id}
                      className={`bg-surface-container p-6 rounded-3xl flex flex-col md:flex-row gap-6 ${
                        event.status === 'pending' ? 'border border-primary/20 bg-gradient-to-br from-surface-container to-primary/5' : ''
                      }`}
                    >
                      <div className="w-full md:w-32 h-32 rounded-2xl overflow-hidden flex-shrink-0">
                        <img src={event.imageUrl} alt={event.title} className="w-full h-full object-cover" />
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-bold text-lg">{event.title}</h3>
                            {event.status === 'reviewed' ? (
                              <p className="text-on-surface-variant text-sm">{event.visitedDate}</p>
                            ) : (
                              <p className="text-primary text-sm font-medium">Pending Review</p>
                            )}
                          </div>
                          {event.status === 'reviewed' && (
                            <div className="flex gap-1 text-tertiary">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <span
                                  key={star}
                                  className="material-symbols-outlined"
                                  style={star <= event.rating ? { fontVariationSettings: "'FILL' 1" } : {}}
                                >
                                  star
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {event.status === 'reviewed' && event.review && (
                          <>
                            <div className="bg-surface-container-lowest p-4 rounded-xl mb-4">
                              <p className="text-on-surface-variant text-sm italic">{event.review}</p>
                            </div>
                            <button className="text-primary text-xs font-bold uppercase tracking-widest flex items-center gap-1 hover:gap-2 transition-all">
                              Edit Review
                              <span className="material-symbols-outlined text-sm">chevron_right</span>
                            </button>
                          </>
                        )}

                        {event.status === 'pending' && (
                          <>
                            <div className="flex gap-1 mb-4">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <span
                                  key={star}
                                  onClick={() => setPendingRating(star)}
                                  className={`material-symbols-outlined cursor-pointer transition-colors ${
                                    star <= pendingRating ? 'text-tertiary' : 'text-on-surface-variant/40 hover:text-tertiary'
                                  }`}
                                  style={star <= pendingRating ? { fontVariationSettings: "'FILL' 1" } : {}}
                                >
                                  star
                                </span>
                              ))}
                            </div>
                            <textarea
                              value={reviewText}
                              onChange={(e) => setReviewText(e.target.value)}
                              className="w-full bg-surface-container-lowest rounded-xl border-none text-sm text-on-surface p-3 mb-3 focus:outline-none focus:ring-1 focus:ring-secondary/50 placeholder:text-on-surface-variant/30 min-h-[80px] resize-none"
                              placeholder="Tell the Curator about your experience..."
                            />
                            <button className="bg-tertiary text-on-tertiary px-6 py-2 rounded-full text-xs font-bold hover:opacity-90 transition-opacity">
                              Post Review
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>

      {/* AI Chat Float */}
      <div className="fixed bottom-20 md:bottom-8 right-8 z-[60]">
        <Link
          to="/planner"
          className="glass-panel w-16 h-16 rounded-2xl flex items-center justify-center text-primary shadow-2xl hover:scale-110 active:scale-95 transition-all relative"
        >
          <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-tertiary rounded-full animate-pulse border-2 border-surface" />
        </Link>
      </div>

      <BottomNav />
      <Footer />
    </div>
  );
}
