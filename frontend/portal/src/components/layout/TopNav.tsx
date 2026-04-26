import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLang } from '../../context/LanguageContext';

export default function TopNav() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();

  const navLinks = [
    { label: t.nav.discover, path: '/' },
    { label: t.nav.map, path: '/map' },
    { label: t.nav.planner, path: '/planner' },
  ];

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <header className="bg-surface sticky top-0 z-[1100]">
      <nav className="flex justify-between items-center w-full px-4 md:px-8 py-4 max-w-[1920px] mx-auto">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl md:text-2xl font-bold tracking-tighter text-tertiary font-headline">
            NextPlan
          </Link>
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`font-label text-sm transition-colors duration-300 hover:text-tertiary ${
                    isActive
                      ? 'text-tertiary border-b-2 border-tertiary pb-1'
                      : 'text-tertiary/70'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <button className="text-tertiary/70 hover:text-tertiary transition-colors" title="Notificaciones">
                <span className="material-symbols-outlined">notifications</span>
              </button>
              <Link
                to="/profile"
                className="text-tertiary/70 hover:text-tertiary transition-colors flex items-center gap-2"
                title={user.full_name ?? user.username}
              >
                <span className="hidden sm:block text-sm font-medium">
                  {user.full_name ?? user.username}
                </span>
                <span className="material-symbols-outlined">account_circle</span>
              </Link>
              <button
                onClick={handleLogout}
                className="text-tertiary/70 hover:text-error transition-colors"
                title="Cerrar sesión"
              >
                <span className="material-symbols-outlined">logout</span>
              </button>
            </>
          ) : (
            <Link to="/login" className="text-sm font-bold text-tertiary hover:underline">
              Iniciar sesión
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
