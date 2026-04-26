import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiUpdateMe } from '../api';
import { useAuth } from '../context/AuthContext';

const CATEGORIES = [
  {
    name: 'Música',
    icon: 'music_note',
    subcategories: [
      'Dance/Electrónica', 'Flamenco/Rumba', 'Hard Rock/Metal', 'Hip-Hop/R&B',
      'Indie/Alternativo', 'Jazz/Blues', 'Latin', 'Música Clásica', 'Pop/Rock', 'Festival',
    ],
  },
  {
    name: 'Arte y Teatro',
    icon: 'theater_comedy',
    subcategories: ['Ballet/Danza', 'Circo', 'Comedia', 'Magia', 'Musical', 'Ópera'],
  },
  {
    name: 'Deportes',
    icon: 'sports_soccer',
    subcategories: ['Baloncesto', 'Ciclismo', 'Fútbol', 'Motor', 'Tenis'],
  },
  {
    name: 'Familia y otros',
    icon: 'family_restroom',
    subcategories: [
      'Actividades en familia', 'Espectáculos de Magia', 'Parques temáticos',
      'Teatro infantil', 'Visitas Guiadas/Exposiciones',
    ],
  },
] as const;

const QUICK_CITIES = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao', 'Málaga', 'Zaragoza'];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const [step, setStep] = useState<1 | 2>(1);
  const [city, setCity] = useState('');
  const [customCity, setCustomCity] = useState('');
  const [showCustom, setShowCustom] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const effectiveCity = showCustom ? customCity.trim() : city;

  function toggleSub(sub: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(sub) ? next.delete(sub) : next.add(sub);
      return next;
    });
  }

  function selectCity(c: string) {
    setCity(c);
    setShowCustom(false);
  }

  function handleOtherCity() {
    setCity('');
    setShowCustom(true);
  }

  function goToStep2() {
    if (!effectiveCity) return;
    setStep(2);
  }

  async function handleFinish() {
    if (selected.size === 0) return;
    setSaving(true);
    setError('');
    try {
      const updated = await apiUpdateMe({
        preferred_location: effectiveCity,
        preferred_categories: Array.from(selected),
      });
      setUser(updated);
      localStorage.removeItem('np_new_user');
      navigate('/');
    } catch {
      setError('No se pudieron guardar tus preferencias. Inténtalo de nuevo.');
    } finally {
      setSaving(false);
    }
  }

  function handleSkip() {
    localStorage.removeItem('np_new_user');
    navigate('/');
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-14 pb-4">
        <span className="text-xl font-bold tracking-tighter text-tertiary font-headline">NextPlan</span>
        <button
          onClick={handleSkip}
          className="text-xs text-on-surface-variant hover:text-on-surface transition-colors py-2 px-3"
        >
          Saltar
        </button>
      </div>

      {/* Progress dots */}
      <div className="flex justify-center gap-2 pb-8">
        {[1, 2].map((s) => (
          <div
            key={s}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              s === step ? 'w-6 bg-primary' : s < step ? 'w-1.5 bg-primary/40' : 'w-1.5 bg-outline-variant/40'
            }`}
          />
        ))}
      </div>

      {/* Step 1 — Ciudad */}
      {step === 1 && (
        <div className="flex-1 flex flex-col px-5 overflow-y-auto pb-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-on-surface leading-tight mb-2">
              ¿Desde qué ciudad<br />
              <span className="text-primary">planeas salir?</span>
            </h1>
            <p className="text-sm text-on-surface-variant">
              Te mostraremos eventos cerca de ti.
            </p>
          </div>

          <div className="flex flex-wrap gap-3 mb-6">
            {QUICK_CITIES.map((c) => (
              <button
                key={c}
                onClick={() => selectCity(c)}
                className={`px-4 py-2.5 rounded-full text-sm font-medium transition-all border ${
                  city === c && !showCustom
                    ? 'bg-primary text-on-primary border-primary'
                    : 'bg-surface-container text-on-surface border-outline-variant/30 hover:border-primary/50'
                }`}
              >
                {c}
              </button>
            ))}
            <button
              onClick={handleOtherCity}
              className={`px-4 py-2.5 rounded-full text-sm font-medium transition-all border ${
                showCustom
                  ? 'bg-primary text-on-primary border-primary'
                  : 'bg-surface-container text-on-surface border-outline-variant/30 hover:border-primary/50'
              }`}
            >
              Otra ciudad
            </button>
          </div>

          {showCustom && (
            <input
              type="text"
              value={customCity}
              onChange={(e) => setCustomCity(e.target.value)}
              autoFocus
              placeholder="Escribe tu ciudad…"
              className="w-full bg-surface-container-lowest rounded-xl border border-outline-variant/30 focus:border-primary focus:outline-none px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 transition-colors mb-6"
            />
          )}

          <div className="mt-auto pt-6">
            <button
              onClick={goToStep2}
              disabled={!effectiveCity}
              className="w-full bg-primary text-on-primary font-bold py-4 rounded-full text-base hover:opacity-90 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Continuar
            </button>
          </div>
        </div>
      )}

      {/* Step 2 — Gustos */}
      {step === 2 && (
        <div className="flex-1 flex flex-col px-5 overflow-y-auto pb-8">
          <div className="mb-6">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-1 text-on-surface-variant mb-4 -ml-1"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_back_ios</span>
              <span className="text-sm">Volver</span>
            </button>
            <h1 className="text-3xl font-bold text-on-surface leading-tight mb-2">
              ¿Qué te gusta<br />
              <span className="text-primary">hacer?</span>
            </h1>
            <p className="text-sm text-on-surface-variant">
              Elige todo lo que te interese. Cuanto más elijas, mejores planes.
            </p>
          </div>

          <div className="space-y-6 mb-8">
            {CATEGORIES.map((cat) => (
              <div key={cat.name}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="material-symbols-outlined text-primary text-[18px]">{cat.icon}</span>
                  <span className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                    {cat.name}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {cat.subcategories.map((sub) => {
                    const active = selected.has(sub);
                    return (
                      <button
                        key={sub}
                        onClick={() => toggleSub(sub)}
                        className={`px-3.5 py-2 rounded-full text-sm font-medium transition-all border ${
                          active
                            ? 'bg-primary text-on-primary border-primary'
                            : 'bg-surface-container text-on-surface border-outline-variant/30 hover:border-primary/50'
                        }`}
                      >
                        {sub}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {error && (
            <div className="bg-error/10 border border-error/30 text-error text-sm px-4 py-3 rounded-xl mb-4">
              {error}
            </div>
          )}

          <div className="mt-auto">
            <button
              onClick={handleFinish}
              disabled={selected.size === 0 || saving}
              className="w-full bg-primary text-on-primary font-bold py-4 rounded-full text-base hover:opacity-90 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {saving
                ? 'Guardando…'
                : selected.size > 0
                  ? `Empezar (${selected.size} ${selected.size === 1 ? 'gusto' : 'gustos'})`
                  : 'Selecciona al menos uno'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
