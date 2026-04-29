import React, { useState, useEffect } from 'react';
import { X, Loader, AlertCircle, Clock, MapPin, Zap, Shield, History, BadgeAlert, ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';

export default function UserTimeline({ userId, userEmail, onClose, mode = 'modal' }) {
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [resolvedUserEmail, setResolvedUserEmail] = useState(userEmail || '');

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
  }, [userId]);

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

  const isPageMode = mode === 'page';
  const Container = isPageMode ? 'div' : 'div';
  const containerClassName = isPageMode
    ? 'min-h-screen bg-gray-900 text-white p-6'
    : 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4';
  const panelClassName = isPageMode
    ? 'mx-auto w-full max-w-6xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden'
    : 'bg-gray-900 border border-gray-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col';

  return (
    <div className={containerClassName}>
      <div className={panelClassName}>
        {/* Header */}
        <div className="flex justify-between items-center border-b border-gray-700 p-6">
          <div>
            <div className="flex items-center gap-2 text-gray-400 mb-2">
              <History className="w-4 h-4" />
              <span className="text-xs uppercase tracking-[0.2em]">Forensic Replay</span>
            </div>
            <h2 className="text-xl font-bold text-white">Activity Timeline</h2>
            <p className="text-sm text-gray-400 mt-1">{resolvedUserEmail || userEmail || 'Unknown user'}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isPageMode ? <ArrowLeft className="w-6 h-6" /> : <X className="w-6 h-6" />}
          </button>
        </div>

        {/* Content */}
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
          ) : timeline.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No activity recorded yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {timeline.map((event, index) => (
                <div
                  key={`${event.timestamp}-${index}`}
                  className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
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
                          <span>
                            {new Date(event.timestamp).toLocaleString()}
                          </span>
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
