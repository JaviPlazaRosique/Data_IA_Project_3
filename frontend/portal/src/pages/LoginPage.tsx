import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../api';
import TopNav from '../components/layout/TopNav';
import BottomNav from '../components/layout/BottomNav';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/profile');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Algo ha ido mal');
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
        {/* Logo */}
        <div className="text-center mb-6">
          <Link to="/" className="text-2xl font-extrabold tracking-tighter text-on-surface font-headline">
            NextPlan
          </Link>
          <p className="text-on-surface-variant text-sm mt-2">Inicia sesión en tu cuenta</p>
        </div>

        {/* Card */}
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
              placeholder="you@example.com"
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
