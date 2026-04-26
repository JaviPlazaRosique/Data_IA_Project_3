import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../api';
import TopNav from '../components/layout/TopNav';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register({ email, username, password, full_name: fullName || undefined });
      localStorage.setItem('np_new_user', '1');
      navigate('/onboarding');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Algo ha ido mal');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <div className="hidden md:block"><TopNav /></div>
      <main className="flex-1 relative flex items-center justify-center px-4 py-8">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative w-full max-w-sm my-4">
        {/* Logo */}
        <div className="text-center mb-10">
          <Link to="/" className="text-2xl font-extrabold tracking-tighter text-on-surface font-headline">
            NextPlan
          </Link>
          <p className="text-on-surface-variant text-sm mt-2">Crea tu cuenta</p>
        </div>

        {/* Card */}
        <form
          onSubmit={handleSubmit}
          className="bg-surface-container-low rounded-[2rem] p-8 space-y-5 border border-outline-variant/10"
        >
          {error && (
            <div className="bg-error/10 border border-error/30 text-error text-sm px-4 py-3 rounded-xl">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block">
              Nombre completo <span className="text-on-surface-variant/40 normal-case font-normal">(opcional)</span>
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              className="w-full bg-surface-container-lowest rounded-xl border border-outline-variant/20 focus:border-secondary focus:outline-none px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 transition-colors"
              placeholder="Elena Vance"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block">
              Usuario
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              className="w-full bg-surface-container-lowest rounded-xl border border-outline-variant/20 focus:border-secondary focus:outline-none px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/40 transition-colors"
              placeholder="elena_vance"
            />
          </div>

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
              placeholder="you@example.com"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-on-surface-variant uppercase tracking-widest block">
              Contraseña <span className="text-on-surface-variant/40 normal-case font-normal">(mín. 8 caracteres)</span>
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
            disabled={loading || !privacyAccepted}
            className="w-full bg-primary text-on-primary font-bold py-3 rounded-full hover:opacity-90 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {loading ? 'Creando cuenta…' : 'Crear cuenta'}
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
    </div>
  );
}
