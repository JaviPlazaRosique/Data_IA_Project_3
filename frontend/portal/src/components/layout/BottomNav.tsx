import { Link, useLocation } from 'react-router-dom';
import { useLang } from '../../context/LanguageContext';

export default function BottomNav() {
  const location = useLocation();
  const { t } = useLang();

  const navItems = [
    { icon: 'style', label: t.nav.discover, path: '/' },
    { icon: 'map', label: t.nav.map, path: '/map' },
    { icon: 'auto_awesome', label: t.nav.planner, path: '/planner' },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-2 pt-3 bg-surface border-t border-outline-variant/20" style={{ paddingBottom: 'max(1.25rem, env(safe-area-inset-bottom))' }}>
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            className={`flex flex-col items-center justify-center gap-1 text-[10px] font-semibold uppercase tracking-widest transition-colors duration-200 min-w-[56px] py-1 ${
              isActive
                ? 'text-tertiary'
                : 'text-tertiary/70 hover:text-tertiary'
            }`}
          >
            <span className="material-symbols-outlined text-[22px]">{item.icon}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
