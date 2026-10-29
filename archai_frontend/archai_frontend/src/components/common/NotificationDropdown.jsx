import React, { useState } from 'react';
import { 
  Bell, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldCheck, 
  Calculator, 
  Sparkles, 
  Clock, 
  Trash2, 
  Check, 
  ArrowRight,
  X
} from 'lucide-react';

const INITIAL_NOTIFICATIONS = [
  {
    id: 'notif_1',
    title: 'CDA Islamabad Setback Verified',
    desc: '5 Marla Villa design satisfies the mandatory 5ft front and 3ft rear setback requirement with 100% compliance score.',
    category: 'bylaws',
    unread: true,
    time: '12m ago',
    icon: ShieldCheck,
    color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200'
  },
  {
    id: 'notif_2',
    title: 'Steel 60-Grade Price Updated',
    desc: 'Amreli & Mughal steel rebar rates updated to ₨ 264/kg. BOQ estimate recalculated automatically.',
    category: 'cost',
    unread: true,
    time: '1h ago',
    icon: Calculator,
    color: 'text-amber-600 bg-amber-50 dark:bg-amber-950/40 border-amber-200'
  },
  {
    id: 'notif_3',
    title: 'AI Floor Plan Synthesis Complete',
    desc: '10 Marla Spanish Villa 3D solid model and AIA-layered DXF ready for inspection in WebGL viewer.',
    category: 'design',
    unread: true,
    time: '3h ago',
    icon: Sparkles,
    color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/40 border-blue-200'
  },
  {
    id: 'notif_4',
    title: 'Security Audit & 2FA Active',
    desc: 'Your account session is secured with TOTP two-factor verification across browser instances.',
    category: 'system',
    unread: false,
    time: 'Yesterday',
    icon: CheckCircle2,
    color: 'text-slate-600 bg-slate-50 dark:bg-slate-800 border-slate-200'
  }
];

export default function NotificationDropdown({
  isOpen,
  onClose,
  onOpenNotificationsPage,
  onOpenStudio
}) {
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS);
  const [filter, setFilter] = useState('all');

  const unreadCount = notifications.filter(n => n.unread).length;

  const handleMarkAsRead = (id) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, unread: false } : n));
  };

  const handleMarkAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const filteredNotifs = filter === 'all' 
    ? notifications 
    : notifications.filter(n => n.category === filter);

  if (!isOpen) return null;

  return (
    <div 
      className="absolute right-0 mt-3 w-80 sm:w-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150"
      onClick={e => e.stopPropagation()}
    >
      {/* Header */}
      <div className="p-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/70 dark:bg-slate-950/50">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-blue-600" />
          <span className="font-bold text-slate-900 dark:text-white text-sm">Notifications</span>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-blue-600 text-white text-[10px] font-mono font-bold">
              {unreadCount} new
            </span>
          )}
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={handleMarkAllRead}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-semibold cursor-pointer"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 p-1.5 border-b border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs">
        {['all', 'design', 'bylaws', 'cost'].map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setFilter(cat)}
            className={`flex-1 py-1 px-2 rounded-lg font-medium capitalize transition cursor-pointer text-center text-[11px] ${
              filter === cat
                ? 'bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-bold'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/80">
        {filteredNotifs.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs">
            No notifications in this category
          </div>
        ) : (
          filteredNotifs.map((item) => {
            const Icon = item.icon;
            return (
              <div 
                key={item.id}
                onClick={() => handleMarkAsRead(item.id)}
                className={`p-3.5 transition flex items-start gap-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 ${
                  item.unread ? 'bg-blue-50/30 dark:bg-blue-950/20' : ''
                }`}
              >
                <div className={`w-8 h-8 rounded-xl border flex items-center justify-center shrink-0 ${item.color}`}>
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                      {item.title}
                    </h4>
                    <span className="text-[10px] text-slate-400 shrink-0 font-mono">{item.time}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2 leading-relaxed">
                    {item.desc}
                  </p>
                </div>

                {item.unread && (
                  <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0 mt-1.5" />
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
        <button
          type="button"
          onClick={() => {
            if (onClose) onClose();
            if (onOpenNotificationsPage) onOpenNotificationsPage();
          }}
          className="w-full py-1.5 text-center text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 font-bold flex items-center justify-center gap-1 cursor-pointer"
        >
          <span>Open Full Notification Center</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
