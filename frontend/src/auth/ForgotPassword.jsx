import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import { api } from '../lib/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await api.post('/forgot-password', { email });
      setSuccess(true);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface text-slate-200 font-body flex flex-col items-center justify-center overflow-hidden relative">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,240,255,0.06)_0%,transparent_70%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.4)_100%)]" />
      </div>

      <div className="fixed top-6 left-6 z-20 hidden lg:block pointer-events-none">
        <div className="font-headline text-[10px] text-primary/40 leading-tight">
          System_Status: Standby<br />
          Node: AUTH_GATE_02<br />
          {new Date().toISOString().slice(11, 19)} UTC
        </div>
      </div>
      <div className="fixed top-6 right-6 z-20 hidden lg:block pointer-events-none">
        <div className="font-headline text-[10px] text-primary/40 text-right leading-tight uppercase">
          CLEARANCE: LEVEL_0<br />
          CONN: ENCRYPTED<br />
          PROTO: TLS_1.3
        </div>
      </div>

      <main className="relative z-10 w-full max-w-md px-6">
        <div className="glass-panel p-8 rounded-lg relative border-t-2 border-primary/50">
          <div className="absolute -top-px left-1/2 -translate-x-1/2 w-3/4 h-px bg-gradient-to-r from-transparent via-primary to-transparent shadow-[0_0_15px_#00f0ff]" />
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border border-primary/30 bg-primary/5 mb-4 relative">
              <Shield className="w-8 h-8 text-primary" />
              <div className="absolute inset-0 rounded-full border border-primary/20 animate-ping opacity-20" />
            </div>
            <h1 className="font-headline text-3xl font-black tracking-tighter text-white uppercase italic">
              SENTINEL<span className="text-primary italic">AI</span>
            </h1>
            <p className="font-label text-xs tracking-widest text-primary/60 uppercase mt-1">
              RESET PASSWORD
            </p>
          </div>

          {success ? (
            <div className="text-center w-full space-y-6">
              <div className="relative mx-auto w-16 h-16 flex items-center justify-center">
                <div className="absolute inset-0 bg-safe/20 blur-xl rounded-full" />
                <div className="relative bg-safe/10 rounded-full w-16 h-16 flex items-center justify-center ring-1 ring-safe/40">
                  <CheckCircle className="w-8 h-8 text-safe" />
                </div>
              </div>
              <p className="text-safe font-medium text-sm">Check your email</p>
              <p className="text-slate-500 text-[11px]">
                If that email is registered, we've sent a password reset link.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 text-[10px] font-bold tracking-widest text-slate-500 hover:text-primary transition-colors uppercase"
              >
                <ArrowLeft className="w-3 h-3" />
                Back to Command Center Login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="w-full space-y-6">
              {error && (
                <div className="rounded-lg border border-critical/30 bg-critical/10 px-4 py-3 text-xs text-critical flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-critical animate-pulse" />
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label className="block text-[10px] font-bold text-slate-500 tracking-[0.2em] ml-1 uppercase">OPERATOR_EMAIL</label>
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/40 group-focus-within:text-primary transition-colors" />
                  <input
                    type="email"
                    required
                    className="block w-full pl-10 pr-4 py-3 bg-slate-950/60 border border-slate-800 focus:border-primary focus:ring-1 focus:ring-primary/20 text-primary placeholder:text-slate-700 text-sm transition-all outline-none"
                    placeholder="OPERATOR@SENTINEL.AI"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-4 bg-primary text-slate-950 font-black tracking-widest text-xs uppercase transition-all active:scale-[0.98] hover:shadow-[0_0_20px_rgba(0,240,255,0.4)] flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
                ) : (
                  <>
                    <span>SEND RESET LINK</span>
                    <Shield className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}

          <div className="pt-2 w-full flex flex-col items-center">
            <Link
              to="/login"
              className="text-[10px] font-bold tracking-widest text-slate-500 hover:text-primary transition-colors uppercase border-b border-transparent hover:border-primary/50 pb-1"
            >
              Back to Command Center Login
            </Link>
          </div>
        </div>
      </main>

      <footer className="fixed bottom-8 left-0 w-full z-20 flex justify-center items-center pointer-events-none">
        <div className="flex items-center space-x-3 px-4 py-2 bg-surface/60 backdrop-blur-sm border border-slate-800/50">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-safe opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-safe" />
          </span>
          <span className="text-[9px] font-bold tracking-[0.3em] text-slate-400 uppercase">BEHAVIORAL PROFILING ACTIVE</span>
        </div>
      </footer>
    </div>
  );
}
