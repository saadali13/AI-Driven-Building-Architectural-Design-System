import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Menu,
  Bell,
  Search,
  ChevronRight,
  X,
  Compass,
  CheckCircle2,
  Sparkles,
  Activity,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useProjects } from '../../context/ProjectContext';
import { apiService } from '../../services/apiService';

interface DashboardHeaderProps {
  onMobileMenuToggle: () => void;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ onMobileMenuToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const { notifications, markNotificationRead, markAllNotificationsRead } = useProjects();

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    // Check real backend status
    apiService.getStatus().then((status) => {
      setIsBackendOnline(!!status);
    }).catch(() => {
      setIsBackendOnline(false);
    });
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getBreadcrumbs = () => {
    const parts = location.pathname.split('/').filter(Boolean);
    return parts;
  };

  const pathParts = getBreadcrumbs();

  const formatBreadcrumb = (part: string) => {
    if (part === 'app') return 'Studio';
    if (part === 'designs') return 'My Designs';
    if (part === 'new') return 'New Design';
    if (part === 'cost-estimation') return 'Cost Estimation';
    if (part === 'compare') return 'Compare';
    if (part === 'templates') return 'Templates';
    if (part === 'favorites') return 'Favorites';
    if (part === 'help-support') return 'Support';
    if (part === 'cost-settings') return 'Material Rates';
    return part.charAt(0).toUpperCase() + part.slice(1);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setSearchModalOpen(false);
      navigate(`/app/designs?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <>
      <header className="h-16 bg-white border-b border-[#E2E7E1] px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-30 shadow-xs">
        {/* Left: Mobile hamburger & breadcrumbs */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMobileMenuToggle}
            className="p-2 rounded-xl text-[#68736C] hover:text-[#202923] hover:bg-[#F1F4F0] lg:hidden transition-colors"
            title="Open Menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          <nav className="hidden sm:flex items-center gap-1.5 text-xs text-[#68736C]">
            <Link to="/app/dashboard" className="hover:text-[#202923] transition-colors flex items-center gap-1">
              <Compass className="h-3.5 w-3.5 text-[#23483D]" />
              <span>Studio</span>
            </Link>

            {pathParts.map((part, index) => {
              if (part === 'app') return null;
              const url = `/${pathParts.slice(0, index + 1).join('/')}`;
              const isLast = index === pathParts.length - 1;

              return (
                <React.Fragment key={url}>
                  <ChevronRight className="h-3.5 w-3.5 text-[#D0D8CF]" />
                  {isLast ? (
                    <span className="text-[#202923] font-semibold">{formatBreadcrumb(part)}</span>
                  ) : (
                    <Link to={url} className="hover:text-[#202923] transition-colors">
                      {formatBreadcrumb(part)}
                    </Link>
                  )}
                </React.Fragment>
              );
            })}
          </nav>
        </div>

        {/* Right: Engine Status, Search, Notifications, Profile */}
        <div className="flex items-center gap-3">
          {/* Live Engine Status Badge */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#F1F4F0] border border-[#E2E7E1] text-[#202923]">
            <span
              className={`h-2 w-2 rounded-full ${
                isBackendOnline ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span className="text-[#68736C]">
              {isBackendOnline ? 'ArchAI Engine Online' : 'Local Sandbox Mode'}
            </span>
          </div>

          {/* Global Search Trigger */}
          <button
            onClick={() => setSearchModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#F7F7F2] hover:bg-[#F1F4F0] border border-[#E2E7E1] text-xs text-[#68736C] hover:text-[#202923] transition-colors"
          >
            <Search className="h-3.5 w-3.5 text-[#68736C]" />
            <span className="hidden md:inline">Search plots, designs...</span>
            <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-white border border-[#E2E7E1] rounded text-[#68736C]">
              Ctrl+K
            </kbd>
          </button>

          {/* Notifications Dropdown */}
          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative p-2 rounded-xl text-[#68736C] hover:text-[#202923] hover:bg-[#F1F4F0] transition-colors"
              title="Notifications"
            >
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[#B86F50] ring-2 ring-white" />
              )}
            </button>

            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-white border border-[#E2E7E1] shadow-xl z-50 overflow-hidden">
                <div className="p-3.5 bg-[#F7F7F2] border-b border-[#E2E7E1] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-[#202923]">Notifications</span>
                    {unreadCount > 0 && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#DCE7DE] text-[#23483D] font-bold">
                        {unreadCount} unread
                      </span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllNotificationsRead}
                      className="text-[11px] text-[#23483D] hover:underline transition-colors font-medium"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                <div className="max-h-80 overflow-y-auto divide-y divide-[#E2E7E1]">
                  {notifications.length === 0 ? (
                    <div className="p-6 text-center text-xs text-[#68736C]">No notifications yet.</div>
                  ) : (
                    notifications.map((notif) => (
                      <div
                        key={notif.id}
                        onClick={() => {
                          markNotificationRead(notif.id);
                          if (notif.link) {
                            setNotificationsOpen(false);
                            navigate(notif.link);
                          }
                        }}
                        className={`p-3.5 text-xs cursor-pointer hover:bg-[#F7F7F2] transition-colors ${
                          notif.read ? 'opacity-70' : 'bg-[#F4F6F3]'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="font-semibold text-[#202923]">{notif.title}</p>
                          <span className="text-[10px] text-[#68736C] shrink-0">{notif.timestamp}</span>
                        </div>
                        <p className="text-[#68736C] mt-1 line-clamp-2">{notif.message}</p>
                      </div>
                    ))
                  )}
                </div>

                <div className="p-2.5 bg-[#F7F7F2] border-t border-[#E2E7E1] text-center">
                  <Link
                    to="/app/notifications"
                    onClick={() => setNotificationsOpen(false)}
                    className="text-xs font-semibold text-[#23483D] hover:underline"
                  >
                    View All Notifications
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Profile Shortcut */}
          <Link
            to="/app/profile"
            className="flex items-center gap-2 pl-2 border-l border-[#E2E7E1] hover:opacity-90 transition-opacity"
            title="Profile & Settings"
          >
            <div className="h-8 w-8 rounded-full bg-[#23483D] flex items-center justify-center text-xs font-bold text-white shadow-xs">
              {currentUser?.name?.charAt(0) || 'U'}
            </div>
            <div className="hidden xl:block text-left">
              <p className="text-xs font-semibold text-[#202923] leading-tight">{currentUser?.name}</p>
              <p className="text-[10px] text-[#68736C] capitalize">{currentUser?.role}</p>
            </div>
          </Link>
        </div>
      </header>

      {/* Global Search Modal */}
      {searchModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#202923]/40 backdrop-blur-sm flex items-start justify-center pt-20 px-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden">
            <form onSubmit={handleSearchSubmit} className="p-4 border-b border-[#E2E7E1] flex items-center gap-3">
              <Search className="h-5 w-5 text-[#23483D] shrink-0" />
              <input
                type="text"
                autoFocus
                placeholder="Search projects, plot sizes (5 Marla, 10 Marla), bedrooms, or bylaws..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent text-sm text-[#202923] focus:outline-none placeholder:text-[#68736C]"
              />
              <button
                type="button"
                onClick={() => setSearchModalOpen(false)}
                className="p-1 rounded text-[#68736C] hover:text-[#202923]"
              >
                <X className="h-5 w-5" />
              </button>
            </form>

            <div className="p-4 text-xs space-y-3 bg-[#F7F7F2]">
              <p className="text-[#68736C] font-semibold uppercase tracking-wider text-[10px]">Quick Suggestions</p>
              <div className="flex flex-wrap gap-2">
                {['5 Marla Bahria Layout', '10 Marla DHA Villa', '1 Kanal Classical Estate', 'CDA Setback Bylaws', 'Cement Bag Rates'].map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => {
                      setSearchQuery(item);
                      setSearchModalOpen(false);
                      navigate(`/app/designs?q=${encodeURIComponent(item)}`);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-white border border-[#E2E7E1] hover:border-[#23483D] text-[#202923] hover:text-[#23483D] transition-colors"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
