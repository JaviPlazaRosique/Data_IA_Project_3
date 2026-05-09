import { type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function AdminRoute({ children }: { children: ReactNode }) {
  const { fbUser, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <span className="text-gray-400 text-sm">Loading…</span>
      </div>
    );
  }

  if (!fbUser) return <Navigate to="/login" replace />;
  if (!user || !user.is_admin) return <Navigate to="/not-admin" replace />;

  return <>{children}</>;
}
