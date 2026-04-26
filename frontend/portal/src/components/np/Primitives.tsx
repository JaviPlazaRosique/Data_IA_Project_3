import type { CSSProperties, ReactNode } from 'react';
import { useLang } from '../../context/LanguageContext';

export function Icon({
  name,
  className = '',
  style = {},
  filled = false,
}: {
  name: string;
  className?: string;
  style?: CSSProperties;
  filled?: boolean;
}) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={{
        fontVariationSettings: filled
          ? '"FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24'
          : '"FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24',
        ...style,
      }}
    >
      {name}
    </span>
  );
}

export function SourceChip({ source }: { source: string }) {
  const map: Record<string, { color: string; icon: string }> = {
    Ticketmaster: { color: 'var(--np-primary)', icon: 'confirmation_number' },
    Eventbrite: { color: 'var(--np-amber)', icon: 'local_activity' },
    'Google Places': { color: 'var(--np-blue)', icon: 'location_on' },
    'Open-Meteo': { color: 'var(--np-amber)', icon: 'cloud' },
  };
  const s = map[source] ?? { color: 'var(--np-primary)', icon: 'open_in_new' };
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium tracking-wide"
      style={{
        background: `color-mix(in oklab, ${s.color} 14%, transparent)`,
        color: s.color,
        border: `1px solid color-mix(in oklab, ${s.color} 25%, transparent)`,
      }}
    >
      <Icon name={s.icon} className="text-[12px]" />
      {source}
    </span>
  );
}

export type WeatherCode = 'sunny' | 'partly' | 'cloudy' | 'rain' | 'storm' | 'clear_night';

export function WeatherBadge({
  code,
  temp,
  size = 'sm',
}: {
  code: WeatherCode;
  temp: number;
  size?: 'sm' | 'lg';
}) {
  const iconMap: Record<WeatherCode, string> = {
    sunny: 'wb_sunny',
    partly: 'partly_cloudy_night',
    cloudy: 'cloud',
    rain: 'cloudy_snowing',
    storm: 'thunderstorm',
    clear_night: 'wb_sunny',
  };
  const tone =
    code === 'rain' || code === 'storm'
      ? 'var(--np-blue)'
      : code === 'clear_night' || code === 'cloudy'
        ? 'var(--np-fg-dim)'
        : 'var(--np-amber)';
  const pad = size === 'lg' ? 'px-3 py-1.5 text-sm' : 'px-2 py-1 text-[11px]';
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${pad}`}
      style={{
        background: `color-mix(in oklab, ${tone} 12%, transparent)`,
        color: tone,
        border: `1px solid color-mix(in oklab, ${tone} 22%, transparent)`,
      }}
    >
      <Icon name={iconMap[code] ?? 'cloud'} className={size === 'lg' ? 'text-base' : 'text-sm'} />
      {temp}°
    </span>
  );
}

export function Pill({
  children,
  active,
  onClick,
  icon,
}: {
  children: ReactNode;
  active?: boolean;
  onClick?: () => void;
  icon?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-all ${
        active
          ? 'text-white shadow-[0_0_0_1px_var(--np-primary-dim)]'
          : 'text-[var(--np-fg-dim)] hover:text-[var(--np-fg)] border border-[var(--np-line)]'
      }`}
      style={active ? { background: 'var(--np-primary-dim)' } : {}}
    >
      {icon && <Icon name={icon} className="text-[16px]" />}
      {children}
    </button>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.2em] text-[var(--np-fg-dim)]">
      <span className="w-6 h-px bg-[var(--np-line)]" />
      {children}
    </div>
  );
}

export function ComingSoonBadge() {
  const { t } = useLang();
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium tracking-wide"
      style={{
        background: 'color-mix(in oklab, var(--np-primary) 10%, transparent)',
        color: 'var(--np-primary-dim)',
        border: '1px dashed color-mix(in oklab, var(--np-primary) 35%, transparent)',
      }}
    >
      <Icon name="schedule" className="text-[11px]" />
      {t.coming_soon}
    </span>
  );
}


