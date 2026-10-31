import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { AuditLogEntry } from '../../types';

export const AuditTrail: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await api.audit.list({
        search,
        action: actionFilter,
      });
      setLogs(res.results || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadAuditLogs();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, actionFilter]);

  const getActionBadgeClass = (action: string) => {
    if (action.includes('FAIL') || action.includes('BLOCKED') || action.includes('DEACTIVATED')) {
      return 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300';
    }
    if (action.includes('SUCCESS') || action.includes('ACTIVATED') || action.includes('CREATED')) {
      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300';
    }
    return 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Immutable Security & Audit Trail
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            PostgreSQL trigger-enforced append-only log of all authentication events, staff modifications, and customer CRM updates.
          </p>
        </div>
        <button
          onClick={loadAuditLogs}
          className="inline-flex items-center px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold rounded-lg"
        >
          ↻ Refresh Logs
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 text-sm">
          {error}
        </div>
      )}

      {/* Filter bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
        <div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by actor email, entity ID..."
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
          />
        </div>
        <div>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
          >
            <option value="">All Audit Actions</option>
            <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
            <option value="LOGIN_FAILED">LOGIN_FAILED</option>
            <option value="STAFF_CREATED">STAFF_CREATED</option>
            <option value="STAFF_DEACTIVATED">STAFF_DEACTIVATED</option>
            <option value="CUSTOMER_CREATED">CUSTOMER_CREATED</option>
            <option value="CUSTOMER_ARCHIVED">CUSTOMER_ARCHIVED</option>
            <option value="CUSTOMER_PORTAL_LINKED">CUSTOMER_PORTAL_LINKED</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading audit history...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 bg-slate-50 dark:bg-slate-900 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
          <p className="text-slate-500">No audit logs matching query.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-3 font-semibold">Timestamp (UTC)</th>
                  <th className="px-6 py-3 font-semibold">Action</th>
                  <th className="px-6 py-3 font-semibold">Actor Email</th>
                  <th className="px-6 py-3 font-semibold">Entity</th>
                  <th className="px-6 py-3 font-semibold">Client IP</th>
                  <th className="px-6 py-3 font-semibold text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-xs">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-6 py-3 text-slate-500">
                      {new Date(log.timestamp).toISOString().replace('T', ' ').slice(0, 19)}
                    </td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${getActionBadgeClass(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-3 font-sans text-slate-800 dark:text-slate-200">
                      {log.actor_email || 'System / Unauth'}
                    </td>
                    <td className="px-6 py-3">
                      {log.entity_type} {log.entity_id ? `(${log.entity_id.slice(0, 8)}...)` : ''}
                    </td>
                    <td className="px-6 py-3 text-slate-500">{log.ip_address || '—'}</td>
                    <td className="px-6 py-3 text-right">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 font-sans text-[11px] font-semibold"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail inspect modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 text-slate-900 dark:text-slate-100">
            <div className="flex justify-between items-center mb-4 border-b border-slate-200 dark:border-slate-800 pb-2">
              <h3 className="text-base font-bold">Audit Event Details</h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2 text-xs font-mono">
              <div>
                <span className="font-bold text-slate-500 font-sans">Action:</span> {selectedLog.action}
              </div>
              <div>
                <span className="font-bold text-slate-500 font-sans">Timestamp:</span> {selectedLog.timestamp}
              </div>
              <div>
                <span className="font-bold text-slate-500 font-sans">Actor:</span> {selectedLog.actor_email || 'None'}
              </div>
              <div>
                <span className="font-bold text-slate-500 font-sans">Entity Target:</span> {selectedLog.entity_type} ({selectedLog.entity_id})
              </div>
              <div className="pt-2">
                <div className="font-bold text-slate-500 font-sans mb-1">Payload / Diff:</div>
                <pre className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg overflow-x-auto text-[11px]">
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-slate-200 dark:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

