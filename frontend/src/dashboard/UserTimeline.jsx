import React, { useEffect, useState } from 'react';
import {
  X, Loader, AlertCircle, Clock, MapPin, Zap, History,
  ChevronRight, ArrowLeft, Filter, Download, CalendarRange, SlidersHorizontal,
  Shield, LayoutDashboard, Users, Activity, Bell, Eye, UserCheck
} from 'lucide-react';
import { api } from '../lib/api';

const ACTION_FILTERS = [
  { value: 'all', label: 'All actions' },
  { value: 'register', label: 'Register' },
  { value: 'login', label: 'Login' },
  { value: 'login_failed', label: 'Login Failed' },
  { value: 'otp_sent', label: 'OTP sent' },
  { value: 'otp_verified', label: 'OTP verified' },
  { value: 'captcha_verified', label: 'CAPTCHA verified' },
  { value: 'quarantined', label: 'Quarantined' },
  { value: 'geo_drift', label: 'Geo Drift' },
  { value: 'blocked', label: 'Blocked' },
];

const SCORE_FILTERS = [
  { value: 'all', label: 'All trust bands' },
  { value: 'high', label: 'Critical (<20)' },
  { value: 'medium', label: 'Elevated (20-39)' },
  { value: 'low', label: 'Moderate (40-69)' },
  { value: 'safe', label: 'Safe (70+)' },
];

const WINDOW_FILTERS = [
  { value: 'all', label: 'All time' },
  { value: '24h', label: 'Last 24 hours' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
];

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'events', label: 'Events', icon: Activity },
  { id: 'alerts', label: 'Alerts', icon: Bell },
];

