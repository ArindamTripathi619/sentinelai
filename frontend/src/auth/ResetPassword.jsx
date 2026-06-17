import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Shield, Lock, ArrowLeft, CheckCircle, Eye, EyeOff, KeyRound } from 'lucide-react';
import { api } from '../lib/api';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!token) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center p-4">
        <div className="glass-panel p-8 max-w-md w-full text-center">
          <p className="text-critical text-sm mb-4">Invalid reset link. No token provided.</p>
          <Link to="/forgot-password" className="text-[10px] font-bold tracking-widest text-slate-500 hover:text-primary transition-colors uppercase border-b border-transparent hover:border-primary/50 pb-1 inline-flex items-center gap-2">
            <ArrowLeft className="w-3 h-3" />
            Request a new reset link
          </Link>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Authentication mismatch: Passwords must align.');
      setIsLoading(false);
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.');
      setIsLoading(false);
      return;
    }

    try {
      await api.post('/reset-password', { token, new_password: newPassword });
      setSuccess(true);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Reset failed. The link may be invalid or expired.');
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
        <div className="font-headline text-[9px] text-primary/30 leading-tight">
          SEC_LEVEL: 04<br />
          ENCR: AES_256<br />
          STAT: TOKEN_ACCEPTED
        </div>
      </div>

      <main className="relative z-10 w-full max-w-md px-6">
        <div className="glass-panel p-8 md:p-10 flex flex-col items-center space-y-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
              <div className="relative w-16 h-16 border border-primary/30 rounded-full flex items-center justify-center bg-surface/80">
                <KeyRound className="w-8 h-8 text-primary" />
              </div>
            </div>
            <div className="space-y-1">
              <h1 className="font-headline font-black text-3xl tracking-tighter text-primary">SENTINEL AI</h1>
              <h2 className="font-headline text-sm tracking-widest text-slate-400 uppercase">SET NEW PASSWORD</h2>
            </div>
          </div>

          {success ? (
            <div className="text-center w-full space-y-6">
              <div className="relative mx-auto w-16 h-16 flex items-center justify-center">
                <div className="absolute inset-0 bg-safe/20 blur-xl rounded-full" />
                <div className="relative bg-safe/10 rounded-full w-16 h-16 flex items-center justify-center ring-1 ring-safe/40">
                  <CheckCircle className="w-8 h-8 text-safe" />
                </div>
              </div>
              <p className="text-safe font-medium text-sm">Password reset successful</p>
              <p className="text-slate-500 text-[11px]">
                You can now log in with your new password.
              </p>
              <button
                onClick={() => navigate('/login', { replace: true })}
                className="w-full py-4 bg-primary text-slate-950 font-black tracking-widest text-xs uppercase transition-all active:scale-[0.98] hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]"
              >
                Go to Login
              </button>
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
                <label className="block text-[10px] font-bold text-slate-500 tracking-[0.2em] ml-1 uppercase">NEW PASSPHRASE</label>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/40 group-focus-within:text-primary transition-colors" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    className="block w-full pl-10 pr-10 py-3 bg-slate-950/60 border border-slate-800 focus:border-primary focus:ring-1 focus:ring-primary/20 text-primary placeholder:text-slate-700 text-sm transition-all outline-none"
                    placeholder="••••••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-[10px] font-bold text-slate-500 tracking-[0.2em] ml-1 uppercase">CONFIRM PASSPHRASE</label>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/40 group-focus-within:text-primary transition-colors" />
                  <input
                    type="password"
                    required
                    minLength={8}
                    className={`block w-full pl-10 pr-4 py-3 bg-slate-950/60 border focus:ring-1 text-sm transition-all outline-none ${
                      confirmPassword && newPassword !== confirmPassword
                        ? 'border-critical/50 focus:border-critical focus:ring-critical/20 text-critical'
                        : 'border-slate-800 focus:border-primary focus:ring-primary/20 text-primary'
                    }`}
                    placeholder="••••••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-[10px] text-critical uppercase tracking-tight px-1">
                    Authentication mismatch: Passwords must align.
                  </p>
                )}
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
                    <span>Reset Password</span>
                    <Shield className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}

          <div className="pt-2 w-full flex flex-col items-center">
            <Link
              to="/login"
              className="text-[10px] font-bold tracking-widest text-slate-500 hover:text-primary transition-colors uppercase border-b border-transparent hover:border-primary/50 pb-1 inline-flex items-center gap-2"
            >
              <ArrowLeft className="w-3 h-3" />
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
