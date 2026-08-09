import React, { useState, useEffect } from "react";
import api from "../services/api";
import type { AuditLog } from "../types";
import { History, ShieldAlert, Loader2 } from "lucide-react";

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Filters
  const [actionFilter, setActionFilter] = useState("");
  const [resourceFilter, setResourceFilter] = useState("");

  const fetchLogs = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      let query = "/audit/logs?limit=50";
      if (actionFilter) query += `&action=${actionFilter}`;
      if (resourceFilter) query += `&resource=${resourceFilter}`;

      const res = await api.get(query);
      if (res.data && res.data.data) {
        setLogs(res.data.data);
      }
    } catch (err: any) {
      console.error(err);
      setErrorMessage("Access Denied: Missing permissions to query system audit trail.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, resourceFilter]);

  if (isLoading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-white animate-spin" />
        <span className="text-xs text-slate-400">Retrieving system ledger...</span>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="glass-panel rounded-2xl p-8 max-w-xl mx-auto text-center space-y-4 animate-fade-in mt-12">
        <div className="flex justify-center text-rose-500">
          <ShieldAlert className="w-12 h-12" />
        </div>
        <h3 className="text-lg font-bold text-white uppercase tracking-wider">Access Denied</h3>
        <p className="text-sm text-slate-400">{errorMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-xl font-bold tracking-tight text-white font-sans flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" /> Audit Log Ledger
          </h1>
          <p className="text-xs text-slate-400">Cryptographically verifiable immutable audit records.</p>
        </div>

        {/* Filter controls */}
        <div className="flex gap-2">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="bg-slate-900 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-white/30"
          >
            <option value="">All Actions</option>
            <option value="login">Login</option>
            <option value="register">Register</option>
            <option value="deactivate">Deactivate</option>
            <option value="activate">Activate</option>
          </select>

          <select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            className="bg-slate-900 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-white/30"
          >
            <option value="">All Resources</option>
            <option value="users">Users</option>
            <option value="roles">Roles</option>
            <option value="papers">Papers</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel rounded-2xl overflow-hidden shadow-xl border border-white/5">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.02] text-xs font-bold text-slate-400 uppercase tracking-widest">
                <th className="p-4 pl-6">Timestamp (UTC)</th>
                <th className="p-4">Action</th>
                <th className="p-4">Resource</th>
                <th className="p-4">Client IP</th>
                <th className="p-4">Execution Time</th>
                <th className="p-4 pr-6 text-right">HTTP Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm text-slate-200 font-mono">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-white/[0.01] transition-colors">
                  <td className="p-4 pl-6 text-xs text-slate-400">
                    {new Date(log.created_at).toISOString().replace("T", " ").substring(0, 19)}
                  </td>
                  <td className="p-4 font-bold text-white uppercase text-xs">{log.action}</td>
                  <td className="p-4 text-xs">{log.resource}</td>
                  <td className="p-4 text-xs text-slate-400">{log.ip_address || "127.0.0.1"}</td>
                  <td className="p-4 text-xs text-slate-400">
                    {log.execution_time_ms ? `${log.execution_time_ms.toFixed(1)} ms` : "N/A"}
                  </td>
                  <td className="p-4 pr-6 text-right">
                    <span
                      className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        (log.status_code || 200) < 400
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/15"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/15"
                      }`}
                    >
                      {log.status_code || 200}
                    </span>
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-xs text-slate-500 italic">
                    No matching audit records found in secure ledger
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default AuditPage;
