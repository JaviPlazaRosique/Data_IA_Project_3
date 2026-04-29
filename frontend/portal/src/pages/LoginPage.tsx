import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth, EmailNotVerifiedError } from '../context/AuthContext';
import TopNav from '../components/layout/TopNav';
import BottomNav from '../components/layout/BottomNav';

function mapAuthError(code: string | undefined): string {
  switch (code) {
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found':
      return 'Email o contraseña incorrectos';
    case 'auth/too-many-requests':
      return 'Demasiados intentos. Inténtalo más tarde.';
    case 'auth/popup-closed-by-user':
      return 'Inicio de sesión cancelado';
    default:
      return 'Algo ha ido mal';
  }
}

export default function LoginPage() {
  const { loginEmail, loginGoogle, loginMicrosoft, user } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingRedirect, setPendingRedirect] = useState(false);

  useEffect(() => {
    if (pendingRedirect && user) {
      setPendingRedirect(false);
      const onboarded =
        !!user.preferred_location ||
        (user.preferred_categories?.length ?? 0) > 0;
      navigate(onboarded ? '/map' : '/onboarding');
    }
  }, [pendingRedirect, user, navigate]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await loginEmail(email, password);
      setPendingRedirect(true);
    } catch (err) {
      if (err instanceof EmailNotVerifiedError) setError(err.message);
      else setError(mapAuthError((err as { code?: string })?.code));
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogle() {
    setError('');
    setLoading(true);
    try {
      await loginGoogle();
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
      <main className="flex-1 relative flex items-center justify-center px-4 py-4 pb-24 md:py-8 md:pb-8 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative w-full max-w-sm">
        <div className="text-center mb-6">
          <Link to="/" className="text-2xl font-extrabold tracking-tighter text-on-surface font-headline">
            NextPlan
          </Link>
          <p className="text-on-surface-variant text-sm mt-2">Inicia sesión en tu cuenta</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-surface-container-low rounded-[2rem] p-6 md:p-8 space-y-4 md:space-y-5 border border-outline-variant/10"
        >
          {error && (
            <div className="bg-error/10 border border-error/30 text-error text-sm px-4 py-3 rounded-xl">
              {error}
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
              autoComplete="current-password"
              className="w-full bg-surface-container-lowest rounded-xl border border-outline-variant/20 focus:border-secondary focus:outline-none px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 transition-colors"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-on-primary font-bold py-3 rounded-full hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {loading ? 'Iniciando sesión…' : 'Iniciar sesión'}
          </button>

          <div className="flex items-center gap-3 text-xs text-on-surface-variant/60">
            <div className="flex-1 h-px bg-outline-variant/20" />
            <span>o</span>
            <div className="flex-1 h-px bg-outline-variant/20" />
          </div>

          <button
            type="button"
            onClick={handleGoogle}
            disabled={loading}
            className="w-full bg-surface-container-lowest border border-outline-variant/20 text-on-surface font-bold py-3 rounded-full hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continuar con Google
          </button>

          <button
            type="button"
            onClick={handleMicrosoft}
            disabled={loading}
            className="w-full bg-surface-container-lowest border border-outline-variant/20 text-on-surface font-bold py-3 rounded-full hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continuar con Microsoft
          </button>

          <p className="text-center text-sm text-on-surface-variant">
            ¿No tienes cuenta?{' '}
            <Link to="/register" className="text-primary font-bold hover:underline">
              Regístrate
            </Link>
          </p>
        </form>
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
