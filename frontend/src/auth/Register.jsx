import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useBehavioral } from '../sdk/behavioral';
import { Shield, User, Mail, Lock, Eye, EyeOff, CheckCircle, Building2 } from 'lucide-react';
import { api } from '../lib/api';

function getPasswordStrength(pw) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

const STREGTH_LABELS = ['None', 'Weak', 'Fair', 'Moderate', 'Maximum'];
const STREGTH_COLORS = ['', 'bg-critical', 'bg-warning', 'bg-warning', 'bg-safe'];
const SECURITY_LEVELS = ['—', 'Level 0', 'Level 1', 'Level 2', 'Level 3'];

export default function Register() {
  const [form, setForm] = useState({ name: '', email: '', company: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();
  const getBehavioralPayload = useBehavioral();

  const strength = getPasswordStrength(form.password);
  const strengthColor = STREGTH_COLORS[strength];

  const updateField = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');

    if (form.password !== form.confirmPassword) {
      setError('Authentication mismatch: Passwords must align.');
      setIsLoading(false);
      return;
    }

    const behavioralData = getBehavioralPayload();

    try {
      const response = await api.post('/register', {
        email: form.email,
        password: form.password,
        name: form.name,
        behavioralData,
      });

      setSuccess(`Registration complete. Trust score: ${response.data.trust_score}.`);
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 1200);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const renderInput = (icon, field, placeholder, type = 'text') => {
    const Icon = icon;
    return (
      <div className="relative group">
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary" />
        <input
          type={type}
          required
          className="w-full bg-black/40 border-slate-800 rounded-lg py-3 pl-10 pr-4 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-primary transition-all"
          placeholder={placeholder}
          value={form[field]}
          onChange={updateField(field)}
        />
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-surface text-slate-300 font-body flex flex-col overflow-hidden relative selection:bg-primary/30">
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,240,255,0.08)_0%,transparent_70%)]" />
        <div className="absolute inset-0 scanline-overlay opacity-30" />
      </div>

      <div className="fixed top-6 left-6 z-20 hidden lg:block pointer-events-none">
        <div className="font-headline text-[10px] text-primary/40 leading-tight">
          SYS_INIT: OK<br />
          NET_STATUS: ENCRYPTED<br />
          LOC_NODE: 127.0.0.1
        </div>
      </div>
      <div className="fixed top-6 right-6 z-20 hidden lg:block pointer-events-none">
        <div className="font-headline text-[10px] text-primary/40 text-right leading-tight uppercase">
          CLEARANCE: LEVEL_0<br />
          TIMESTAMP: {new Date().toISOString().slice(0, 10).replace(/-/g, '.')}_{new Date().toTimeString().slice(0, 5)}<br />
          MODE: REGISTRATION_GATE
        </div>
      </div>

      <main className="relative z-10 flex-grow flex items-center justify-center p-6">
        <div className="w-full max-w-md glass-panel p-8 rounded-lg relative border-t-2 border-primary/50">
          <div className="absolute -top-px left-1/2 -translate-x-1/2 w-3/4 h-px bg-gradient-to-r from-transparent via-primary to-transparent shadow-[0_0_15px_#00f0ff]" />

          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border border-primary/30 bg-primary/5 mb-4 relative">
              <Shield className="w-8 h-8 text-primary" />
              <div className="absolute inset-0 rounded-full border border-primary/20 animate-ping opacity-20" />
            </div>
            <h1 className="font-headline text-3xl font-black tracking-tighter text-white uppercase italic">
              SENTINEL<span className="text-primary italic">AI</span>
            </h1>
            <p className="font-label text-xs tracking-widest text-primary/60 uppercase mt-1">Create Your Account</p>
          </div>

          {error && (
            <div className="mb-4 rounded-lg border border-critical/30 bg-critical/10 px-4 py-3 text-sm text-critical flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-critical animate-pulse" />
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 rounded-lg border border-safe/30 bg-safe/10 px-4 py-3 text-sm text-safe flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              {success}
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-5">
            <div className="space-y-1">
              {form.name ? (
                <div className="relative group">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-safe/60 group-focus-within:text-safe" />
                  <input
                    type="text"
                    required
                    className="w-full bg-black/40 border-safe/50 rounded-lg py-3 pl-10 pr-4 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-safe transition-all"
                    placeholder="Full Name"
                    value={form.name}
                    onChange={updateField('name')}
                  />
                  <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-safe" />
                </div>
              ) : (
                renderInput(User, 'name', 'Full Name')
              )}
            </div>

            <div className="space-y-1">
              {renderInput(Mail, 'email', 'Email Address', 'email')}
            </div>

            <div className="space-y-1">
              {renderInput(Building2, 'company', 'Organization / Entity')}
            </div>

            <div className="space-y-2">
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  className="w-full bg-black/40 border-slate-800 rounded-lg py-3 pl-10 pr-10 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-primary transition-all"
                  placeholder="Password"
                  value={form.password}
                  onChange={updateField('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>

              {form.password && (
                <>
                  <div className="flex gap-1.5 px-1">
                    {[0, 1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className={`flex-1 h-1 rounded-full transition-all duration-300 ${
                          i < strength ? `${strengthColor} ${strength >= 3 ? 'shadow-[0_0_8px_#00ff87]' : ''}` : 'bg-slate-800'
                        }`}
                      />
                    ))}
                  </div>
                  <p className="text-[10px] text-warning uppercase tracking-tighter px-1 flex justify-between">
                    <span>Entropy: {STREGTH_LABELS[strength]}</span>
                    <span>{SECURITY_LEVELS[strength]}</span>
                  </p>
                </>
              )}
            </div>

            <div className="space-y-1">
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary" />
                <input
                  type="password"
                  required
                  className={`w-full bg-black/40 rounded-lg py-3 pl-10 pr-4 text-sm text-white placeholder:text-slate-700 focus:outline-none transition-all ${
                    form.confirmPassword && form.password !== form.confirmPassword
                      ? 'border-critical/50 focus:border-critical'
                      : 'border-slate-800 focus:border-primary'
                  }`}
                  placeholder="Confirm Password"
                  value={form.confirmPassword}
                  onChange={updateField('confirmPassword')}
                />
              </div>
              {form.confirmPassword && form.password !== form.confirmPassword && (
                <p className="text-[10px] text-critical uppercase tracking-tight px-1">
                  Authentication mismatch: Passwords must align.
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary hover:bg-primary/90 text-black font-black uppercase tracking-widest text-xs py-4 rounded transition-all active:scale-95 shadow-[0_0_20px_rgba(0,240,255,0.4)] hover:shadow-[0_0_30px_rgba(0,240,255,0.6)] mt-4 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                ) : (
                  'REGISTER ACCOUNT'
                )}
            </button>
          </form>

          <div className="text-center mt-6">
            <Link
              to="/login"
              className="text-slate-500 hover:text-primary text-[10px] uppercase tracking-wider transition-colors"
            >
              Already have an account? <span className="text-primary font-bold">Log In</span>
            </Link>
          </div>
        </div>
      </main>

      <footer className="relative z-10 p-6 flex flex-col items-center space-y-3">
        <div className="flex items-center space-x-2 bg-black/60 border border-slate-800 px-4 py-1.5 rounded-full backdrop-blur-md">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-safe opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-safe" />
          </span>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">BEHAVIORAL PROFILING ACTIVE</span>
        </div>
        <div className="flex items-center space-x-4 text-[9px] uppercase tracking-widest text-slate-700">
          <a href="#" className="hover:text-primary transition-colors">Terms of Service</a>
          <span className="w-px h-3 bg-slate-800" />
          <a href="#" className="hover:text-primary transition-colors">Privacy Protocol</a>
          <span className="w-px h-3 bg-slate-800" />
          <a href="#" className="hover:text-primary transition-colors">System Status</a>
        </div>
      </footer>
    </div>
  );
}
