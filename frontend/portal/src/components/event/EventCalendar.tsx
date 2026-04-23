import { useMemo, useState } from 'react';

export type CalendarSlot = { time: string; url: string | null };
export type CalendarEntry = { date: string; slots: CalendarSlot[] };

type Props = {
  entries: CalendarEntry[];
};

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function parseISO(date: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return isNaN(d.getTime()) ? null : d;
}

function toISO(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function EventCalendar({ entries }: Props) {
  const entryMap = useMemo(() => {
    const m = new Map<string, CalendarEntry>();
    for (const e of entries) m.set(e.date, e);
    return m;
  }, [entries]);

  const firstEventDate = useMemo(() => {
    for (const e of entries) {
      const d = parseISO(e.date);
      if (d) return d;
    }
    return new Date();
  }, [entries]);

  const [viewMonth, setViewMonth] = useState<Date>(
    () => new Date(firstEventDate.getFullYear(), firstEventDate.getMonth(), 1)
  );
  const [selectedDate, setSelectedDate] = useState<string | null>(() => {
    for (const e of entries) if (parseISO(e.date)) return e.date;
    return null;
  });

  const grid = useMemo(() => {
    const year = viewMonth.getFullYear();
    const month = viewMonth.getMonth();
    const first = new Date(year, month, 1);
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const startOffset = (first.getDay() + 6) % 7;
    const cells: (Date | null)[] = [];
    for (let i = 0; i < startOffset; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(year, month, d));
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [viewMonth]);

  const goPrev = () => setViewMonth((v) => new Date(v.getFullYear(), v.getMonth() - 1, 1));
  const goNext = () => setViewMonth((v) => new Date(v.getFullYear(), v.getMonth() + 1, 1));

  const selectedEntry = selectedDate ? entryMap.get(selectedDate) ?? null : null;
  const todayISO = toISO(new Date());

  return (
    <div className="bg-surface-container-low rounded-2xl p-4 md:p-6 border border-outline-variant/20">
      <div className="flex items-center justify-between mb-4">
        <button
          type="button"
          onClick={goPrev}
          aria-label="Previous month"
          className="w-9 h-9 rounded-full flex items-center justify-center hover:bg-surface-container-high transition-colors"
        >
          <span className="material-symbols-outlined rotate-180">chevron_right</span>
        </button>
        <div className="font-bold font-headline text-lg">
          {MONTH_NAMES[viewMonth.getMonth()]} {viewMonth.getFullYear()}
        </div>
        <button
          type="button"
          onClick={goNext}
          aria-label="Next month"
          className="w-9 h-9 rounded-full flex items-center justify-center hover:bg-surface-container-high transition-colors"
        >
          <span className="material-symbols-outlined">chevron_right</span>
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-bold uppercase tracking-wider text-on-surface-variant mb-2">
        {WEEKDAYS.map((w) => <div key={w}>{w}</div>)}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {grid.map((cell, idx) => {
          if (!cell) return <div key={`empty-${idx}`} className="aspect-square" />;
          const iso = toISO(cell);
          const hasEvent = entryMap.has(iso);
          const isSelected = iso === selectedDate;
          const isToday = iso === todayISO;
          return (
            <button
              key={iso}
              type="button"
              onClick={() => hasEvent && setSelectedDate(iso)}
              disabled={!hasEvent}
              aria-pressed={isSelected}
              className={[
                'aspect-square rounded-lg flex flex-col items-center justify-center text-sm font-medium transition-colors relative',
                hasEvent
                  ? 'cursor-pointer hover:bg-primary/20'
                  : 'text-on-surface-variant/40 cursor-default',
                isSelected
                  ? 'bg-primary text-on-primary hover:bg-primary'
                  : hasEvent
                    ? 'bg-surface-container-high text-on-surface'
                    : '',
                isToday && !isSelected ? 'ring-1 ring-primary/40' : '',
              ].join(' ')}
            >
              <span>{cell.getDate()}</span>
              {hasEvent && !isSelected && (
                <span className="w-1 h-1 rounded-full bg-primary absolute bottom-1" />
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-5 pt-5 border-t border-outline-variant/20">
        {selectedEntry && selectedEntry.slots.length > 0 ? (
          <>
            <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-3">
              Times on {selectedEntry.date}
            </p>
            <div className="flex flex-wrap gap-2">
              {selectedEntry.slots.map((slot) =>
                slot.url ? (
                  <a
                    key={slot.time}
                    href={slot.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-primary/10 hover:bg-primary/20 text-primary font-semibold text-sm transition-colors"
                  >
                    <span className="material-symbols-outlined text-base">schedule</span>
                    {slot.time}
                  </a>
                ) : (
                  <span
                    key={slot.time}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface font-semibold text-sm"
                  >
                    <span className="material-symbols-outlined text-base">schedule</span>
                    {slot.time}
                  </span>
                )
              )}
            </div>
          </>
        ) : selectedEntry ? (
          <p className="text-sm text-on-surface-variant">No time info.</p>
        ) : (
          <p className="text-sm text-on-surface-variant">Select a highlighted day to see times.</p>
        )}
      </div>
    </div>
  );
}
