import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell
} from 'recharts';
import { 
  ShieldAlert, Users, Activity, Lock, AlertTriangle, 
  ChevronRight, Search, Server, Shield
} from 'lucide-react';

// Mock Data
const velocityData = [
  { time: '10:00', signups: 12 },
  { time: '10:05', signups: 15 },
  { time: '10:10', signups: 18 },
  { time: '10:15', signups: 85 }, // Bot wave spike
  { time: '10:20', signups: 14 },
  { time: '10:25', signups: 11 },
  { time: '10:30', signups: 16 },
];

const trustScoreData = [
  { range: '0-20', count: 45, label: 'Blocked' },
  { range: '21-40', count: 80, label: 'Quarantine' },
  { range: '41-70', count: 250, label: 'Suspicious' },
  { range: '71-100', count: 1800, label: 'Safe' },
];

const COLORS = {
  Blocked: '#ef4444',     // Red
  Quarantine: '#f97316',  // Orange
  Suspicious: '#eab308',  // Yellow
  Safe: '#22c55e',        // Green
};

const mockAlerts = [
  { id: 1, type: 'Bot Wave', desc: '14 signups in 60s detected', severity: 'high', time: '2m ago' },
  { id: 2, type: 'Geo Drift', desc: 'user22@test.com: IN → DE', severity: 'medium', time: '15m ago' },
  { id: 3, type: 'Velocity', desc: 'IP 192.168.1.1 registered 5 accs', severity: 'high', time: '42m ago' },
  { id: 4, type: 'Behavioral', desc: 'Low mouse entropy score (0.04)', severity: 'low', time: '1h ago' },
];

const mockUsers = [
  { id: 'usr_001', email: 'john@example.com', ip: '203.0.113.1', score: 92, status: 'Safe', date: '2023-10-25 10:45' },
  { id: 'usr_002', email: 'bot_runner77@temp.com', ip: '45.22.11.9', score: 12, status: 'Blocked', date: '2023-10-25 10:15' },
  { id: 'usr_003', email: 'sarah.m@gmail.com', ip: '198.51.100.2', score: 68, status: 'Suspicious', date: '2023-10-25 09:22' },
  { id: 'usr_004', email: 'admin_test@corp.net', ip: '192.0.2.4', score: 35, status: 'Quarantine', date: '2023-10-25 08:11' },
];

export default function Dashboard() {
  const [alerts, setAlerts] = useState(mockAlerts);
  
  // Simulate live threat feed polling
  useEffect(() => {
    const interval = setInterval(() => {
      // Just a mock rotation to look "alive"
      setAlerts(prev => {
        const newAlert = { ...prev[3], id: Date.now(), time: 'Just now' };
        return [newAlert, ...prev.slice(0, 3)];
      });
    }, 8000);
    return () => clearInterval(interval);
  }, []);

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
        </div>
      </header>

      {/* KPI Row (Panel 5) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard title="Total Users" value="2,175" icon={Users} color="text-blue-400" bg="bg-blue-400/10" />
        <KPICard title="Flagged Today" value="125" icon={AlertTriangle} color="text-yellow-400" bg="bg-yellow-400/10" trend="+14%" />
        <KPICard title="Bot Waves Detected" value="3" icon={Activity} color="text-red-400" bg="bg-red-400/10" />
        <KPICard title="Quarantined" value="80" icon={Lock} color="text-orange-400" bg="bg-orange-400/10" />
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
              <BarChart data={trustScoreData} layout="vertical" margin={{ top: 0, right: 30, left: 20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                <XAxis type="number" stroke="#9ca3af" axisLine={false} tickLine={false} />
                <YAxis dataKey="range" type="category" stroke="#9ca3af" axisLine={false} tickLine={false} />
                <RechartsTooltip 
                  cursor={{fill: '#374151', opacity: 0.4}}
                  contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', borderRadius: '0.5rem' }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {trustScoreData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.label]} />
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
                {mockUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-800/80 transition-colors group">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-200">{user.email}</div>
                      <div className="text-xs text-gray-500">{user.date}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs">{user.ip}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-full bg-gray-700 rounded-full h-1.5 max-w-[4rem]">
                          <div 
                            className={`h-1.5 rounded-full ${
                              user.score < 20 ? 'bg-red-500' :
                              user.score < 40 ? 'bg-orange-500' :
                              user.score < 70 ? 'bg-yellow-500' : 'bg-green-500'
                            }`} 
                            style={{ width: `${user.score}%` }}
                          ></div>
                        </div>
                        <span className="text-xs font-bold text-gray-300">{user.score}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-1 rounded-md border ${
                        user.status === 'Blocked' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                        user.status === 'Quarantine' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                        user.status === 'Suspicious' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                        'bg-green-500/10 text-green-400 border-green-500/20'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button className="text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 p-1.5 rounded-md transition-colors border border-gray-700">
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
