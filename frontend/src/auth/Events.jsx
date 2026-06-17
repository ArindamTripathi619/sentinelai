import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthToken, clearUserSession, isAdmin } from '../lib/api';
import { LogOut, Activity, ArrowLeft } from 'lucide-react';

export default function EventsPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (!getAuthToken()) {
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  function handleLogout() {
    clearUserSession();
    navigate('/login', { replace: true });
  }

  const admin = isAdmin();

  return (
    <div className="min-h-screen bg-surface font-body text-slate-300 flex flex-col items-center justify-center relative overflow-hidden">
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,240,255,0.08)_0%,transparent_70%)]" />
        <div className="absolute inset-0 scanline-overlay opacity-20" />
      </div>

      <div className="glass-panel p-10 max-w-md w-full text-center rounded-lg relative z-10">
        <div className="bg-warning/10 p-3 rounded-full mx-auto mb-4 w-16 h-16 flex items-center justify-center ring-1 ring-warning/30">
          <Activity className="w-8 h-8 text-warning" />
        </div>
        <h2 className="text-xl font-headline font-bold text-white mb-2">Event Platform</h2>
        <p className="text-sm text-slate-500 font-body mb-4">Event listing — under construction</p>
        <p className="text-[10px] text-slate-600 mb-8">Event management features coming soon.</p>
        <div className="flex flex-col gap-3">
          {admin && (
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-xs font-medium rounded-lg border border-primary/30 text-primary hover:bg-primary/10 bg-primary/5 transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </button>
          )}
          <button
            onClick={handleLogout}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-xs font-medium rounded-lg border border-slate-800/50 text-slate-400 hover:text-critical hover:border-critical/30 bg-slate-900/60 hover:bg-critical/10 transition-all"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
