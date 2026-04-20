import { Link, useLocation } from 'react-router-dom';

interface SideNavProps {
  readonly activeItem?: string;
}

const navItems = [
  { icon: 'explore', label: 'Home', path: '/' },
  { icon: 'auto_awesome', label: 'AI Chat', path: '/planner' },
  { icon: 'map', label: 'Explore', path: '/map' },
  { icon: 'person', label: 'Profile', path: '/profile' },
];

export default function SideNav({ activeItem }: SideNavProps) {
  const location = useLocation();

  return (
    <aside className="hidden md:flex h-screen w-64 fixed left-0 top-0 bg-surface-container-low flex-col py-6 pl-4 z-50">
      <Link to="/" className="text-xl font-black text-on-surface mb-8 font-headline tracking-tighter">
        NextPlan
      </Link>
      <nav className="flex-1 space-y-2">
        {navItems.map((item) => {
          const isActive = activeItem
            ? activeItem === item.label
            : location.pathname === item.path;
          return (
            <Link
              key={item.label}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 transition-all rounded-r-full ${
                isActive
                  ? 'bg-surface-container-high text-tertiary font-bold'
                  : 'text-on-surface/60 hover:text-on-surface hover:bg-surface-container'
              }`}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto space-y-2 pr-4">
        <Link
          to="/"
          className="w-full py-3 mb-6 bg-primary text-on-primary font-bold rounded-full text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-sm">auto_awesome</span>
          Surprise Me
        </Link>
        <div className="flex flex-col gap-1">
          <a href="#" className="flex items-center gap-3 px-4 py-2 text-on-surface-variant hover:text-on-surface text-xs transition-colors">
            <span className="material-symbols-outlined text-lg">help</span>
            <span>Help</span>
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-2 text-on-surface-variant hover:text-on-surface text-xs transition-colors">
            <span className="material-symbols-outlined text-lg">logout</span>
            <span>Sign Out</span>
          </a>
        </div>
      </div>
    </aside>
  );
}
