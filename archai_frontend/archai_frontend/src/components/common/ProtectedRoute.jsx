import React from 'react';
import { useAuth, ROLE_DETAILS, ROLES } from '../../context/AuthContext';


import { ShieldAlert, Lock, ArrowRight, ShieldCheck, UserX } from 'lucide-react';

export default function ProtectedRoute({ 
  children, 
  requiredRole, 
  allowedRoles = [], 
  requiredPermission,
  fallbackToAuth = true,
  onNavigateToAuth 
}) {
  const { user, isAuthenticated, loading, hasPermission } = useAuth();

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center bg-white text-slate-500 font-mono text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span>Verifying Session &amp; RBAC Clearance...</span>
        </div>
      </div>
    );
  }

  // 1. Unauthenticated barrier
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-[420px] flex flex-col items-center justify-center bg-white p-8 rounded-3xl border border-slate-200 shadow-sm text-center max-w-lg mx-auto my-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-xs">
          <Lock className="w-7 h-7" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">Authentication Required</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto leading-relaxed">
            You must be signed in with a verified session to access this architectural design feature.
          </p>
        </div>
        <button
          type="button"
          onClick={() => onNavigateToAuth ? onNavigateToAuth() : window.location.reload()}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow-md shadow-blue-500/20 flex items-center gap-2 cursor-pointer hover:scale-[1.01]"
        >
          <span>Sign In to Continue</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  // 2. Specific Role Check
  if (requiredRole && user.role !== requiredRole && user.role !== ROLES.SYSTEM_ADMIN) {
    const reqMeta = ROLE_DETAILS[requiredRole] || { title: requiredRole };
    const curMeta = ROLE_DETAILS[user.role] || { title: user.role, color: 'bg-slate-100 text-slate-700' };

    return (
      <div className="min-h-[380px] flex flex-col items-center justify-center bg-white p-8 rounded-3xl border border-slate-200 shadow-sm text-center max-w-lg mx-auto my-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 shadow-xs">
          <ShieldAlert className="w-7 h-7" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">RBAC Clearance Restricted</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto leading-relaxed">
            This module requires <strong className="text-slate-800">{reqMeta.title}</strong> clearance. Your current active role is <strong className="text-slate-800">{curMeta.title}</strong>.
          </p>
        </div>

        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs flex items-center justify-between w-full max-w-xs">
          <span className="text-slate-500 font-medium">Your Role:</span>
          <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${curMeta.color}`}>
            {curMeta.title}
          </span>
        </div>
      </div>
    );
  }

  // 3. Multi-role allowed list
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role) && user.role !== ROLES.SYSTEM_ADMIN) {
    const curMeta = ROLE_DETAILS[user.role] || { title: user.role, color: 'bg-slate-100 text-slate-700' };

    return (
      <div className="min-h-[380px] flex flex-col items-center justify-center bg-white p-8 rounded-3xl border border-slate-200 shadow-sm text-center max-w-lg mx-auto my-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 shadow-xs">
          <UserX className="w-7 h-7" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">Access Restricted by Role</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto leading-relaxed">
            Your current role (<span className="font-semibold text-slate-800">{curMeta.title}</span>) is not permitted to view this module.
          </p>
        </div>
      </div>
    );
  }

  // 4. Granular Permission Check
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="min-h-[380px] flex flex-col items-center justify-center bg-white p-8 rounded-3xl border border-slate-200 shadow-sm text-center max-w-lg mx-auto my-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 shadow-xs">
          <ShieldAlert className="w-7 h-7" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">Permission Denied</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto leading-relaxed">
            Missing authority scope: <span className="font-mono text-rose-600 font-bold">{requiredPermission}</span>.
          </p>
        </div>
      </div>
    );
  }

  return children;
}
