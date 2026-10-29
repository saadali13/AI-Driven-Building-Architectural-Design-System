import React, { useState } from 'react';
import { 
  Bell, 
  CheckCircle2, 
  Sparkles, 
  DollarSign, 
  Layers, 
  ShieldCheck, 
  Users, 
  Trash2, 
  Check, 
  Eye, 
  Clock,
  Filter
} from 'lucide-react';

import { MessageSquare } from 'lucide-react';
import { getStoredAdminNotifications, updateAdminNotificationStatus } from '../../utils/feedbackStore';

const INITIAL_NOTIFICATIONS = [
  {
    id: 'notif_1',
    title: '5 Marla Elevation Synthesized',
    desc: 'ISB-C5 double story modern elevation model was successfully processed with 98.4% vector confidence.',
    time: '10 minutes ago',
    type: 'synthesis',
    status: 'pending',
    unread: true,
    icon: Sparkles,
    color: 'text-blue-600 bg-blue-50 border-blue-200'
  },
  {
    id: 'notif_2',
    title: 'PKR Material Price Matrix Updated',
    desc: 'Islamabad regional cement and steel rates have been synchronized with local market vendors.',
    time: '2 hours ago',
    type: 'cost',
    status: 'pending',
    unread: true,
    icon: DollarSign,
    color: 'text-emerald-600 bg-emerald-50 border-emerald-200'
  },
  {
    id: 'notif_3',
    title: 'ChromaDB Vector Index Re-synced',
    desc: '1,450 floor plans from THEODOROS/Architext_v1 dataset successfully embedded into 384-dim vector space.',
    time: 'Yesterday',
    type: 'system',
    status: 'received',
    unread: false,
    icon: ShieldCheck,
    color: 'text-purple-600 bg-purple-50 border-purple-200'
  },
  {
    id: 'notif_4',
    title: 'New Team Member Joined',
    desc: 'Lead Architect joined the Capital Villa Master Plan project as an active collaborator.',
    time: '2 days ago',
    type: 'team',
    status: 'received',
    unread: false,
    icon: Users,
    color: 'text-indigo-600 bg-indigo-50 border-indigo-200'
  }
];

export default function NotificationsModule({ onOpenStudio }) {
  const [notifications, setNotifications] = useState(() => {
    const adminNotifs = getStoredAdminNotifications().map(item => ({
      id: item.id,
      title: item.title,
      desc: item.message,
      time: item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'Just now',
      type: 'feedback',
      status: item.status || (item.read ? 'received' : 'pending'),
      unread: !item.read,
      icon: MessageSquare,
      color: 'text-purple-600 bg-purple-50 border-purple-200'
    }));
    return [...adminNotifs, ...INITIAL_NOTIFICATIONS];
  });
  const [filterType, setFilterType] = useState('ALL');
  const [toastMsg, setToastMsg] = useState('');

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3500);
  };

  const handleNotificationClick = async (notifId) => {
    try {
      const token = localStorage.getItem('jwt_token') || localStorage.getItem('archai_token');
      if (token) {
        await fetch(`/api/admin/notifications/${notifId}/status`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ status: 'received' })
        }).catch(() => {});
      }
    } catch (e) {
      console.warn('API status mutation error', e);
    }

    updateAdminNotificationStatus(notifId, 'received');
    setNotifications(prev => prev.map(n => {
      if (n.id === notifId) {
        return { ...n, status: 'received', unread: false };
      }
      return n;
    }));
    showToast('Notification status updated to Received.');
  };


  const handleMarkAllRead = () => {
    setNotifications(notifications.map(n => ({ ...n, unread: false })));
    showToast('All notifications marked as read.');
  };

  const handleClearAll = () => {
    setNotifications([]);
    showToast('Notification center cleared.');
  };

  const filteredNotifications = notifications.filter(n => {
    if (filterType === 'ALL') return true;
    if (filterType === 'UNREAD') return n.unread;
    return n.type === filterType;
  });

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 text-slate-900 font-sans">
      
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2.5 px-5 py-3.5 bg-slate-900 text-white rounded-2xl shadow-2xl text-sm font-semibold animate-in fade-in">
          <Check className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-100 text-blue-600">
              <Bell className="w-6 h-6" />
            </div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Notification Center</h1>
            <span className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 font-mono text-xs font-bold border border-blue-200">
              {notifications.filter(n => n.unread).length} Unread
            </span>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed max-w-xl">
            Real-time synthesis logs, PKR price matrix updates, and team collaboration alerts.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={handleMarkAllRead}
            className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition cursor-pointer"
          >
            Mark all read
          </button>
          <button
            type="button"
            onClick={handleClearAll}
            className="p-2.5 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-xl transition cursor-pointer border border-rose-200"
            title="Clear all notifications"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto bg-white p-2 rounded-2xl border border-slate-200 shadow-xs">
        {[
          { id: 'ALL', label: 'All Alerts' },
          { id: 'UNREAD', label: 'Unread' },
          { id: 'synthesis', label: 'Design Synthesis' },
          { id: 'cost', label: 'PKR Cost Matrix' },
          { id: 'system', label: 'System Telemetry' },
          { id: 'team', label: 'Team Activity' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setFilterType(tab.id)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
              filterType === tab.id
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div className="space-y-4">
        {filteredNotifications.length === 0 ? (
          <div className="p-12 bg-white border border-slate-200 rounded-3xl text-center space-y-3 shadow-xs">
            <Bell className="w-8 h-8 text-slate-300 mx-auto" />
            <h3 className="text-base font-bold text-slate-900">No Notifications</h3>
            <p className="text-xs text-slate-500">All alerts have been reviewed and acknowledged.</p>
          </div>
        ) : (
          filteredNotifications.map((notif) => {
            const Icon = notif.icon;
            return (
              <div
                key={notif.id}
                onClick={() => handleNotificationClick(notif.id)}
                className={`p-6 bg-white border rounded-3xl transition flex flex-col sm:flex-row items-start justify-between gap-4 shadow-xs cursor-pointer hover:border-blue-300 ${
                  notif.unread ? 'border-blue-200 bg-blue-50/20' : 'border-slate-200'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-2xl border flex items-center justify-center shrink-0 ${notif.color}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h4 className="font-bold text-sm text-slate-900">{notif.title}</h4>
                      
                      {/* Dynamic Status Badge Reflection (Pending -> Received) */}
                      {notif.status === 'received' || !notif.unread ? (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          Received
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                          <Clock className="w-3 h-3 text-amber-600" />
                          Pending
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-slate-600 mt-1 leading-relaxed">{notif.desc}</p>
                    <span className="text-xs text-slate-400 font-mono mt-2 block flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{notif.time}</span>
                    </span>
                  </div>
                </div>

                {notif.type === 'synthesis' && (
                  <button
                    type="button"
                    onClick={() => onOpenStudio && onOpenStudio('5marla')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow-xs flex items-center gap-1.5 cursor-pointer shrink-0 self-end sm:self-center"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Inspect 3D Scene</span>
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
