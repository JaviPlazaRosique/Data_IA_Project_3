import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import TopNav from '../components/layout/TopNav';
import BottomNav from '../components/layout/BottomNav';

const PW_RULES = {
  length: (v: string) => v.length >= 8,
  upper: (v: string) => /[A-Z]/.test(v),
  lower: (v: string) => /[a-z]/.test(v),
  digit: (v: string) => /\d/.test(v),
  symbol: (v: string) => /[^A-Za-z0-9]/.test(v),
};

function mapAuthError(code: string | undefined): string {
  switch (code) {
    case 'auth/email-already-in-use':
      return 'Este email ya está registrado';
    case 'auth/invalid-email':
      return 'Email no válido';
    case 'auth/weak-password':
      return 'Contraseña demasiado débil';
    default:
      return 'Algo ha ido mal';
  }
}

export default function RegisterPage() {
  const { registerEmail, loginGoogle, loginMicrosoft, user } = useAuth();
  const navigate = useNavigate();
  const [pendingRedirect, setPendingRedirect] = useState(false);

  useEffect(() => {
    if (pendingRedirect && user) {
      setPendingRedirect(false);
      navigate('/onboarding');
    }
  }, [pendingRedirect, user, navigate]);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);

  const checks = useMemo(() => ({
    length: PW_RULES.length(password),
    upper: PW_RULES.upper(password),
    lower: PW_RULES.lower(password),
    digit: PW_RULES.digit(password),
    symbol: PW_RULES.symbol(password),
  }), [password]);

  const pwValid = Object.values(checks).every(Boolean);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setInfo('');
    if (!pwValid) {
      setError('La contraseña no cumple los requisitos');
      return;
    }
    setLoading(true);
    try {
      await registerEmail(email, password);
      localStorage.setItem('np_new_user', '1');
      setInfo('Cuenta creada. Revisa tu email para verificar antes de iniciar sesión.');
    } catch (err) {
      setError(mapAuthError((err as { code?: string })?.code));
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogle() {
    setError('');
    setLoading(true);
    try {
      await loginGoogle();
      localStorage.setItem('np_new_user', '1');
      setPendingRedirect(true);
    } catch (err) {
      setError(mapAuthError((err as { code?: string })?.code));
    } finally {
      setLoading(false);
    }
  }

  async function handleMicrosoft() {
    setError('');
    setLoading(true);
    try {
      await loginMicrosoft();
      localStorage.setItem('np_new_user', '1');
      setPendingRedirect(true);
    } catch (err) {
      setError(mapAuthError((err as { code?: string })?.code));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen bg-surface flex flex-col overflow-hidden">
      <div className="hidden md:block"><TopNav /></div>
      <main className="flex-1 relative flex items-center justify-center px-4 py-3 pb-24 md:py-8 md:pb-8 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative w-full max-w-sm">
        <div className="text-center mb-4">
          <Link to="/" className="text-2xl font-extrabold tracking-tighter text-on-surface font-headline">
            NextPlan
          </Link>
          <p className="text-on-surface-variant text-sm mt-2">Crea tu cuenta</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-surface-container-low rounded-[2rem] p-5 md:p-8 space-y-3 md:space-y-5 border border-outline-variant/10"
        >
          {error && (
            <div className="bg-error/10 border border-error/30 text-error text-sm px-4 py-3 rounded-xl">
              {error}
            </div>
          )}
          {info && (
            <div className="bg-primary/10 border border-primary/30 text-on-surface text-sm px-4 py-3 rounded-xl">
              {info}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block">
              Correo electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full bg-surface-container-lowest rounded-xl border border-outline-variant/20 focus:border-secondary focus:outline-none px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 transition-colors"
              placeholder="tu@ejemplo.com"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              className="w-full bg-surface-container-lowest rounded-xl border border-outline-variant/20 focus:border-secondary focus:outline-none px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 transition-colors"
              placeholder="••••••••"
            />
            <ul className="text-xs space-y-0.5 mt-2">
              <li className={checks.length ? 'text-primary' : 'text-on-surface-variant/60'}>• Mínimo 8 caracteres</li>
              <li className={checks.upper ? 'text-primary' : 'text-on-surface-variant/60'}>• Una mayúscula</li>
              <li className={checks.lower ? 'text-primary' : 'text-on-surface-variant/60'}>• Una minúscula</li>
              <li className={checks.digit ? 'text-primary' : 'text-on-surface-variant/60'}>• Un número</li>
              <li className={checks.symbol ? 'text-primary' : 'text-on-surface-variant/60'}>• Un símbolo</li>
            </ul>
          </div>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={privacyAccepted}
              onChange={(e) => setPrivacyAccepted(e.target.checked)}
              required
              className="mt-0.5 accent-primary w-4 h-4 shrink-0"
            />
            <span className="text-xs text-on-surface-variant leading-relaxed">
              He leído y acepto el{' '}
              <Link to="/privacy" className="text-primary font-bold hover:underline" target="_blank">
                Aviso de privacidad
              </Link>
            </span>
          </label>

          <button
            type="submit"
            disabled={loading || !privacyAccepted || !pwValid}
            className="w-full bg-primary text-on-primary font-bold py-3 rounded-full hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {loading ? 'Creando cuenta…' : 'Crear cuenta'}
          </button>

          <div className="flex items-center gap-3 text-xs text-on-surface-variant/60">
            <div className="flex-1 h-px bg-outline-variant/20" />
            <span>o</span>
            <div className="flex-1 h-px bg-outline-variant/20" />
          </div>

          <button
            type="button"
            onClick={handleGoogle}
            disabled={loading || !privacyAccepted}
            className="w-full bg-surface-container-lowest border border-outline-variant/20 text-on-surface font-bold py-3 rounded-full hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continuar con Google
          </button>

          <button
            type="button"
            onClick={handleMicrosoft}
            disabled={loading || !privacyAccepted}
            className="w-full bg-surface-container-lowest border border-outline-variant/20 text-on-surface font-bold py-3 rounded-full hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continuar con Microsoft
          </button>

          <p className="text-center text-sm text-on-surface-variant">
            ¿Ya tienes cuenta?{' '}
            <Link to="/login" className="text-primary font-bold hover:underline">
              Inicia sesión
            </Link>
          </p>
        </form>
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
