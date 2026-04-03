import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { icon: 'home', label: 'Home', path: '/' },
  { icon: 'auto_awesome', label: 'AI Chat', path: '/planner' },
  { icon: 'map', label: 'Explore', path: '/map' },
  { icon: 'person', label: 'Profile', path: '/profile' },
];

export default function BottomNav() {
  const location = useLocation();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-6 pt-3 bg-surface-container-low/60 backdrop-blur-xl rounded-t-3xl border-t border-outline-variant/20 shadow-[0_-10px_40px_rgba(0,0,0,0.4)]">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            className={`flex flex-col items-center justify-center gap-1 text-[10px] font-semibold uppercase tracking-widest transition-all active:scale-90 duration-200 ${
              isActive
                ? 'text-tertiary bg-tertiary/10 rounded-xl px-4 py-1'
                : 'text-on-surface/50 hover:text-primary'
            }`}
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
