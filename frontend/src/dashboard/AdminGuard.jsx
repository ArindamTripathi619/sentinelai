import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthToken, isAdmin, clearUserSession } from '../lib/api';
import { Shield } from 'lucide-react';

export default function AdminGuard({ children }) {
  const [status, setStatus] = useState('checking');
  const navigate = useNavigate();

  const checkAuth = () => {
    const token = getAuthToken();
    if (!token) {
      setStatus('denied');
      return;
    }
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.exp * 1000 < Date.now()) {
        clearUserSession();
        setStatus('denied');
        return;
      }
    } catch {
      setStatus('denied');
      return;
    }
    setStatus(isAdmin() ? 'admin' : 'denied');
  };

  useEffect(() => {
    checkAuth();
    const onStorage = () => checkAuth();
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  useEffect(() => {
    if (status === 'denied' && !getAuthToken()) {
      navigate('/login?error=unauthorized', { replace: true });
    } else if (status === 'denied') {
      navigate('/events', { replace: true });
    }
  }, [status, navigate]);

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
    return null;
  }

  return children;
}
