import React, { useState } from 'react';
import { History, Shield, Filter, Search, UserCheck } from 'lucide-react';
import { INITIAL_AUDIT_LOGS } from '../../data/mockData';
import { AuditLog } from '../../types';

export const AuditLogsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');

  const filtered = INITIAL_AUDIT_LOGS.filter((l: AuditLog) => {
    if (searchTerm && !l.target.toLowerCase().includes(searchTerm.toLowerCase()) && !l.userName.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (roleFilter !== 'all' && l.userRole !== roleFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">System Audit & Security Logs</h1>
          <p className="text-xs text-[#68736C] mt-1">
            Immutable log of architectural reviews, cost rate revisions, user role elevation, and exports.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-[#E2E7E1] shadow-xs">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#68736C]" />
          <input
            type="text"
            placeholder="Search log events or users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl pl-9 pr-3 py-1.5 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-1.5 text-xs text-[#202923]"
          >
            <option value="all">All Roles</option>
            <option value="admin">Administrator</option>
            <option value="architect">PCATP Architect</option>
            <option value="contractor">Contractor</option>
            <option value="customer">Homeowner</option>
          </select>
        </div>
      </div>

      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 text-xs shadow-xs space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="pb-3 font-medium">Timestamp</th>
                <th className="pb-3 font-medium">Actor</th>
                <th className="pb-3 font-medium">Role</th>
                <th className="pb-3 font-medium">Action Event</th>
                <th className="pb-3 font-medium">Target Entity</th>
                <th className="pb-3 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#68736C]">
              {filtered.map((log: AuditLog) => (
                <tr key={log.id} className="hover:bg-[#F7F7F2]/60 transition-colors">
                  <td className="py-3 font-mono text-[11px] text-[#202923]">{log.timestamp}</td>
                  <td className="py-3 font-semibold text-[#202923]">{log.userName}</td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#DCE7DE] text-[#23483D]">
                      {log.userRole}
                    </span>
                  </td>
                  <td className="py-3 font-mono text-[#23483D] font-medium">{log.action}</td>
                  <td className="py-3 text-[#202923]">{log.target}</td>
                  <td className="py-3 text-right">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        log.status === 'security_event'
                          ? 'bg-rose-100 text-rose-800'
                          : log.status === 'warning'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
