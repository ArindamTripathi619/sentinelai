import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer
} from 'recharts';
import {
  Shield, ShieldAlert, Users, Activity, AlertTriangle, Search,
  LogOut, LayoutDashboard, Clock, Bell, ChevronRight, Settings,
  Terminal, GitBranch, Zap, Globe, UserCheck
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Eye } from 'lucide-react';
import { api, clearUserSession, getAuthToken } from '../lib/api';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard, route: '/dashboard' },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'events', label: 'Events', icon: Activity, route: '/events' },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'settings', label: 'Settings', icon: Settings },
];

const TIME_WINDOWS = [
  { key: '1h', label: '1H', bucket: '1min' },
  { key: '6h', label: '6H', bucket: '5min' },
  { key: '24h', label: '24H', bucket: '30min' },
  { key: '7d', label: '7D', bucket: '1h' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const [summary, setSummary] = useState(null);
  const [velocityData, setVelocityData] = useState([]);
  const [trustDistribution, setTrustDistribution] = useState([]);
  const [users, setUsers] = useState([]);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalUsers, setTotalUsers] = useState(0);
  const [timeWindow, setTimeWindow] = useState('1h');
  const [currentTime, setCurrentTime] = useState(new Date().toISOString().slice(11, 19) + ' UTC');
  const [adminEmail, setAdminEmail] = useState('OPERATOR');

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setAdminEmail(payload.email?.split('@')[0]?.toUpperCase() || 'OPERATOR');
      } catch {}
    }
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toISOString().slice(11, 19) + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const getAlertIcon = (alertType) => {
    switch (alertType?.toLowerCase()) {
      case 'bot_wave': return <Zap className="w-5 h-5 text-accent" />;
      case 'geo_drift': return <Globe className="w-5 h-5 text-warning" />;
      case 'speed_bot': return <Zap className="w-5 h-5 text-critical" />;
      case 'duplicate_device': return <Activity className="w-5 h-5 text-accent" />;
      case 'email_pattern': return <Shield className="w-5 h-5 text-warning" />;
      case 'velocity_spike': return <TrendingUp className="w-5 h-5 text-critical" />;
      default: return <ShieldAlert className="w-5 h-5 text-accent" />;
    }
  };

  const getRiskProfile = (score) => {
    if (score < 20) return { label: 'CRIT', color: 'text-critical', bg: 'bg-critical/10 border-critical/20' };
    if (score < 40) return { label: 'HIGH', color: 'text-critical', bg: 'bg-critical/5 border-critical/20' };
    if (score < 70) return { label: 'MED', color: 'text-warning', bg: 'bg-warning/10 border-warning/20' };
    return { label: 'LOW', color: 'text-safe', bg: 'bg-safe/10 border-safe/20' };
  };

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'active': case 'authorized': return { label: 'AUTHORIZED', color: 'text-safe bg-safe/10' };
      case 'challenged': return { label: 'CHALLENGED', color: 'text-warning bg-warning/10' };
      case 'quarantined': return { label: 'QUARANTINED', color: 'text-critical bg-critical/10' };
      case 'blocked': return { label: 'BLOCKED', color: 'text-critical bg-critical/10' };
      default: return { label: (status || 'unknown').toUpperCase(), color: 'text-slate-500 bg-slate-900' };
    }
  };

  const getRelativeTime = (timestamp) => {
    if (!timestamp) return '—';
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const getUserInitials = (email) => {
    if (!email) return '?';
    const parts = email.split('@')[0].split(/[._-]/);
    return parts.map(p => p[0]).join('').toUpperCase().slice(0, 2) || '?';
  };

  const kpis = summary ? [
    {
      title: 'Total Users', value: summary.total_users?.toLocaleString() || '0',
      icon: Users
    },
    {
      title: 'Avg Trust Score', value: summary.avg_trust_score ?? '—',
      icon: Shield, gauge: true, gaugeValue: Math.round(summary.avg_trust_score || 0)
    },
    {
      title: 'Active Alerts', value: summary.active_alerts ?? '0',
      icon: Activity, critical: true
    },
    {
      title: 'Threats Detected', value: summary.flagged_today ?? '0',
      icon: ShieldAlert, critical: true
    },
  ] : [];

  const windowConfig = TIME_WINDOWS.find(w => w.key === timeWindow) || TIME_WINDOWS[0];

  useEffect(() => {
    let mounted = true;

    const loadDashboard = async () => {
      try {
        setError('');
        const offset = (currentPage - 1) * pageSize;
        const searchParam = searchQuery ? `&q=${encodeURIComponent(searchQuery)}` : '';
        const [summaryRes, velocityRes, trustRes, usersRes, alertsRes] = await Promise.all([
          api.get('/analytics/summary'),
          api.get(`/analytics/velocity?window=${windowConfig.key}&bucket=${windowConfig.bucket}`),
          api.get('/analytics/trust-distribution'),
          api.get(`/users?limit=${pageSize}&offset=${offset}${searchParam}`),
          api.get('/alerts?limit=15'),
        ]);

        if (!mounted) return;

        setSummary(summaryRes.data);
        setTotalUsers(usersRes.data.total || 0);
        setVelocityData((velocityRes.data.data || []).map((point, index) => ({
          time: point.timestamp
            ? new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : `T${index + 1}`,
          signups: point.registrations ?? 0,
        })));

        const bands = trustRes.data.bands || [];
        const totalCount = bands.reduce((sum, b) => sum + (b.count || 0), 0);
        const bandColors = ['#00f0ff', '#00ff87', '#ffbf00', '#ff3355', '#cc0044'];
        const mappedBands = bands.map((b, i) => ({
          label: b.label || `Band ${i + 1}`,
          count: b.count,
          color: bandColors[i % bandColors.length],
        }));

        setTrustDistribution(mappedBands.map(d => ({
          ...d,
          pct: totalCount > 0 ? Math.round((d.count / totalCount) * 100) : 0,
        })));

        setUsers(usersRes.data.users || []);
        setLiveAlerts((alertsRes.data.alerts || []).map((a) => ({
          id: a.alert_id,
          type: a.type,
          desc: a.description || a.type,
          severity: a.severity,
          time: new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        })));
      } catch (err) {
        if (!mounted) return;
        if (err?.response?.status === 401) {
          clearUserSession();
          navigate('/login', { replace: true });
          return;
        }
        setError(err?.response?.data?.detail || 'Failed to load dashboard');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadDashboard();
    const interval = setInterval(loadDashboard, 4000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [currentPage, pageSize, timeWindow, searchQuery, navigate]);

  const handleLogout = () => {
    clearUserSession();
    navigate('/login', { replace: true });
  };

  const filteredUsers = users;

  const totalDistCount = trustDistribution.reduce((s, d) => s + d.count, 0);
  const newAlertCount = liveAlerts.length;

  const handleDismissAlert = async (alertId) => {
    try {
      await api.patch(`/alerts/${alertId}/resolve`);
      setLiveAlerts(prev => prev.filter(a => a.id !== alertId));
    } catch {
    }
  };

  const handleExportCsv = () => {
    const headers = ['Email,Trust Score,Status,Last Activity'];
    const rows = users.map(u =>
      `${u.email || ''},${u.trust_score ?? ''},${u.status || ''},${u.last_login_at || u.registered_at || ''}`
    );
    const csv = [...headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sentinelai_users_export.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-surface flex font-body text-slate-300">
      <aside className="h-screen w-56 fixed left-0 top-0 bg-[#0a0a0f]/80 backdrop-blur-md border-r border-primary/20 shadow-[4px_0_24px_rgba(0,0,0,0.5)] flex flex-col py-6 px-3 z-50">
        <div className="mb-8 px-2">
          <h1 className="text-base font-headline font-black tracking-widest text-primary drop-shadow-[0_0_8px_rgba(0,240,255,0.6)]">SENTNEL_AI</h1>
          <p className="font-headline tracking-tighter uppercase text-[10px] text-slate-500 mt-1">V_2.0.4 STATUS: ACTIVE</p>
        </div>
        <nav className="flex-1 space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive = item.route ? location.pathname === item.route : false;
            return (
              <button
                key={item.id}
                onClick={() => item.route && navigate(item.route)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 text-xs transition-all duration-200 ${
                  isActive
                    ? 'border-l-4 border-primary bg-gradient-to-r from-primary/10 to-transparent text-primary font-bold'
                    : 'text-slate-400 hover:bg-primary/5 hover:text-primary border-l-4 border-transparent'
                }`}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                <span className="font-headline tracking-tighter uppercase text-[11px]">{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="mt-auto space-y-4">
          <button className="w-full py-2.5 bg-transparent border border-primary/40 text-primary font-headline text-[10px] tracking-widest hover:bg-primary hover:text-surface transition-all duration-300">
            INITIATE SCAN
          </button>
          <div className="pt-4 border-t border-white/5 flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded border border-primary/30 bg-primary/5 flex items-center justify-center">
                <Shield className="w-4 h-4 text-primary/60" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-2.5 h-2.5 bg-safe rounded-full border-2 border-surface"></div>
            </div>
            <div>
              <p className="text-[11px] font-bold text-white uppercase tracking-wider">{adminEmail}</p>
              <p className="text-[9px] text-primary/60 uppercase">
                {summary ? `Security Clearance ${Math.min(5, Math.max(1, Math.round((summary.avg_trust_score || 0) / 20)))}` : '—'}
              </p>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <button className="flex items-center gap-2 text-slate-500 hover:text-primary transition-colors text-[10px] uppercase font-bold tracking-widest">
              <Shield className="w-3 h-3" /> Security Log
            </button>
            <button onClick={handleLogout} className="flex items-center gap-2 text-slate-500 hover:text-critical transition-colors text-[10px] uppercase font-bold tracking-widest">
              <LogOut className="w-3 h-3" /> Logout
            </button>
          </div>
        </div>
      </aside>

      <main className="ml-56 flex-1 min-h-screen">
        <header className="fixed top-0 right-0 left-56 h-14 bg-[#0a0a0f]/60 backdrop-blur-xl border-b border-primary/20 flex justify-between items-center px-6 z-40">
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <h2 className="text-white font-headline font-black text-sm tracking-[0.2em] uppercase">Command Center</h2>
              <span className="bg-safe/10 text-safe text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 border border-safe/20">
                <span className="w-1.5 h-1.5 bg-safe rounded-full animate-ping" />
                LIVE
              </span>
            </div>
            <div className="relative w-56 group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500" />
              <input
                type="text"
                className="bg-[#1a1a2e]/50 border-none text-[10px] tracking-widest focus:ring-1 focus:ring-primary/50 w-full pl-9 h-8 rounded text-slate-300 placeholder:text-slate-600 transition-all outline-none"
                placeholder="SEARCH USERS BY EMAIL..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
          </div>
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-4 text-slate-400">
              <button className="text-primary border-b-2 border-primary pb-1 font-body text-xs tracking-widest uppercase">LIVE_FEED</button>
              <button className="text-slate-500 hover:text-accent transition-colors font-body text-xs tracking-widest uppercase">NETWORK_MAP</button>
            </div>
            <div className="flex items-center gap-3">
              <button className="relative text-slate-400 hover:text-primary transition-all">
                <Bell className="w-4 h-4" />
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-accent rounded-full"></span>
              </button>
              <button className="text-slate-400 hover:text-primary transition-all">
                <Terminal className="w-4 h-4" />
              </button>
              <button className="text-slate-400 hover:text-primary transition-all">
                <GitBranch className="w-4 h-4" />
              </button>
              <div className="h-5 w-px bg-white/10"></div>
              <span className="text-primary font-headline text-[11px] tracking-widest font-bold">{currentTime}</span>
            </div>
          </div>
        </header>

        <div className="pt-20 px-6 pb-10 space-y-6">
          {error && (
            <div className="rounded border border-critical/30 bg-critical/10 px-4 py-3 text-xs text-critical flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-critical" />
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {kpis.map((card) => (
              <div key={card.title} className={`glass-panel p-4 relative overflow-hidden group ${card.critical ? 'border-critical/30' : ''}`}>
                {card.icon && (
                  <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                    <card.icon className={`w-8 h-8 ${card.critical ? 'text-critical' : 'text-primary'}`} />
                  </div>
                )}
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-1">{card.title}</p>
                <div className="flex items-end justify-between">
                  <h3 className={`text-2xl font-headline font-black text-white ${!card.critical ? 'drop-shadow-[0_0_8px_rgba(0,240,255,0.3)]' : ''}`}>
                    {loading ? (
                      <span className="inline-block w-12 h-6 bg-slate-800/60 rounded animate-pulse" />
                    ) : (
                      card.value
                    )}
                  </h3>
                  <div className="flex items-center mb-1">
                    {card.online && (
                      <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 bg-primary rounded-full animate-ping" />
                        <span className="text-primary text-[10px] font-bold">ONLINE</span>
                      </div>
                    )}
                    {card.gauge && (
                      <div className="relative w-10 h-10">
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 40 40">
                          <circle cx="20" cy="20" r="16" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
                          <circle
                            cx="20" cy="20" r="16" fill="transparent" stroke="#00f0ff"
                            strokeWidth="4"
                            strokeDasharray="100.5"
                            strokeDashoffset={100.5 - (100.5 * (card.gaugeValue || 0) / 100)}
                            strokeLinecap="round"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-primary">{card.gaugeValue || 0}%</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 lg:col-span-8 space-y-6">
              <div className="glass-panel p-5">
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center gap-3">
                    <Activity className="w-4 h-4 text-primary" />
                    <h4 className="text-[11px] font-headline font-bold tracking-widest uppercase">Request Velocity</h4>
                  </div>
                  <div className="flex gap-1">
                    {TIME_WINDOWS.map((w) => (
                      <button
                        key={w.key}
                        onClick={() => setTimeWindow(w.key)}
                        className={`px-3 py-1 text-[10px] font-bold tracking-widest border transition-colors ${
                          timeWindow === w.key
                            ? 'border-primary text-primary bg-primary/10'
                            : 'border-white/10 text-slate-500 hover:text-white'
                        }`}
                      >
                        {w.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="relative h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={velocityData} margin={{ top: 8, right: 8, left: 4, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="time" stroke="#475569" axisLine={false} tickLine={false} tickMargin={6} height={20} fontSize={9} />
                      <YAxis stroke="#475569" axisLine={false} tickLine={false} fontSize={9} />
                      <RechartsTooltip
                        contentStyle={{ backgroundColor: '#0a0a0f', border: '1px solid rgba(0,240,255,0.2)', borderRadius: '0.125rem', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}
                        itemStyle={{ color: '#00f0ff', fontSize: '11px' }}
                      />
                      <defs>
                        <linearGradient id="vGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#00f0ff" stopOpacity={0.2} />
                          <stop offset="100%" stopColor="#00f0ff" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Line type="monotone" dataKey="signups" stroke="#00f0ff" strokeWidth={2} dot={false} activeDot={{ r: 3, fill: '#00f0ff', strokeWidth: 0 }} fill="url(#vGrad)" />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-surface/80 border border-primary/40 px-3 py-1.5 text-[10px] tracking-tighter backdrop-blur-sm shadow-xl pointer-events-none">
                    <span className="text-slate-500">TIMESTAMP:</span> {currentTime}<br />
                    <span className="text-primary">REQ_VOL:</span> {(velocityData.reduce((s, d) => s + d.signups, 0) || 0).toLocaleString()}/SEC
                  </div>
                </div>
              </div>

              <div className="glass-panel overflow-hidden">
                <div className="p-5 border-b border-white/5 flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <Users className="w-4 h-4 text-primary" />
                    <h4 className="text-[11px] font-headline font-bold tracking-widest uppercase">Recent Users</h4>
                  </div>
                  <button onClick={handleExportCsv} className="text-primary text-[10px] font-bold tracking-widest hover:underline uppercase">Export CSV</button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="bg-white/5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                        <th className="px-5 py-3.5">User Identity</th>
                        <th className="px-5 py-3.5">Trust Score</th>
                        <th className="px-5 py-3.5">Risk Profile</th>
                        <th className="px-5 py-3.5">Activity</th>
                        <th className="px-5 py-3.5">Status</th>
                        <th className="px-5 py-3.5"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-[11px]">
                      {filteredUsers.map((user) => {
                        const risk = getRiskProfile(user.trust_score);
                        const statusBadge = getStatusBadge(user.status);
                        return (
                          <tr key={user.user_id} className="hover:bg-white/5 transition-colors">
                            <td className="px-5 py-3">
                              <div className="flex items-center gap-3">
                                <div className="w-7 h-7 rounded border border-white/10 bg-primary/5 flex items-center justify-center text-[9px] font-bold text-primary flex-shrink-0">
                                  {getUserInitials(user.email)}
                                </div>
                                <div>
                                  <div className="text-white font-bold uppercase text-[11px]">
                                    {user.email?.split('@')[0]?.replace(/[._-]/g, '_') || 'Unknown'}
                                  </div>
                                  <div className="text-slate-500 text-[9px]">{user.email || '—'}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-5 py-3">
                              <span className={`font-bold ${user.trust_score >= 70 ? 'text-safe' : user.trust_score >= 40 ? 'text-warning' : 'text-critical'}`}>
                                {user.trust_score ?? '—'}/100
                              </span>
                            </td>
                            <td className="px-5 py-3">
                              <span className={`px-2 py-0.5 ${risk.bg} ${risk.color} border rounded text-[9px] font-bold`}>
                                {risk.label}
                              </span>
                            </td>
                            <td className="px-5 py-3 text-slate-400">{getRelativeTime(user.last_login_at || user.registered_at)}</td>
                            <td className="px-5 py-3">
                              <div className="flex items-center gap-2">
                                <span className={`w-1.5 h-1.5 rounded-full ${
                                  user.trust_score >= 70 ? 'bg-safe' : user.trust_score >= 40 ? 'bg-warning' : 'bg-critical'
                                } ${user.trust_score < 20 ? 'animate-ping' : ''}`} />
                                <span className="text-slate-300">{statusBadge.label}</span>
                              </div>
                            </td>
                            <td className="px-5 py-3">
                              <button
                                onClick={() => navigate(`/dashboard/users/${user.user_id}/timeline`)}
                                className="text-slate-500 hover:text-primary transition-colors p-1"
                                title="View Timeline"
                              >
                                <Eye className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                      {filteredUsers.length === 0 && (
                        <tr>
                          <td colSpan={6} className="px-5 py-8 text-center text-xs text-slate-600">
                            No users match your search.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                {totalUsers > pageSize && (
                  <div className="flex items-center justify-between px-5 py-3 border-t border-white/5">
                    <span className="text-[9px] text-slate-500">
                      {Math.min((currentPage - 1) * pageSize + 1, totalUsers)}–{Math.min(currentPage * pageSize, totalUsers)} of {totalUsers}
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="px-2.5 py-1 text-[10px] font-bold border border-white/10 text-slate-400 hover:text-white hover:border-primary/40 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      >
                        Prev
                      </button>
                      {Array.from({ length: Math.min(5, Math.ceil(totalUsers / pageSize)) }, (_, i) => {
                        const totalPages = Math.ceil(totalUsers / pageSize);
                        let startPage = Math.max(1, currentPage - 2);
                        if (startPage + 4 > totalPages) startPage = Math.max(1, totalPages - 4);
                        const page = startPage + i;
                        if (page > totalPages) return null;
                        return (
                          <button
                            key={page}
                            onClick={() => setCurrentPage(page)}
                            className={`w-7 h-7 text-[10px] font-bold border transition-colors ${
                              currentPage === page
                                ? 'border-primary text-primary bg-primary/10'
                                : 'border-white/10 text-slate-500 hover:text-white'
                            }`}
                          >
                            {page}
                          </button>
                        );
                      })}
                      <button
                        onClick={() => setCurrentPage(p => Math.min(Math.ceil(totalUsers / pageSize), p + 1))}
                        disabled={currentPage >= Math.ceil(totalUsers / pageSize)}
                        className="px-2.5 py-1 text-[10px] font-bold border border-white/10 text-slate-400 hover:text-white hover:border-primary/40 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="col-span-12 lg:col-span-4 space-y-6">
              <div className="glass-panel p-5">
                <div className="flex items-center gap-3 mb-6">
                  <Activity className="w-4 h-4 text-primary" />
                  <h4 className="text-[11px] font-headline font-bold tracking-widest uppercase">Trust Distribution</h4>
                </div>
                <div className="flex flex-col items-center">
                  <div className="relative w-44 h-44 mb-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={trustDistribution.length > 0 ? trustDistribution : [{ label: 'No data', count: 1, color: '#1a1a2e' }]}
                          cx="50%" cy="50%"
                          innerRadius={32}
                          outerRadius={52}
                          paddingAngle={0}
                          dataKey="count"
                          nameKey="label"
                          stroke="none"
                        >
                          {trustDistribution.map((entry, idx) => (
                            <Cell key={idx} fill={entry.color} />
                          ))}
                        </Pie>
                        <RechartsTooltip
                          contentStyle={{ backgroundColor: '#0a0a0f', border: '1px solid rgba(0,240,255,0.2)', borderRadius: '0.125rem' }}
                          formatter={(value, name) => [`${value} nodes`, name]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <span className="text-xl font-headline font-black text-white">{totalDistCount.toLocaleString()}</span>
                      <span className="text-[8px] text-slate-500 uppercase tracking-widest">TOTAL_NODES</span>
                    </div>
                  </div>
                  <div className="w-full grid grid-cols-2 gap-3">
                    {trustDistribution.map((d) => (
                      <div key={d.label} className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
                        <span className="text-[10px] text-slate-400 font-bold uppercase">{d.label}: {d.pct}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="glass-panel p-5">
                <div className="flex justify-between items-center mb-5">
                  <div className="flex items-center gap-3">
                    <Bell className="w-4 h-4 text-accent" />
                    <h4 className="text-[11px] font-headline font-bold tracking-widest uppercase">Active Alerts</h4>
                  </div>
                  {newAlertCount > 0 && (
                    <span className="bg-accent/10 text-accent text-[9px] font-bold px-2 py-0.5 rounded border border-accent/20">
                      {newAlertCount} NEW
                    </span>
                  )}
                </div>
                <div className="space-y-3">
                  {liveAlerts.slice(0, 5).map((alert) => {
                    const alertColors = {
                      bot_wave: { border: 'border-accent/20', bg: 'bg-accent/5', hover: 'hover:bg-accent/10' },
                      geo_drift: { border: 'border-warning/20', bg: 'bg-warning/5', hover: 'hover:bg-warning/10' },
                      speed_bot: { border: 'border-critical/20', bg: 'bg-critical/5', hover: 'hover:bg-critical/10' },
                    };
                    const colors = alertColors[alert.type?.toLowerCase()] || { border: 'border-accent/20', bg: 'bg-accent/5', hover: 'hover:bg-accent/10' };
                    return (
                      <div key={alert.id} className={`p-3 ${colors.bg} ${colors.border} border flex gap-3 group ${colors.hover} transition-colors`}>
                        <div className="mt-0.5 flex-shrink-0">
                          {getAlertIcon(alert.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start mb-1">
                            <span className={`text-[10px] font-bold tracking-tighter uppercase ${
                              alert.type?.toLowerCase() === 'bot_wave' ? 'text-accent' :
                              alert.type?.toLowerCase() === 'geo_drift' ? 'text-warning' :
                              alert.type?.toLowerCase() === 'speed_bot' ? 'text-critical' : 'text-accent'
                            }`}>
                              {alert.type?.replace(/_/g, '_') || 'alert'}
                            </span>
                            <span className="text-[9px] text-slate-500 flex-shrink-0">{alert.time}</span>
                          </div>
                          <p className="text-[11px] text-slate-300 leading-tight mb-2">{alert.desc}</p>
                          <div className="flex gap-2">
                            <button className="px-2 py-1 bg-primary text-surface text-[9px] font-bold uppercase tracking-widest">
                              {alert.type?.toLowerCase() === 'bot_wave' ? 'Deploy Firewall' : 'Investigate'}
                            </button>
                            <button
                              onClick={() => handleDismissAlert(alert.id)}
                              className="px-2 py-1 border border-white/10 text-slate-400 text-[9px] font-bold uppercase tracking-widest hover:text-white"
                            >
                              Dismiss
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {liveAlerts.length === 0 && (
                    <div className="text-center py-6 text-xs text-slate-600">
                      No active alerts
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
