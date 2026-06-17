import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useBehavioral } from '../sdk/behavioral';
import { Shield, Lock, Mail, ArrowRight, KeyRound, Shuffle, UserPlus } from 'lucide-react';
import { api, setUserSession, isAdmin } from '../lib/api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpSessionId, setOtpSessionId] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [captchaToken, setCaptchaToken] = useState('');
  const [captchaPrompt, setCaptchaPrompt] = useState('');
  const [captchaAnswer, setCaptchaAnswer] = useState('');
  const [requiresOtp, setRequiresOtp] = useState(false);
  const [requiresCaptcha, setRequiresCaptcha] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [currentTime, setCurrentTime] = useState('20:44:12');
  const navigate = useNavigate();
  const getBehavioralPayload = useBehavioral();

  useEffect(() => {
    const t = setInterval(() => {
      setCurrentTime(new Date().toISOString().slice(11, 19) + ' UTC');
    }, 1000);
    return () => clearInterval(t);
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setInfo('');

    const behavioralData = getBehavioralPayload();

    try {
      const response = await api.post('/login', {
        email,
        password,
        behavioralData,
        user_agent: navigator.userAgent,
      });

      if (response.data.otp_required) {
        setRequiresOtp(true);
        setOtpSessionId(response.data.otp_session_id);
        setInfo('OTP required — code sent to your session.');

        if (response.data.otp_session_id) {
          await api.post('/otp/send', {
            otp_session_id: response.data.otp_session_id,
            email,
          });
        }
      } else if (response.data.captcha_required) {
        setRequiresCaptcha(true);
        setCaptchaToken(response.data.captcha_token);
        setCaptchaPrompt(response.data.captcha_prompt);
        setInfo('Security check required — enter the challenge code.');
      } else if (response.data.is_blocked) {
        setError(response.data.message || 'Account access restricted.');
      } else if (response.data.token) {
        setUserSession({ token: response.data.token, userId: response.data.user_id });
        const isAdminUser = isAdmin();
        navigate(isAdminUser ? '/dashboard' : '/events', { replace: true });
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpVerify = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await api.post('/otp/verify', {
        otp_session_id: otpSessionId,
        otp_code: otpCode,
      });

      setUserSession({ token: response.data.token, userId: response.data.user_id });
      navigate(isAdmin() ? '/dashboard' : '/events', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || 'OTP verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCaptchaVerify = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await api.post('/captcha/verify', {
        captcha_token: captchaToken,
        captcha_answer: captchaAnswer,
      });

      setUserSession({ token: response.data.token, userId: response.data.user_id });
      navigate(isAdmin() ? '/dashboard' : '/events', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || 'CAPTCHA verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface text-slate-300 font-body flex flex-col overflow-hidden relative selection:bg-primary/30">
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,240,255,0.08)_0%,transparent_70%)]" />
        <div className="absolute inset-4 border border-primary/5 rounded-[4rem] opacity-40" />
        <div className="absolute inset-0 scanline-overlay opacity-20" />
      </div>

      <div className="fixed top-6 left-6 z-20 hidden lg:block pointer-events-none">
        <div className="font-headline text-[10px] text-primary/40 leading-tight">
          System_Status: Operational<br />
          Node: HQ_WEST_04<br />
          {currentTime}
        </div>
      </div>
      <div className="fixed top-6 right-6 z-20 hidden lg:block pointer-events-none">
        <div className="font-headline text-[10px] text-primary/40 text-right leading-tight uppercase">
          CLEARANCE: LEVEL_0<br />
          CONN: ENCRYPTED<br />
          PROTO: TLS_1.3
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
            <p className="font-label text-xs tracking-widest text-primary/60 uppercase mt-1">
              CYBER COMMAND LOGIN
            </p>
            <p className="text-[10px] text-slate-500 mt-3">
              Biometric handshake required for level 5 access.
            </p>
          </div>

          {error && (
            <div className="mb-4 rounded-lg border border-critical/30 bg-critical/10 px-4 py-3 text-sm text-critical flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-critical animate-pulse" />
              {error}
            </div>
          )}

          {info && (
            <div className="mb-4 rounded-lg border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-primary flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              {info}
            </div>
          )}

          {!requiresOtp && !requiresCaptcha ? (
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 tracking-[0.2em] ml-1 uppercase">Access_Identifier</label>
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary" />
                  <input
                    type="email"
                    required
                    className="w-full bg-black/40 border-slate-800 rounded-lg py-3 pl-10 pr-4 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-primary transition-all"
                    placeholder="OPERATOR@SENTINEL.AI"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between ml-1">
                  <label className="text-[10px] font-bold text-slate-500 tracking-[0.2em] uppercase">Passphrase_Key</label>
                  <Link to="/forgot-password" className="text-[9px] text-primary/60 hover:text-primary uppercase tracking-wider transition-colors">
                    Recover?
                  </Link>
                </div>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-primary" />
                  <input
                    type="password"
                    required
                    className="w-full bg-black/40 border-slate-800 rounded-lg py-3 pl-10 pr-4 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-primary transition-all"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-primary hover:bg-primary/90 text-black font-black uppercase tracking-widest text-xs py-4 rounded transition-all active:scale-95 shadow-[0_0_20px_rgba(0,240,255,0.4)] hover:shadow-[0_0_30px_rgba(0,240,255,0.6)] flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Authenticate</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>

              <div className="pt-2 border-t border-slate-800/50 text-center">
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 text-[10px] text-slate-500 hover:text-primary uppercase tracking-wider transition-colors"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  Request Clearance / Register Account
                </Link>
              </div>
            </form>
          ) : requiresOtp ? (
            <form onSubmit={handleOtpVerify} className="space-y-5">
              <div className="text-center mb-2">
                <KeyRound className="w-10 h-10 text-primary mx-auto mb-2" />
                <p className="text-lg font-headline font-bold text-white">MFA_AUTHENTICATION</p>
                <p className="text-[10px] text-slate-500 mt-1">Enter the 6-digit code sent to your session</p>
              </div>
              <div className="space-y-1">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  required
                  className="w-full bg-black/40 border-slate-800 rounded-lg py-3 text-center text-lg font-mono tracking-[0.4em] text-white placeholder:text-slate-700 focus:outline-none focus:border-primary transition-all"
                  placeholder="123456"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-primary hover:bg-primary/90 text-black font-black uppercase tracking-widest text-xs py-4 rounded transition-all active:scale-95 shadow-[0_0_20px_rgba(0,240,255,0.4)] flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Verify OTP</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => { setRequiresOtp(false); setError(''); setInfo(''); }}
                className="w-full text-[10px] text-slate-500 hover:text-slate-300 uppercase tracking-wider transition-colors"
              >
                Back to login
              </button>
            </form>
          ) : (
            <form onSubmit={handleCaptchaVerify} className="space-y-5">
              <div className="text-center mb-2">
                <Shuffle className="w-10 h-10 text-warning mx-auto mb-2" />
                <p className="text-lg font-headline font-bold text-white">Security Check</p>
                <p className="text-[10px] text-slate-500 mt-1">Enter the challenge code below</p>
              </div>
              <div className="space-y-1">
                <div className="rounded-lg bg-black/40 border border-slate-800 px-4 py-3 text-center tracking-[0.5em] text-xl font-mono font-semibold text-warning select-all">
                  {captchaPrompt || '------'}
                </div>
              </div>
              <div className="space-y-1">
                <input
                  type="text"
                  required
                  className="w-full bg-black/40 border-slate-800 rounded-lg py-3 text-center uppercase font-mono tracking-[0.3em] text-white placeholder:text-slate-700 focus:outline-none focus:border-primary transition-all"
                  placeholder="Enter code"
                  value={captchaAnswer}
                  onChange={(e) => setCaptchaAnswer(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-warning hover:bg-warning/90 text-black font-black uppercase tracking-widest text-xs py-4 rounded transition-all active:scale-95 shadow-[0_0_20px_rgba(255,191,0,0.4)] flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Verify</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => { setRequiresCaptcha(false); setError(''); setInfo(''); }}
                className="w-full text-[10px] text-slate-500 hover:text-slate-300 uppercase tracking-wider transition-colors"
              >
                Back to login
              </button>
            </form>
          )}
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
        <div className="text-[9px] text-slate-700 font-mono">
          Encrypted Connection: SHA-512_RSA_2048
        </div>
        <div className="flex items-center space-x-4 text-[9px] uppercase tracking-widest text-slate-700">
          <span>SEC_INIT: OK</span>
          <span className="w-px h-3 bg-slate-800" />
          <span>NET: SECURE_TUNNEL</span>
          <span className="w-px h-3 bg-slate-800" />
          <span>NODE_SYNC: ACTIVE</span>
        </div>
        <div className="text-[8px] text-slate-800 font-mono text-center leading-relaxed max-w-md">
          [BOOT_SEQUENCE]: AES-256_GCM_INIT • TLS_1.3_HANDSHAKE • SECURE_CHANNEL_ESTABLISHED<br />
          [AUTH_GATE]: BEACON_SYNC_OK • THREAT_INTEL_LOADED • BIOMETRIC_SCANNER_ARMED<br />
          [SYSTEM]: READY_FOR_OPERATOR_AUTHENTICATION
        </div>
      </footer>
    </div>
  );
}
