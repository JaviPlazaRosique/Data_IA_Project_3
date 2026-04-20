import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const navLinks = [
  { label: 'Home', path: '/' },
  { label: 'AI Chat', path: '/planner' },
  { label: 'Explore', path: '/map' },
  { label: 'Profile', path: '/profile' },
];

export default function TopNav() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <header className="bg-surface sticky top-0 z-50">
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
          <button className="text-tertiary/70 hover:text-tertiary transition-colors">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          {user ? (
            <div className="flex items-center gap-3">
              <Link to="/profile" className="hidden sm:block text-sm font-medium text-tertiary/70 hover:text-tertiary transition-colors">
                {user.full_name ?? user.username}
              </Link>
              <button
                onClick={handleLogout}
                className="text-tertiary/70 hover:text-error transition-colors"
                title="Sign out"
              >
                <span className="material-symbols-outlined">logout</span>
              </button>
            </div>
          ) : (
            <Link to="/login" className="text-sm font-bold text-tertiary hover:underline">
              Sign In
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
