import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell
} from 'recharts';
import { 
  ShieldAlert, Users, Activity, Lock, AlertTriangle, 
  ChevronRight, Search, Server, Shield, LogOut
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api, clearUserSession } from '../lib/api';
import UserTimeline from './UserTimeline';

const COLORS = {
  Blocked: '#ef4444',     // Red
  Quarantine: '#f97316',  // Orange
  Suspicious: '#eab308',  // Yellow
  Safe: '#22c55e',        // Green
};

const BAND_COLORS = {
  green: '#22c55e',
  yellow: '#eab308',
  orange: '#f97316',
  red: '#ef4444',
  darkred: '#7f1d1d',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [velocityData, setVelocityData] = useState([]);
  const [trustScoreData, setTrustScoreData] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);

  const alerts = summary
    ? [
        {
          id: 'summary-1',
          type: 'Bot Waves',
          desc: `${summary.bot_waves_detected} bot wave(s) detected`,
          severity: summary.bot_waves_detected > 0 ? 'high' : 'low',
          time: 'Live',
        },
        {
          id: 'summary-2',
          type: 'Trust',
          desc: `${summary.quarantined} quarantined users, ${summary.blocked} blocked users`,
          severity: summary.blocked > 0 ? 'high' : 'medium',
          time: 'Live',
        },
      ]
    : [];

  const kpis = summary
    ? [
        { title: 'Total Users', value: summary.total_users, icon: Users, color: 'text-blue-400', bg: 'bg-blue-400/10' },
        { title: 'Flagged Today', value: summary.flagged_today, icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
        { title: 'Bot Waves Detected', value: summary.bot_waves_detected, icon: Activity, color: 'text-red-400', bg: 'bg-red-400/10' },
        { title: 'Quarantined', value: summary.quarantined, icon: Lock, color: 'text-orange-400', bg: 'bg-orange-400/10' },
      ]
    : [];

  useEffect(() => {
    let mounted = true;

    const loadDashboard = async () => {
      try {
        setError('');
        const [summaryRes, velocityRes, trustRes, usersRes] = await Promise.all([
          api.get('/analytics/summary'),
          api.get('/analytics/velocity?window=1h&bucket=1min'),
          api.get('/analytics/trust-distribution'),
          api.get('/users?limit=8&offset=0'),
        ]);

        if (!mounted) return;

        setSummary(summaryRes.data);
        setVelocityData((velocityRes.data.data || []).map((point, index) => ({
          time: point.timestamp ? new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : `T${index + 1}`,
          signups: point.registrations ?? 0,
        })));

        setTrustScoreData((trustRes.data.bands || []).map((band) => ({
          range: band.label,
          count: band.count,
          label: band.label,
          color: BAND_COLORS[band.color] || '#64748b',
        })));

        setUsers(usersRes.data.users || []);
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
    const interval = setInterval(loadDashboard, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    clearUserSession();
    navigate('/login', { replace: true });
  };

  const trustScoreCards = trustScoreData.length > 0 ? trustScoreData : [];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 font-sans">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-500/20 p-2 rounded-lg ring-1 ring-blue-500/50">
            <Shield className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">SentinelAI Command Center</h1>
            <p className="text-sm text-gray-400">Behavioral Intelligence Platform</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2 text-green-400 bg-green-400/10 px-3 py-1.5 rounded-full border border-green-400/20">
            <Server className="w-4 h-4" />
            <span>System Active</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 text-gray-300 hover:text-white bg-gray-800/80 border border-gray-700 px-3 py-1.5 rounded-full transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* KPI Row (Panel 5) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {kpis.map((card) => (
          <KPICard key={card.title} title={card.title} value={loading ? '...' : card.value} icon={card.icon} color={card.color} bg={card.bg} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Registration Velocity Chart (Panel 4) */}
        <div className="lg:col-span-2 bg-gray-800/50 border border-gray-700 rounded-xl p-6 shadow-lg backdrop-blur-sm">
          <h2 className="text-lg font-semibold mb-6 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-400" />
            Registration Velocity (Live)
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={velocityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis dataKey="time" stroke="#9ca3af" axisLine={false} tickLine={false} />
                <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', borderRadius: '0.5rem' }}
                  itemStyle={{ color: '#60a5fa' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="signups" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#3b82f6', strokeWidth: 2, stroke: '#1e3a8a' }}
                  activeDot={{ r: 6, fill: '#60a5fa', strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live Threat Feed (Panel 1) */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 shadow-lg backdrop-blur-sm flex flex-col">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <ShieldAlert className="w-5 h-5 mr-2 text-red-400" />
            Live Threat Feed
          </h2>
          <div className="flex-1 overflow-y-auto pr-2 space-y-4">
            {alerts.map((alert) => (
              <div key={alert.id} className="bg-gray-900/50 border border-gray-700 p-4 rounded-lg animate-in fade-in slide-in-from-right-4 duration-500">
                <div className="flex justify-between items-start mb-1">
                  <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                    alert.severity === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                    alert.severity === 'medium' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                    'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                  }`}>
                    {alert.type}
                  </span>
                  <span className="text-xs text-gray-500">{alert.time}</span>
                </div>
                <p className="text-sm text-gray-300 mt-2">{alert.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trust Score Distribution (Panel 2) */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 shadow-lg backdrop-blur-sm">
          <h2 className="text-lg font-semibold mb-6">Trust Score Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trustScoreCards} layout="vertical" margin={{ top: 0, right: 30, left: 20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                <XAxis type="number" stroke="#9ca3af" axisLine={false} tickLine={false} />
                <YAxis dataKey="range" type="category" stroke="#9ca3af" axisLine={false} tickLine={false} />
                <RechartsTooltip 
                  cursor={{fill: '#374151', opacity: 0.4}}
                  contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', borderRadius: '0.5rem' }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {trustScoreCards.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || COLORS.Blocked} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* User Forensics Table (Panel 3) */}
        <div className="lg:col-span-2 bg-gray-800/50 border border-gray-700 rounded-xl p-6 shadow-lg backdrop-blur-sm overflow-hidden flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold">User Forensics</h2>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-500" />
              </div>
              <input
                type="text"
                className="bg-gray-900 border border-gray-700 text-sm rounded-lg pl-9 pr-3 py-1.5 focus:outline-none focus:border-blue-500 transition-colors"
                placeholder="Search users or IPs..."
              />
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-gray-400 uppercase bg-gray-900/50 border-y border-gray-700">
                <tr>
                  <th className="px-4 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">IP Address</th>
                  <th className="px-4 py-3 font-medium">Trust Score</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {users.map((user) => (
                  <tr key={user.user_id} className="hover:bg-gray-800/80 transition-colors group">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-200">{user.email}</div>
                      <div className="text-xs text-gray-500">{user.registered_at}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs">{user.last_ip || 'n/a'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-full bg-gray-700 rounded-full h-1.5 max-w-[4rem]">
                          <div 
                            className={`h-1.5 rounded-full ${
                              user.trust_score < 20 ? 'bg-red-500' :
                              user.trust_score < 40 ? 'bg-orange-500' :
                              user.trust_score < 70 ? 'bg-yellow-500' : 'bg-green-500'
                            }`} 
                            style={{ width: `${user.trust_score}%` }}
                          ></div>
                        </div>
                        <span className="text-xs font-bold text-gray-300">{user.trust_score}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-1 rounded-md border ${
                        user.status === 'blocked' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                        user.status === 'quarantined' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                        'bg-green-500/10 text-green-400 border-green-500/20'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelectedUser(user)}
                        className="text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 p-1.5 rounded-md transition-colors border border-gray-700"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {selectedUser && (
        <UserTimeline
          userId={selectedUser.user_id}
          userEmail={selectedUser.email}
          onClose={() => setSelectedUser(null)}
        />
      )}
    </div>
  );
}

function KPICard({ title, value, icon: Icon, color, bg, trend }) {
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 shadow-lg backdrop-blur-sm hover:border-gray-600 transition-colors">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-gray-400 mb-1">{title}</p>
          <h3 className="text-3xl font-bold text-white">{value}</h3>
          {trend && (
            <p className="text-xs font-medium text-red-400 mt-2 flex items-center">
              <Activity className="w-3 h-3 mr-1" />
              {trend} vs last hour
            </p>
          )}
        </div>
        <div className={`${bg} p-3 rounded-lg border border-gray-700/50`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );
}
