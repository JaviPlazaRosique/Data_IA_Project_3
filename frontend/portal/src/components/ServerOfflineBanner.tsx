import { useState } from 'react';

export default function ServerOfflineBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="fixed top-0 left-0 w-full z-[999] flex items-center justify-between gap-4 bg-error/10 border-b border-error/30 px-4 py-3 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <span className="material-symbols-outlined text-error">cloud_off</span>
        <p className="text-sm font-medium text-error">
          Not possible to connect to the server. Some features may be unavailable.
        </p>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="text-error hover:opacity-70 transition-opacity flex-shrink-0"
      >
        <span className="material-symbols-outlined text-base">close</span>
      </button>
    </div>
  );
}
