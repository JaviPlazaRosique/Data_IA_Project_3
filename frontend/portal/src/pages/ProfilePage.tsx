import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import SideNav from '../components/layout/SideNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { useAuth } from '../context/AuthContext';
import {
  apiUpdateMe,
  apiListSavedEvents,
  apiUnsaveEvent,
  apiListMyReviews,
  apiUpdateReview,
  type SavedEventRead,
  type EventReviewRead,
} from '../api';

const budgetOptions = ['€', '€€', '€€€', '€€€€'];
const favoriteCategories = ['Immersive Art', 'Techno Operas', 'Speakeasies'];

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [activeBudget, setActiveBudget] = useState(user?.preferred_budget ?? '€');
  const [savedEvents, setSavedEvents] = useState<SavedEventRead[]>([]);
  const [myReviews, setMyReviews] = useState<EventReviewRead[]>([]);

  useEffect(() => {
    Promise.all([apiListSavedEvents(), apiListMyReviews()])
      .then(([events, reviews]) => {
        setSavedEvents(events);
        setMyReviews(reviews);
      })
      .catch(() => { /* silent */ });
  }, []);

  async function handleBudgetChange(opt: string) {
    setActiveBudget(opt);
    try {
      const updated = await apiUpdateMe({ preferred_budget: opt });
      setUser(updated);
    } catch { /* silent */ }
  }

  async function handleUnsave(eventId: string) {
    try {
      await apiUnsaveEvent(eventId);
      setSavedEvents((prev) => prev.filter((e) => e.event_id !== eventId));
    } catch { /* silent */ }
  }

  async function handleEditReview(reviewId: string, rating: number, text: string) {
    try {
      const updated = await apiUpdateReview(reviewId, {
        rating,
        review_text: text || null,
      });
      setMyReviews((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } catch { /* silent */ }
  }

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
                  <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-surface-container-high shadow-2xl bg-surface-container-high flex items-center justify-center">
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={user.full_name ?? user?.username} className="w-full h-full object-cover" />
                    ) : (
                      <span className="material-symbols-outlined text-5xl text-on-surface-variant">account_circle</span>
                    )}
                  </div>
                  <div className="absolute bottom-0 right-0 bg-tertiary text-on-tertiary p-1.5 rounded-full shadow-lg border-2 border-surface">
                    <span className="material-symbols-outlined text-sm block">edit</span>
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl md:text-5xl font-extrabold tracking-tight text-on-surface mb-2">
                    {user?.full_name ?? user?.username}
                  </h1>
                  <div className="flex items-center gap-3">
                    <span className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border border-primary/30">
                      {user?.is_verified ? 'Verified Member' : 'Member'}
                    </span>
                    {user?.preferred_location && (
                      <span className="text-on-surface-variant text-sm flex items-center gap-1">
                        <span className="material-symbols-outlined text-base">location_on</span>
                        {user.preferred_location}
                      </span>
                    )}
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
                          onClick={() => handleBudgetChange(opt)}
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
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Preferred Location</label>
                    <div className="space-y-3">
                      {user?.preferred_location ? (
                        <div className="bg-surface-container-lowest flex items-center justify-between p-3 rounded-xl">
                          <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-secondary">location_on</span>
                            <span className="text-sm font-medium">{user.preferred_location}</span>
                          </div>
                          <button
                            onClick={async () => {
                              try {
                                const updated = await apiUpdateMe({ preferred_location: null });
                                setUser(updated);
                              } catch { /* silent */ }
                            }}
                            className="material-symbols-outlined text-on-surface-variant text-sm cursor-pointer hover:text-error transition-colors"
                          >close</button>
                        </div>
                      ) : (
                        <p className="text-on-surface-variant/50 text-sm italic">No location set</p>
                      )}
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
                  {savedEvents.length === 0 && (
                    <p className="text-on-surface-variant/50 text-sm italic col-span-2">No saved events yet.</p>
                  )}
                  {savedEvents.map((event) => (
                    <div key={event.id} className="bg-surface-container-high rounded-[1.5rem] overflow-hidden group hover:translate-y-[-4px] transition-transform duration-300">
                      <div className="h-48 w-full overflow-hidden relative">
                        {event.event_image_url ? (
                          <img
                            src={event.event_image_url}
                            alt={event.event_title ?? event.event_id}
                            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                          />
                        ) : (
                          <div className="w-full h-full bg-surface-container-highest flex items-center justify-center">
                            <span className="material-symbols-outlined text-4xl text-on-surface-variant/30">event</span>
                          </div>
                        )}
                        {event.event_date && (
                          <div className="absolute top-4 left-4 bg-surface/80 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                            {event.event_date}
                          </div>
                        )}
                        <button
                          onClick={() => handleUnsave(event.event_id)}
                          className="absolute top-4 right-4 w-8 h-8 bg-surface/80 backdrop-blur-md rounded-full flex items-center justify-center text-on-surface-variant hover:text-error transition-colors"
                          title="Remove bookmark"
                        >
                          <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                      </div>
                      <div className="p-6">
                        <h3 className="text-lg font-bold mb-1">{event.event_title ?? event.event_id}</h3>
                        <p className="text-on-surface-variant text-xs mb-4">
                          {[event.event_venue, event.event_time].filter(Boolean).join(' • ')}
                        </p>
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
                  {myReviews.length === 0 && (
                    <p className="text-on-surface-variant/50 text-sm italic">No reviews yet. Rate events you've attended.</p>
                  )}
                  {myReviews.map((review) => (
                    <div key={review.id} className="bg-surface-container p-6 rounded-3xl flex flex-col md:flex-row gap-6">
                      <div className="w-full md:w-32 h-32 rounded-2xl overflow-hidden flex-shrink-0 bg-surface-container-highest flex items-center justify-center">
                        <span className="material-symbols-outlined text-4xl text-on-surface-variant/30">event</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-bold text-lg">{review.event_id}</h3>
                            <p className="text-on-surface-variant text-sm">
                              {new Date(review.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                            </p>
                          </div>
                          <div className="flex gap-1 text-tertiary">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <span
                                key={star}
                                className="material-symbols-outlined"
                                style={star <= review.rating ? { fontVariationSettings: "'FILL' 1" } : {}}
                              >
                                star
                              </span>
                            ))}
                          </div>
                        </div>

                        {review.review_text && (
                          <div className="bg-surface-container-lowest p-4 rounded-xl mb-4">
                            <p className="text-on-surface-variant text-sm italic">{review.review_text}</p>
                          </div>
                        )}
                        <button
                          onClick={() => handleEditReview(review.id, review.rating, review.review_text ?? '')}
                          className="text-primary text-xs font-bold uppercase tracking-widest flex items-center gap-1 hover:gap-2 transition-all"
                        >
                          Edit Review
                          <span className="material-symbols-outlined text-sm">chevron_right</span>
                        </button>
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
