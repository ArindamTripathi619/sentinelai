import React, { useEffect, useState } from 'react';
import {
  X,
  Loader,
  AlertCircle,
  Clock,
  MapPin,
  Zap,
  History,
  BadgeAlert,
  ArrowLeft,
  Filter,
  Download,
  ChevronRight,
  CalendarRange,
  SlidersHorizontal,
} from 'lucide-react';
import { api } from '../lib/api';

const ACTION_FILTERS = [
  { value: 'all', label: 'All actions' },
  { value: 'register', label: 'Register' },
  { value: 'login', label: 'Login' },
  { value: 'otp_sent', label: 'OTP sent' },
  { value: 'otp_verified', label: 'OTP verified' },
  { value: 'flagged', label: 'Flagged' },
  { value: 'quarantined', label: 'Quarantined' },
];

const SCORE_FILTERS = [
  { value: 'all', label: 'All trust bands' },
  { value: 'high', label: 'High risk (<20)' },
  { value: 'medium', label: 'Medium risk (20-39)' },
  { value: 'low', label: 'Low risk (40-69)' },
  { value: 'safe', label: 'Safe (70+)' },
];

const WINDOW_FILTERS = [
  { value: 'all', label: 'All time' },
  { value: '24h', label: 'Last 24 hours' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
];

export default function UserTimeline({ userId, userEmail, onClose, mode = 'modal' }) {
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [resolvedUserEmail, setResolvedUserEmail] = useState(userEmail || '');
  const [actionFilter, setActionFilter] = useState('all');
  const [scoreFilter, setScoreFilter] = useState('all');
  const [windowFilter, setWindowFilter] = useState('all');

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await api.get(`/users/${userId}/timeline`);
        setResolvedUserEmail(response.data.user_email || userEmail || '');
        setTimeline(response.data.timeline || response.data.events || []);
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load timeline');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchTimeline();
    }
  }, [userId, userEmail]);

  const isPageMode = mode === 'page';
  const filteredTimeline = timeline.filter((event) => {
    const action = (event.action_type || event.action || '').toLowerCase();
    const trustScore = Number(event.trust_score ?? event.trust_score_at_time ?? 0);
    const eventTimestamp = event.timestamp ? new Date(event.timestamp).getTime() : 0;

    if (actionFilter !== 'all' && action !== actionFilter) {
      return false;
    }

    if (scoreFilter !== 'all') {
      const band = getTrustBand(trustScore);
      if (band !== scoreFilter) {
        return false;
      }
    }

    if (windowFilter !== 'all' && eventTimestamp) {
      const now = Date.now();
      const cutoffMs =
        windowFilter === '24h'
          ? 24 * 60 * 60 * 1000
          : windowFilter === '7d'
            ? 7 * 24 * 60 * 60 * 1000
            : 30 * 24 * 60 * 60 * 1000;
      if (now - eventTimestamp > cutoffMs) {
        return false;
      }
    }

    return true;
  });

  const getActionBadgeColor = (action) => {
    switch (action?.toLowerCase()) {
      case 'register':
      case 'registration':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'login':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'otp_sent':
      case 'otp verified':
      case 'otp_verified':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'event_signup':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'flagged':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'quarantined':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getTrustScoreColor = (score) => {
    if (score < 20) return 'text-red-400';
    if (score < 40) return 'text-orange-400';
    if (score < 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getTrustBand = (score) => {
    if (score < 20) return 'high';
    if (score < 40) return 'medium';
    if (score < 70) return 'low';
    return 'safe';
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

    const csv = [headers, ...rows]
      .map((row) => row.map(escapeCsv).join(','))
      .join('\n');

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

  const containerClassName = isPageMode
    ? 'min-h-screen bg-gray-900 text-white p-6'
    : 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4';
  const panelClassName = isPageMode
    ? 'mx-auto w-full max-w-6xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden'
    : 'bg-gray-900 border border-gray-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col';

  return (
    <div className={containerClassName}>
      <div className={panelClassName}>
        <div className="flex justify-between items-start gap-4 border-b border-gray-700 p-6">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-gray-400 mb-3 text-xs uppercase tracking-[0.2em]">
              <History className="w-4 h-4" />
              <span>Forensic Replay</span>
            </div>

            {isPageMode && (
              <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-gray-400">
                <button
                  onClick={onClose}
                  className="inline-flex items-center gap-1.5 text-blue-300 hover:text-blue-200 transition-colors"
                >
                  Dashboard
                </button>
                <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
                <span className="text-gray-500">User timeline</span>
              </div>
            )}

            <h2 className="text-xl font-bold text-white">Activity Timeline</h2>
            <p className="text-sm text-gray-400 mt-1">{resolvedUserEmail || userEmail || 'Unknown user'}</p>

            {isPageMode && (
              <button
                onClick={onClose}
                className="mt-4 inline-flex items-center gap-2 text-sm text-blue-300 hover:text-blue-200 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to dashboard
              </button>
            )}
          </div>
          <button
            onClick={onClose}
            className={`transition-colors ${isPageMode ? 'text-gray-500 hover:text-white' : 'text-gray-400 hover:text-white'}`}
          >
            {isPageMode ? <X className="w-5 h-5" /> : <X className="w-6 h-6" />}
          </button>
        </div>

        {isPageMode && (
          <div className="border-b border-gray-700 bg-gray-800/40 p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-gray-300">
                <Filter className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium">Timeline filters</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span>{filteredTimeline.length} of {timeline.length} events shown</span>
                <button
                  onClick={handleExportCsv}
                  disabled={filteredTimeline.length === 0}
                  className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1.5 text-blue-300 transition-colors hover:bg-blue-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export CSV
                </button>
              </div>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <label className="space-y-2">
                <span className="flex items-center gap-2 text-xs uppercase tracking-wider text-gray-500">
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                  Action type
                </span>
                <select
                  value={actionFilter}
                  onChange={(event) => setActionFilter(event.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white outline-none transition-colors focus:border-blue-500"
                >
                  {ACTION_FILTERS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="space-y-2">
                <span className="flex items-center gap-2 text-xs uppercase tracking-wider text-gray-500">
                  <CalendarRange className="w-3.5 h-3.5" />
                  Time window
                </span>
                <select
                  value={windowFilter}
                  onChange={(event) => setWindowFilter(event.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white outline-none transition-colors focus:border-blue-500"
                >
                  {WINDOW_FILTERS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="space-y-2">
                <span className="flex items-center gap-2 text-xs uppercase tracking-wider text-gray-500">
                  <Filter className="w-3.5 h-3.5" />
                  Trust band
                </span>
                <select
                  value={scoreFilter}
                  onChange={(event) => setScoreFilter(event.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white outline-none transition-colors focus:border-blue-500"
                >
                  {SCORE_FILTERS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={resetFilters}
                className="text-xs text-gray-400 hover:text-white transition-colors"
              >
                Reset filters
              </button>
            </div>
          </div>
        )}

        <div className={isPageMode ? 'p-6' : 'flex-1 overflow-y-auto p-6'}>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
          ) : error ? (
            <div className="flex items-center space-x-3 bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : filteredTimeline.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No activity matches the current filters</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTimeline.map((event, index) => (
                <div
                  key={`${event.timestamp}-${index}`}
                  className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span
                          className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded border ${getActionBadgeColor(
                            event.action_type || event.action
                          )}`}
                        >
                          {formatActionLabel(event.action_type || event.action)}
                        </span>
                        {(event.trust_score !== undefined || event.trust_score_at_time !== undefined) && (
                          <span className={`text-xs font-bold ${getTrustScoreColor(event.trust_score ?? event.trust_score_at_time)}`}>
                            Trust: {event.trust_score ?? event.trust_score_at_time}
                          </span>
                        )}
                        {event.country && (
                          <span className="text-xs font-medium px-2 py-1 rounded border border-gray-600 text-gray-300">
                            {event.country}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-300 mb-3">
                        {event.description || 'Event occurred'}
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-gray-400">
                        <div className="flex items-center space-x-2">
                          <Clock className="w-4 h-4 flex-shrink-0 text-gray-500" />
                          <span>{new Date(event.timestamp).toLocaleString()}</span>
                        </div>
                        {event.ip_address && (
                          <div className="flex items-center space-x-2">
                            <MapPin className="w-4 h-4 flex-shrink-0 text-gray-500" />
                            <span className="font-mono">{event.ip_address}</span>
                          </div>
                        )}
                        {event.user_agent && (
                          <div className="flex items-center space-x-2 md:col-span-2">
                            <Zap className="w-4 h-4 flex-shrink-0 text-gray-500" />
                            <span className="truncate text-gray-500">
                              {event.user_agent}
                            </span>
                          </div>
                        )}
                        {event.metadata && Object.keys(event.metadata).length > 0 && (
                          <div className="md:col-span-2 bg-gray-900/70 border border-gray-700 rounded-md p-3 text-gray-300">
                            <div className="flex items-center gap-2 mb-2 text-gray-400">
                              <BadgeAlert className="w-4 h-4" />
                              <span className="text-[11px] uppercase tracking-wider">Metadata</span>
                            </div>
                            <pre className="whitespace-pre-wrap break-words text-[11px] leading-5 text-gray-400">
                              {JSON.stringify(event.metadata, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
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
  if (!action) {
    return 'Unknown';
  }

  return action
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
