import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LanguageContext';
import { SectionLabel } from '../components/np/Primitives';
import {
  apiUpdateMe,
  apiUploadAvatar,
  apiListSavedEvents,
  apiUnsaveEvent,
  type SavedEventRead,
} from '../api';

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const { t } = useLang();
  const [locationDraft, setLocationDraft] = useState(user?.preferred_location ?? '');
  const [savedEvents, setSavedEvents] = useState<SavedEventRead[]>([]);
  const [showAvatarEdit, setShowAvatarEdit] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);

  useEffect(() => {
    setLocationDraft(user?.preferred_location ?? '');
  }, [user?.preferred_location]);

  useEffect(() => {
    apiListSavedEvents()
      .then(setSavedEvents)
      .catch(() => { /* silent */ });
  }, []);

  function handleAvatarFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setAvatarFile(file);
    if (file) {
      setAvatarPreview(URL.createObjectURL(file));
    } else {
      setAvatarPreview(null);
    }
  }

  async function handleAvatarSave() {
    if (!avatarFile) return;
    setAvatarUploading(true);
    try {
      const updated = await apiUploadAvatar(avatarFile);
      setUser(updated);
      setShowAvatarEdit(false);
      setAvatarFile(null);
      setAvatarPreview(null);
    } catch { /* silent */ } finally {
      setAvatarUploading(false);
    }
  }

  async function handleLocationBlur() {
    const value = locationDraft.trim();
    if (value === (user?.preferred_location ?? '')) return;
    try {
      const updated = await apiUpdateMe({ preferred_location: value || null });
      setUser(updated);
    } catch { /* silent */ }
  }

  async function handleUnsave(eventId: string) {
    try {
      await apiUnsaveEvent(eventId);
      setSavedEvents((prev) => prev.filter((e) => e.event_id !== eventId));
    } catch { /* silent */ }
  }

  const categories = user?.preferred_categories ?? [];

  const profileSteps = [
    { label: 'Foto de perfil', done: !!user?.avatar_url },
    { label: 'Nombre completo', done: !!user?.full_name },
    { label: 'Ciudad', done: !!user?.preferred_location },
    { label: 'Categorías', done: categories.length > 0 },
  ];
  const completedSteps = profileSteps.filter((s) => s.done).length;
  const completionPct = Math.round((completedSteps / profileSteps.length) * 100);

  return (
    <div className="bg-surface text-on-surface min-h-screen">
      <TopNav />

      <main className="pt-6 pb-24 px-4 md:px-12">
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
                  <button
                    onClick={() => setShowAvatarEdit(true)}
                    className="absolute bottom-0 right-0 bg-tertiary text-on-tertiary p-1.5 rounded-full shadow-lg border-2 border-surface"
                  >
                    <span className="material-symbols-outlined text-sm block">edit</span>
                  </button>
                </div>
                <div>
                  <SectionLabel>{t.profile_title}</SectionLabel>
                  <h1 className="font-serif text-3xl md:text-5xl tracking-tight text-on-surface mb-2 mt-2">
                    {user?.full_name ?? user?.username}
                  </h1>
                  <div className="flex items-center gap-3">
                    <span className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border border-primary/30">
                      {user?.is_verified ? 'Miembro Verificado' : 'Miembro'}
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
                Sorpréndeme
              </Link>
            </div>
          </header>

          {/* Modal edición de avatar */}
          {showAvatarEdit && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-surface-container-low rounded-[2rem] p-8 w-full max-w-md space-y-4">
                <h3 className="text-lg font-bold">Cambiar foto de perfil</h3>
                <label className="flex flex-col items-center justify-center w-full h-36 border-2 border-dashed border-outline-variant/40 rounded-2xl cursor-pointer hover:border-primary/50 transition-colors bg-surface-container-lowest">
                  {avatarPreview ? (
                    <img src={avatarPreview} alt="Vista previa" className="h-full w-full object-cover rounded-2xl" />
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-on-surface-variant/60">
                      <span className="material-symbols-outlined text-4xl">upload</span>
                      <span className="text-sm">Haz clic para seleccionar una imagen</span>
                      <span className="text-xs">JPEG, PNG, WEBP o GIF</span>
                    </div>
                  )}
                  <input type="file" accept="image/*" className="hidden" onChange={handleAvatarFileChange} />
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => { setShowAvatarEdit(false); setAvatarFile(null); setAvatarPreview(null); }}
                    className="flex-1 border border-outline-variant/30 py-3 rounded-full text-sm font-bold hover:bg-surface-container-high transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleAvatarSave}
                    disabled={!avatarFile || avatarUploading}
                    className="flex-1 bg-primary text-on-primary py-3 rounded-full text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {avatarUploading ? 'Subiendo…' : 'Guardar'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Grid Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left: Preferencias */}
            <section className="lg:col-span-4 space-y-8">
              <div className="bg-surface-container-low p-8 rounded-[2rem] relative group">
                <div className="absolute inset-0 rounded-[2rem] overflow-hidden pointer-events-none">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full group-hover:bg-primary/10 transition-colors" />
                </div>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">tune</span>
                  {t.profile_prefs}
                </h2>
                <div className="space-y-6">
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Categorías</label>
                    <div className="flex flex-wrap gap-2">
                      {categories.length === 0 ? (
                        <span className="text-on-surface-variant/50 text-sm italic">Sin categorías seleccionadas</span>
                      ) : (
                        categories.map((cat) => (
                          <span
                            key={cat}
                            className="px-4 py-2 rounded-xl text-sm font-medium border bg-primary/20 text-primary border-primary/30"
                          >
                            {cat}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-4">Ciudad</label>
                    <div className="bg-surface-container-lowest flex items-center gap-3 p-3 rounded-xl">
                      <span className="material-symbols-outlined text-secondary">location_on</span>
                      <input
                        type="text"
                        value={locationDraft}
                        onChange={(e) => setLocationDraft(e.target.value)}
                        onBlur={handleLocationBlur}
                        placeholder="Ej. Madrid, Barcelona…"
                        className="flex-1 bg-transparent text-sm font-medium focus:outline-none placeholder:text-on-surface-variant/40"
                      />
                    </div>
                  </div>
                </div>
              </div>
              {/* Completitud del perfil */}
              <div className="glass-panel p-8 rounded-[2rem]">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-tertiary">auto_awesome</span>
                  Tu perfil
                </h2>
                <ul className="space-y-2 mb-6">
                  {profileSteps.map((step) => (
                    <li key={step.label} className="flex items-center gap-2 text-sm">
                      <span className={`material-symbols-outlined text-base ${step.done ? 'text-primary' : 'text-on-surface-variant/30'}`}>
                        {step.done ? 'check_circle' : 'radio_button_unchecked'}
                      </span>
                      <span className={step.done ? 'text-on-surface' : 'text-on-surface-variant/50'}>{step.label}</span>
                    </li>
                  ))}
                </ul>
                <div className="h-1 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary transition-all duration-500" style={{ width: `${completionPct}%` }} />
                </div>
                <p className="text-[10px] text-on-surface-variant mt-2 text-right uppercase tracking-tighter">
                  Perfil completado: {completionPct}%
                </p>
              </div>
            </section>

            {/* Right: Eventos guardados */}
            <section className="lg:col-span-8 space-y-12">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-extrabold tracking-tight flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>bookmark</span>
                    {t.profile_saved}
                  </h2>
                  <a href="#" className="text-primary text-sm font-bold hover:underline">Ver todos</a>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {savedEvents.length === 0 && (
                    <p className="text-on-surface-variant/50 text-sm italic col-span-2">Aún no tienes eventos guardados.</p>
                  )}
                  {savedEvents.map((event) => (
                    <Link
                      key={event.id}
                      to={`/event/${event.event_id}`}
                      className="block bg-surface-container-high rounded-[1.5rem] overflow-hidden group hover:translate-y-[-4px] transition-transform duration-300"
                    >
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
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleUnsave(event.event_id);
                          }}
                          className="absolute top-4 right-4 w-8 h-8 bg-surface/80 backdrop-blur-md rounded-full flex items-center justify-center text-on-surface-variant hover:text-error transition-colors"
                          title="Eliminar guardado"
                        >
                          <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                      </div>
                      <div className="p-6">
                        <h3 className="text-lg font-bold mb-1">{event.event_title ?? event.event_id}</h3>
                        <p className="text-on-surface-variant text-xs mb-4">
                          {[event.event_venue, event.event_time].filter(Boolean).join(' • ')}
                        </p>
                        {event.event_url ? (
                          <a
                            href={event.event_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="block text-center w-full border border-outline-variant/30 py-2.5 rounded-full text-xs font-bold hover:bg-on-surface hover:text-surface transition-colors"
                          >
                            Reservar
                          </a>
                        ) : (
                          <button
                            disabled
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
                            className="w-full border border-outline-variant/20 py-2.5 rounded-full text-xs font-bold text-on-surface-variant/50 cursor-not-allowed"
                          >
                            Sin entradas disponibles
                          </button>
                        )}
                      </div>
                    </Link>
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
