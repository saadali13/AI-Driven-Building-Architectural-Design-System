import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bell,
  CheckCircle2,
  AlertCircle,
  FileSearch,
  Calculator,
  Compass,
  ArrowRight,
  Filter,
  CheckCheck
} from 'lucide-react';
import { useProjects } from '../../context/ProjectContext';

export const NotificationsPage: React.FC = () => {
  const { notifications, markNotificationRead, markAllNotificationsRead } = useProjects();
  const [filterType, setFilterType] = useState<string>('all');

  const filtered = notifications.filter((n) => {
    if (filterType !== 'all' && n.type !== filterType) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7E1] pb-5">
        <div>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">Notifications Center</h1>
          <p className="text-xs text-[#68736C] mt-1">
            System updates, AI spatial layout generations, and PCATP architect review alerts.
          </p>
        </div>

        <button
          onClick={markAllNotificationsRead}
          className="px-3.5 py-1.5 rounded-xl border border-[#E2E7E1] bg-white hover:bg-[#F7F7F2] text-[#202923] text-xs font-semibold flex items-center gap-1.5 self-start sm:self-auto transition-colors shadow-xs"
        >
          <CheckCheck className="h-3.5 w-3.5 text-[#23483D]" />
          <span>Mark All as Read</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {[
          { id: 'all', label: 'All Notifications' },
          { id: 'review', label: 'Architect Reviews' },
          { id: 'generation', label: 'AI Spatial Synthesis' },
          { id: 'estimate', label: 'BOQ Estimates' },
          { id: 'system', label: 'System & Engine' },
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setFilterType(f.id)}
            className={`px-3 py-1.5 rounded-xl font-semibold transition-colors shrink-0 ${
              filterType === f.id
                ? 'bg-[#23483D] text-white shadow-xs'
                : 'bg-white border border-[#E2E7E1] text-[#68736C] hover:text-[#202923]'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Notification Cards */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="bg-white border border-[#E2E7E1] rounded-2xl p-10 text-center text-xs text-[#68736C] shadow-xs">
            <Bell className="h-8 w-8 text-[#68736C]/40 mx-auto mb-2" />
            <p className="font-semibold text-[#202923]">No notifications found</p>
            <p className="mt-1">You are all caught up with your architectural project alerts.</p>
          </div>
        ) : (
          filtered.map((n) => (
            <div
              key={n.id}
              onClick={() => markNotificationRead(n.id)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-start gap-4 shadow-xs ${
                n.read
                  ? 'bg-white border-[#E2E7E1] opacity-75'
                  : 'bg-white border-[#23483D]/40 ring-1 ring-[#23483D]/20'
              }`}
            >
              <div
                className={`h-9 w-9 rounded-xl flex items-center justify-center shrink-0 ${
                  n.type === 'review'
                    ? 'bg-[#DCE7DE] text-[#23483D]'
                    : n.type === 'estimate'
                    ? 'bg-amber-50 text-amber-700'
                    : 'bg-[#F7F7F2] text-[#202923]'
                }`}
              >
                {n.type === 'review' ? (
                  <FileSearch className="h-4 w-4" />
                ) : n.type === 'estimate' ? (
                  <Calculator className="h-4 w-4" />
                ) : (
                  <Bell className="h-4 w-4" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-bold text-xs text-[#202923] flex items-center gap-2">
                    {n.title}
                    {!n.read && (
                      <span className="h-2 w-2 rounded-full bg-[#23483D] inline-block shrink-0" />
                    )}
                  </h4>
                  <span className="text-[10px] text-[#68736C] shrink-0 font-mono">{n.timestamp}</span>
                </div>
                <p className="text-xs text-[#68736C] mt-1 leading-relaxed">{n.message}</p>
                {n.link && (
                  <Link
                    to={n.link}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#23483D] hover:underline mt-2"
                  >
                    <span>View Details</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