export default function UserTimeline({ userId, userEmail, onClose, mode = 'modal' }) {
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [resolvedUserEmail, setResolvedUserEmail] = useState(userEmail || '');

  useEffect(() => {
    if (userEmail) setResolvedUserEmail(userEmail);
  }, [userEmail]);
  const [userDetail, setUserDetail] = useState(null);
  const [actionFilter, setActionFilter] = useState('all');
  const [scoreFilter, setScoreFilter] = useState('all');
  const [windowFilter, setWindowFilter] = useState('all');

  useEffect(() => {
    if (!userId) {
      setTimeline([]);
      setUserDetail(null);
      setLoading(false);
      return;
    }

    const fetchTimeline = async () => {
      try {
        setLoading(true);
        setError('');
        const [timelineRes, userRes] = await Promise.allSettled([
          api.get(`/users/${userId}/timeline`),
          api.get(`/users/${userId}`),
        ]);
        if (timelineRes.status === 'fulfilled') {
          setResolvedUserEmail(timelineRes.value.data.user_email || userEmail || '');
          setTimeline(timelineRes.value.data.timeline || timelineRes.value.data.events || []);
        } else {
          setError(timelineRes.reason?.response?.data?.detail || 'Failed to load timeline');
        }
        if (userRes.status === 'fulfilled') {
          setUserDetail(userRes.value.data);
        }
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load timeline');
      } finally {
        setLoading(false);
      }
    };

    fetchTimeline();
  }, [userId, userEmail]);

  const isPageMode = mode === 'page';
  const filteredTimeline = timeline.filter((event) => {
    const action = (event.action_type || event.action || '').toLowerCase();
    const trustScore = Number(event.trust_score ?? event.trust_score_at_time ?? 0);
    const eventTimestamp = event.timestamp ? new Date(event.timestamp).getTime() : 0;

    if (actionFilter !== 'all' && action !== actionFilter) return false;
    if (scoreFilter !== 'all') {
      if (scoreFilter === 'high' && trustScore >= 20) return false;
      if (scoreFilter === 'medium' && (trustScore < 20 || trustScore >= 40)) return false;
      if (scoreFilter === 'low' && (trustScore < 40 || trustScore >= 70)) return false;
      if (scoreFilter === 'safe' && trustScore < 70) return false;
    }
    if (windowFilter !== 'all' && eventTimestamp) {
      const now = Date.now();
      const cutoffMs = windowFilter === '24h' ? 86400000 : windowFilter === '7d' ? 604800000 : 2592000000;
      if (now - eventTimestamp > cutoffMs) return false;
    }
    return true;
  });

  const getActionBadgeColor = (action) => {
    switch (action?.toLowerCase()) {
      case 'register': return 'text-primary border-primary/30 bg-primary/10';
      case 'login': return 'text-safe border-safe/30 bg-safe/10';
      case 'login_failed': return 'text-critical border-critical/30 bg-critical/10';
      case 'otp_sent': case 'otp_verified': return 'text-primary border-primary/30 bg-primary/10';
      case 'captcha_verified': return 'text-warning border-warning/30 bg-warning/10';
      case 'flagged': case 'blocked': return 'text-critical border-critical/30 bg-critical/10';
      case 'quarantined': return 'text-amber border-amber/30 bg-amber/10';
      case 'geo_drift': return 'text-accent border-accent/30 bg-accent/10';
      default: return 'text-slate-500 border-slate-700 bg-slate-900';
    }
  };

  const getTrustScoreColor = (score) => {
    if (score < 20) return 'text-critical';
    if (score < 40) return 'text-warning';
    if (score < 70) return 'text-warning';
    return 'text-safe';
  };

  const resetFilters = () => {
    setActionFilter('all');
    setScoreFilter('all');
    setWindowFilter('all');
  };

  const escapeCsv = (value) => {
    const normalized = value === null || value === undefined ? '' : String(value);
    const escaped = normalized.replace(/"/g, '""');
    return /[",\n]/.test(escaped) ? `"${escaped}"` : escaped;
  };

  const handleExportCsv = () => {
    const headers = ['timestamp', 'action', 'description', 'trust_score', 'country', 'ip_address', 'user_agent', 'metadata'];
    const rows = filteredTimeline.map((event) => [
      event.timestamp || '',
      event.action_type || event.action || '',
      event.description || '',
      event.trust_score ?? event.trust_score_at_time ?? '',
      event.country || '',
      event.ip_address || '',
      event.user_agent || '',
      event.metadata ? JSON.stringify(event.metadata) : '',
    ]);

    const csv = [headers, ...rows].map((row) => row.map(escapeCsv).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sentinelai-timeline-${userId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  if (isPageMode) {
    return (
      <div className="min-h-screen bg-surface flex font-body text-slate-300">
        <aside className="w-56 flex-shrink-0 bg-surface border-r border-slate-800/50 flex flex-col">
          <div className="p-3 border-b border-slate-800/50">
            <div className="flex items-center gap-2">
              <div className="bg-primary/10 p-1.5 rounded ring-1 ring-primary/30 flex-shrink-0">
                <Shield className="w-4 h-4 text-primary" />
              </div>
              <span className="font-headline font-black text-xs tracking-tighter text-white">SENTNEL_AI</span>
            </div>
          </div>
          <nav className="flex-1 py-3 space-y-0.5 px-2">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded text-xs transition-all ${
                  item.id === 'timeline'
                    ? 'bg-accent/10 text-accent border-l-2 border-accent'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-900/50'
                }`}
              >
                <item.icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
          <button onClick={onClose} className="m-3 p-2 text-xs text-slate-500 hover:text-primary bg-slate-900/50 hover:bg-primary/10 rounded transition-all flex items-center gap-2.5">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>
        </aside>

        <main className="flex-1 overflow-y-auto">
          <header className="sticky top-0 z-20 bg-surface/80 backdrop-blur-xl border-b border-slate-800/30 px-5 py-3">
            <div className="flex items-center gap-2 text-[10px] text-slate-600 mb-1 font-mono">
              <button onClick={onClose} className="text-primary hover:text-primary/80 transition-colors">Dashboard</button>
              <ChevronRight className="w-3 h-3" />
              User Timeline
            </div>
            <h1 className="text-sm font-headline font-bold text-white">User Investigation</h1>
            <p className="text-[10px] text-slate-500 mt-0.5">{resolvedUserEmail || userEmail || `User ${userId?.slice(0, 8) || 'Unknown'}`}</p>
          </header>

          <div className="max-w-6xl mx-auto p-5 space-y-5">
            <div className="glass-panel p-4 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="bg-accent/10 p-2.5 rounded-full ring-1 ring-accent/30">
                  <UserCheck className="w-5 h-5 text-accent" />
                </div>
                <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-[9px] text-slate-600 uppercase tracking-wider">Trust Score</p>
                    <p className={`text-lg font-bold font-headline ${userDetail ? (userDetail.trust_score >= 70 ? 'text-safe' : userDetail.trust_score >= 40 ? 'text-warning' : 'text-critical') : 'text-primary'}`}>
                      {userDetail ? `${userDetail.trust_score}/100` : loading ? '—' : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-[9px] text-slate-600 uppercase tracking-wider">Risk Level</p>
                    {userDetail ? (
                      <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded inline-block border ${
                        userDetail.trust_score < 20 ? 'text-critical border-critical/30 bg-critical/10' :
                        userDetail.trust_score < 40 ? 'text-critical border-critical/30 bg-critical/10' :
                        userDetail.trust_score < 70 ? 'text-warning border-warning/30 bg-warning/10' :
                        'text-safe border-safe/30 bg-safe/10'
                      }`}>
                        {userDetail.trust_score < 20 ? 'CRITICAL' :
                         userDetail.trust_score < 40 ? 'HIGH' :
                         userDetail.trust_score < 70 ? 'ELEVATED' : 'LOW'}
                      </span>
                    ) : (
                      <span className="text-[9px] text-amber bg-amber/10 border border-amber/30 px-2 py-0.5 rounded inline-block font-bold uppercase tracking-wider">
                        {loading ? 'Loading...' : 'Pending'}
                      </span>
                    )}
                  </div>
                  <div>
                    <p className="text-[9px] text-slate-600 uppercase tracking-wider">Total Events</p>
                    <p className="text-lg font-bold font-headline text-white">{timeline.length}</p>
                  </div>
                  <div>
                    <p className="text-[9px] text-slate-600 uppercase tracking-wider">Filtered</p>
                    <p className="text-lg font-bold font-headline text-white">
                      {filteredTimeline.length}
                      <span className="text-[10px] text-slate-600 font-sans font-normal ml-1">/ {timeline.length}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-lg">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-2 text-slate-300">
                  <Filter className="w-3.5 h-3.5 text-accent" />
                  <span className="text-[10px] font-medium uppercase tracking-wider">Timeline Filters</span>
                </div>
                <button
                  onClick={handleExportCsv}
                  disabled={filteredTimeline.length === 0}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-primary/20 bg-primary/10 px-3 py-1.5 text-[9px] text-primary transition-colors hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Download className="w-3 h-3" />
                  Export CSV
                </button>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                <label className="space-y-1">
                  <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-slate-600">
                    <SlidersHorizontal className="w-3 h-3" /> Action Type
                  </span>
                  <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}
                    className="w-full rounded-lg border border-slate-800/50 bg-slate-900/80 px-3 py-2 text-[10px] text-slate-300 outline-none transition-colors focus:border-primary/40">
                    {ACTION_FILTERS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
                  </select>
                </label>
                <label className="space-y-1">
                  <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-slate-600">
                    <CalendarRange className="w-3 h-3" /> Time Window
                  </span>
                  <select value={windowFilter} onChange={(e) => setWindowFilter(e.target.value)}
                    className="w-full rounded-lg border border-slate-800/50 bg-slate-900/80 px-3 py-2 text-[10px] text-slate-300 outline-none transition-colors focus:border-primary/40">
                    {WINDOW_FILTERS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
                  </select>
                </label>
                <label className="space-y-1">
                  <span className="flex items-center gap-1 text-[9px] uppercase tracking-wider text-slate-600">
                    <Filter className="w-3 h-3" /> Trust Band
                  </span>
                  <select value={scoreFilter} onChange={(e) => setScoreFilter(e.target.value)}
                    className="w-full rounded-lg border border-slate-800/50 bg-slate-900/80 px-3 py-2 text-[10px] text-slate-300 outline-none transition-colors focus:border-primary/40">
                    {SCORE_FILTERS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
                  </select>
                </label>
              </div>

              <div className="mt-2 flex justify-between items-center">
                <button onClick={resetFilters} className="text-[9px] text-slate-600 hover:text-slate-400 transition-colors">
                  Reset filters
                </button>
              </div>
            </div>

            <div className="space-y-3">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader className="w-8 h-8 text-primary animate-spin" />
                </div>
              ) : error ? (
                <div className="flex items-center gap-3 bg-critical/10 border border-critical/30 rounded-lg p-4 text-critical text-xs">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              ) : filteredTimeline.length === 0 ? (
                <div className="text-center py-16 text-slate-600">
                  <Clock className="w-8 h-8 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No activity matches the current filters</p>
                </div>
              ) : (
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-px bg-gradient-to-b from-accent/40 via-primary/20 to-transparent" />
                  {filteredTimeline.map((event, index) => {
                    const action = event.action_type || event.action;
                    return (
                      <div key={`${event.timestamp}-${index}`} className="relative pl-10 pb-4">
                        <div className="absolute left-[14px] top-1.5 w-2 h-2 rounded-full bg-accent ring-2 ring-surface z-10" />
                        <div className="glass-panel p-4 rounded-lg">
                          <div className="flex items-start gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2 flex-wrap">
                                <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${getActionBadgeColor(action)}`}>
                                  {formatActionLabel(action)}
                                </span>
                                {(event.trust_score !== undefined || event.trust_score_at_time !== undefined) && (
                                  <span className={`text-[9px] font-bold ${getTrustScoreColor(event.trust_score ?? event.trust_score_at_time)}`}>
                                    Trust: {event.trust_score ?? event.trust_score_at_time}
                                  </span>
                                )}
                                {event.country && (
                                  <span className="text-[9px] px-2 py-0.5 rounded-full border border-slate-800/50 text-slate-400">
                                    {event.country}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-400 mb-2">{event.description || 'Event occurred'}</p>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[9px] text-slate-600">
                                <div className="flex items-center gap-1.5">
                                  <Clock className="w-3 h-3" />
                                  <span className="font-mono">{event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'}</span>
                                </div>
                                {event.ip_address && (
                                  <div className="flex items-center gap-1.5">
                                    <MapPin className="w-3 h-3" />
                                    <span className="font-mono">{event.ip_address}</span>
                                  </div>
                                )}
                                {event.user_agent && (
                                  <div className="flex items-center gap-1.5 md:col-span-2">
                                    <Zap className="w-3 h-3" />
                                    <span className="truncate text-slate-600">{event.user_agent}</span>
                                  </div>
                                )}
                              </div>
                              {event.metadata && Object.keys(event.metadata).length > 0 && (
                                <div className="mt-2 bg-slate-900/60 border border-slate-800/30 rounded p-2">
                                  <div className="flex items-center gap-1.5 mb-1 text-slate-600">
                                    <Eye className="w-3 h-3" />
                                    <span className="text-[8px] uppercase tracking-wider">Metadata</span>
                                  </div>
                                  <pre className="whitespace-pre-wrap break-words text-[9px] leading-5 text-slate-500">{JSON.stringify(event.metadata, null, 2)}</pre>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-surface/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass-panel max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col rounded-lg">
        <div className="flex items-center justify-between p-4 border-b border-slate-800/50">
          <div className="flex items-center gap-2 text-slate-400">
            <History className="w-4 h-4" />
            <span className="text-[9px] uppercase tracking-widest">Forensic Replay</span>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : error ? (
            <div className="flex items-center gap-3 bg-critical/10 border border-critical/30 rounded-lg p-4 text-critical text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : filteredTimeline.length === 0 ? (
            <div className="text-center py-16 text-slate-600">
              <Clock className="w-8 h-8 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No activity matches the current filters</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTimeline.map((event, index) => (
                <div key={`${event.timestamp}-${index}`} className="bg-slate-900/60 border border-slate-800/40 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${getActionBadgeColor(event.action_type || event.action)}`}>
                      {formatActionLabel(event.action_type || event.action)}
                    </span>
                    {(event.trust_score !== undefined || event.trust_score_at_time !== undefined) && (
                      <span className={`text-[9px] font-bold ${getTrustScoreColor(event.trust_score ?? event.trust_score_at_time)}`}>
                        Trust: {event.trust_score ?? event.trust_score_at_time}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mb-2">{event.description || 'Event occurred'}</p>
                  <div className="grid grid-cols-2 gap-2 text-[9px] text-slate-600">
                    <div className="flex items-center gap-1.5"><Clock className="w-3 h-3" />{event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'}</div>
                    {event.ip_address && <div className="flex items-center gap-1.5"><MapPin className="w-3 h-3" /><span className="font-mono">{event.ip_address}</span></div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatActionLabel(action) {
  if (!action) return 'Unknown';
  return action.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}
