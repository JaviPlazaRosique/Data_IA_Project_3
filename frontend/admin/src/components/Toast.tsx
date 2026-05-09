import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

export type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

let _nextId = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const t = timers.current.get(id);
    if (t) { clearTimeout(t); timers.current.delete(id); }
  }, []);

  const toast = useCallback((message: string, type: ToastType = 'info') => {
    const id = String(++_nextId);
    setToasts((prev) => [...prev.slice(-4), { id, message, type }]);
    timers.current.set(id, setTimeout(() => dismiss(id), 4000));
  }, [dismiss]);

  useEffect(() => {
    const t = timers.current;
    return () => { t.forEach(clearTimeout); };
  }, []);

  const colors: Record<ToastType, string> = {
    success: 'bg-emerald-900 border-emerald-700 text-emerald-200',
    error: 'bg-red-900 border-red-700 text-red-200',
    info: 'bg-gray-800 border-gray-600 text-gray-200',
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-5 right-5 flex flex-col gap-2 z-50 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            onClick={() => dismiss(t.id)}
            className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg border text-sm shadow-lg cursor-pointer max-w-sm ${colors[t.type]}`}
          >
            <span className="flex-1">{t.message}</span>
            <span className="text-xs opacity-60">✕</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
