import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { STRINGS, type I18n } from '../i18n';

interface LanguageContextValue {
  t: I18n;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const value = useMemo<LanguageContextValue>(() => ({ t: STRINGS['es'] }), []);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLang must be used within LanguageProvider');
  return ctx;
}
