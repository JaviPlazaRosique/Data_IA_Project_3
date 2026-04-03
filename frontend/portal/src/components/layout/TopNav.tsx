import { Link, useLocation } from 'react-router-dom';

const navLinks = [
  { label: 'Discover', path: '/' },
  { label: 'Map', path: '/map' },
  { label: 'Planner', path: '/planner' },
  { label: 'Dashboard', path: '/profile' },
];

export default function TopNav() {
  const location = useLocation();

  return (
    <header className="bg-surface sticky top-0 z-50">
      <nav className="flex justify-between items-center w-full px-8 py-4 max-w-[1920px] mx-auto">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-2xl font-bold tracking-tighter text-on-surface font-headline">
            The Electric Curator
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
                      ? 'text-primary border-b-2 border-primary pb-1'
                      : 'text-on-surface/70'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-6">
          <button className="text-on-surface/70 hover:text-tertiary transition-colors">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <Link to="/profile" className="text-on-surface/70 hover:text-tertiary transition-colors">
            <span className="material-symbols-outlined">account_circle</span>
          </Link>
        </div>
      </nav>
    </header>
  );
}
