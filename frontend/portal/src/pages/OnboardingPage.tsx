import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiCheckUsername, apiUpdateMe } from '../api';
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

const USERNAME_REGEX = /^[a-zA-Z0-9][a-zA-Z0-9_-]{2,29}$/;

type UsernameStatus = 'idle' | 'checking' | 'available' | 'taken' | 'invalid';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [usernameStatus, setUsernameStatus] = useState<UsernameStatus>('idle');
  const usernameTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Step 2
  const [city, setCity] = useState('');
  const [customCity, setCustomCity] = useState('');
  const [showCustom, setShowCustom] = useState(false);

  // Step 3
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const effectiveCity = showCustom ? customCity.trim() : city;

  function handleUsernameChange(value: string) {
    setUsername(value);
    setUsernameStatus('idle');
    if (usernameTimerRef.current) clearTimeout(usernameTimerRef.current);
    const trimmed = value.trim().toLowerCase();
    if (!trimmed) return;
    if (!USERNAME_REGEX.test(trimmed)) {
      setUsernameStatus('invalid');
      return;
    }
    setUsernameStatus('checking');
    usernameTimerRef.current = setTimeout(async () => {
      try {
        const { available } = await apiCheckUsername(trimmed);
        setUsernameStatus(available ? 'available' : 'taken');
      } catch {
        setUsernameStatus('idle');
      }
    }, 500);
  }

  async function goToStep2() {
    const trimmed = username.trim().toLowerCase();
    if (!trimmed) return;
    if (!USERNAME_REGEX.test(trimmed)) {
      setUsernameStatus('invalid');
      return;
    }
    if (usernameStatus === 'checking') return;
    if (usernameStatus === 'taken') return;
    if (usernameStatus !== 'available') {
      setUsernameStatus('checking');
      try {
        const { available } = await apiCheckUsername(trimmed);
        if (!available) { setUsernameStatus('taken'); return; }
        setUsernameStatus('available');
      } catch {
        setUsernameStatus('idle');
        return;
      }
    }
    setStep(2);
  }

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

  function goToStep3() {
    if (!effectiveCity) return;
    setStep(3);
  }

  async function handleFinish() {
    if (selected.size === 0) return;
    setSaving(true);
    setError('');
    try {
      const updated = await apiUpdateMe({
        username: username.trim().toLowerCase(),
        full_name: fullName.trim() || null,
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

  const canContinueStep1 =
    username.trim().length >= 3 &&
    (usernameStatus === 'available');

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
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              s === step ? 'w-6 bg-primary' : s < step ? 'w-1.5 bg-primary/40' : 'w-1.5 bg-outline-variant/40'
            }`}
          />
        ))}
      </div>

      {/* Step 1 — Nombre de usuario y nombre completo */}
      {step === 1 && (
        <div className="flex-1 flex flex-col px-5 overflow-y-auto pb-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-on-surface leading-tight mb-2">
              ¿Cómo quieres<br />
              <span className="text-primary">que te llamemos?</span>
            </h1>
            <p className="text-sm text-on-surface-variant">
              Elige tu nombre de usuario único para NextPlan.
            </p>
          </div>

          {/* Username */}
          <div className="mb-6">
            <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-2">
              Nombre de usuario
            </label>
            <div className={`bg-surface-container-lowest flex items-center gap-2 rounded-xl border transition-colors px-4 py-3 ${
              usernameStatus === 'taken' || usernameStatus === 'invalid'
                ? 'border-error/60'
                : usernameStatus === 'available'
                  ? 'border-primary/60'
                  : 'border-outline-variant/30 focus-within:border-primary'
            }`}>
              <span className="text-on-surface-variant/60 text-sm select-none">@</span>
              <input
                type="text"
                value={username}
                onChange={(e) => handleUsernameChange(e.target.value)}
                autoFocus
                placeholder="tu_usuario"
                maxLength={30}
                className="flex-1 bg-transparent text-sm text-on-surface focus:outline-none placeholder:text-on-surface-variant/40"
              />
              {usernameStatus === 'checking' && (
                <span className="material-symbols-outlined text-base text-on-surface-variant animate-spin">progress_activity</span>
              )}
              {usernameStatus === 'available' && (
                <span className="material-symbols-outlined text-base text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
              )}
              {(usernameStatus === 'taken' || usernameStatus === 'invalid') && (
                <span className="material-symbols-outlined text-base text-error" style={{ fontVariationSettings: "'FILL' 1" }}>cancel</span>
              )}
            </div>
            {usernameStatus === 'taken' && (
              <p className="text-xs text-error mt-1.5 px-1">Este nombre de usuario ya está en uso.</p>
            )}
            {usernameStatus === 'invalid' && (
              <p className="text-xs text-error mt-1.5 px-1">
                3–30 caracteres. Solo letras, números, _ y -.
              </p>
            )}
            {usernameStatus === 'available' && (
              <p className="text-xs text-primary mt-1.5 px-1">¡Disponible!</p>
            )}
            {usernameStatus === 'idle' && username.length === 0 && (
              <p className="text-xs text-on-surface-variant/50 mt-1.5 px-1">
                Mínimo 3 caracteres. Solo letras, números, _ y -.
              </p>
            )}
          </div>

          {/* Full Name */}
          <div className="mb-6">
            <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block mb-2">
              Nombre completo{' '}
              <span className="normal-case font-normal text-on-surface-variant/50">(opcional)</span>
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Ej. María García"
              maxLength={100}
              className="w-full bg-surface-container-lowest rounded-xl border border-outline-variant/30 focus:border-primary focus:outline-none px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 transition-colors"
            />
          </div>

          <div className="mt-auto pt-6">
            <button
              onClick={goToStep2}
              disabled={!canContinueStep1}
              className="w-full bg-primary text-on-primary font-bold py-4 rounded-full text-base hover:opacity-90 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {usernameStatus === 'checking' ? 'Comprobando…' : 'Continuar'}
            </button>
          </div>
        </div>
      )}

      {/* Step 2 — Ciudad */}
      {step === 2 && (
        <div className="flex-1 flex flex-col px-5 overflow-y-auto pb-8">
          <div className="mb-8">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-1 text-on-surface-variant mb-4 -ml-1"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_back_ios</span>
              <span className="text-sm">Volver</span>
            </button>
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
              onClick={goToStep3}
              disabled={!effectiveCity}
              className="w-full bg-primary text-on-primary font-bold py-4 rounded-full text-base hover:opacity-90 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Continuar
            </button>
          </div>
        </div>
      )}

      {/* Step 3 — Gustos */}
      {step === 3 && (
        <div className="flex-1 flex flex-col px-5 overflow-y-auto pb-8">
          <div className="mb-6">
            <button
              onClick={() => setStep(2)}
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
