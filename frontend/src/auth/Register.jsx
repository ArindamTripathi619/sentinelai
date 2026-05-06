import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useBehavioral } from '../sdk/behavioral';
import { ShieldAlert, User, Mail, Lock, ArrowRight } from 'lucide-react';
import { api } from '../lib/api';
import { supabase } from '../lib/supabase';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();
  const getBehavioralPayload = useBehavioral();

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const { data, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/login`,
          data: {
            full_name: name,
          },
        },
      });

      if (authError) {
        throw authError;
      }

      if (data.session) {
        const behavioralData = getBehavioralPayload();
        try {
          await api.post('/sync', {
            event_type: 'register',
            behavioral: behavioralData,
            ip_address: '127.0.0.1',
            user_agent: navigator.userAgent,
            country: 'US',
          });
        } catch (syncErr) {
          // Do not block successful auth on trust-sync/network issues.
          console.warn('Trust sync failed after register:', syncErr);
        }
        navigate('/dashboard', { replace: true });
        return;
      }

      setSuccess('Registration successful. Check your email to confirm your account, then sign in.');
      setTimeout(() => navigate('/login', { replace: true }), 1500);
    } catch (err) {
      const message = err?.message || err?.response?.data?.detail || 'Registration failed';
      const isAlreadyRegistered = /already registered|already exists|user already/i.test(String(message));

      if (isAlreadyRegistered) {
        try {
          const { error: resendError } = await supabase.auth.resend({
            type: 'signup',
            email,
            options: {
              emailRedirectTo: `${window.location.origin}/login`,
            },
          });

          if (!resendError) {
            setSuccess('This email is already registered. A fresh confirmation link has been sent.');
            setError('');
            return;
          }
        } catch (resendErr) {
          console.warn('Resend confirmation failed:', resendErr);
        }
      }

      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Dynamic Background */}
      <div className="absolute inset-0 z-0 overflow-hidden">
        <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-indigo-500/20 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-teal-500/20 blur-[120px] rounded-full"></div>
      </div>

      <div className="z-10 w-full max-w-md bg-gray-800/50 backdrop-blur-xl border border-gray-700 p-8 rounded-2xl shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-indigo-500/20 p-3 rounded-full mb-4 ring-1 ring-indigo-500/50">
            <ShieldAlert className="w-8 h-8 text-indigo-400" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Create Account</h1>
          <p className="text-gray-400 mt-2 text-sm text-center">
            Behavioral analysis will run during signup
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
            {success}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-5">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-300">Full Name</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-gray-500" />
              </div>
              <input
                type="text"
                required
                className="w-full bg-gray-900/50 border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-300">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-gray-500" />
              </div>
              <input
                type="email"
                required
                className="w-full bg-gray-900/50 border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                placeholder="john@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-300">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-500" />
              </div>
              <input
                type="password"
                required
                className="w-full bg-gray-900/50 border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-lg py-2.5 px-4 flex items-center justify-center space-x-2 transition-all transform hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-70 disabled:cursor-not-allowed mt-2"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <>
                <span>Complete Registration</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
