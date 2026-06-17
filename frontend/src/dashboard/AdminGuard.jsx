import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { getAuthToken, isAdmin } from '../lib/api';
import { Shield } from 'lucide-react';

export default function AdminGuard({ children }) {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    if (!getAuthToken()) {
      setStatus('denied');
    } else if (isAdmin()) {
      setStatus('admin');
    } else {
      setStatus('denied');
    }
  }, []);

  if (status === 'checking') {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Shield className="w-8 h-8 text-primary animate-pulse-glow" />
          <div className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (status === 'denied') {
    return <Navigate to="/login?error=unauthorized" replace />;
  }

  return children;
}
