import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, KeyRound } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';

export const AccessDeniedPage: React.FC = () => {
  const { currentUser, switchRole } = useAuth();
  const navigate = useNavigate();

  const handleRoleElevate = (role: UserRole) => {
    switchRole(role);
    navigate('/app/dashboard');
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-12">
      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-8 max-w-lg w-full text-center space-y-6 shadow-sm">
        <div className="h-16 w-16 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
          <ShieldAlert className="h-8 w-8" />
        </div>

        <div className="space-y-2">
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200 font-semibold">
            HTTP 403 &bull; ACCESS RESTRICTED
          </span>
          <h1 className="text-2xl font-bold text-[#202923] font-heading">Privileged Role Required</h1>
          <p className="text-xs text-[#68736C] leading-relaxed">
            Your current logged-in role (<strong className="text-[#202923] capitalize">{currentUser?.role || 'Guest'}</strong>) does not have permission to access this route.
          </p>
        </div>

        {/* Demo Role Sandbox Switcher */}
        <div className="bg-[#F7F7F2] rounded-2xl p-4 border border-[#E2E7E1] text-left space-y-2.5">
          <p className="text-[11px] font-semibold text-[#202923] flex items-center gap-1.5">
            <KeyRound className="h-3.5 w-3.5 text-[#23483D]" />
            Switch Demo Role to Proceed:
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              onClick={() => handleRoleElevate('admin')}
              className="p-2.5 rounded-xl bg-white hover:bg-[#DCE7DE]/40 border border-[#E2E7E1] text-left transition-colors"
            >
              <p className="font-bold text-[#23483D]">System Admin</p>
              <p className="text-[10px] text-[#68736C]">Manage users & rates</p>
            </button>
            <button
              onClick={() => handleRoleElevate('architect')}
              className="p-2.5 rounded-xl bg-white hover:bg-[#DCE7DE]/40 border border-[#E2E7E1] text-left transition-colors"
            >
              <p className="font-bold text-[#23483D]">PCATP Architect</p>
              <p className="text-[10px] text-[#68736C]">Review client plans</p>
            </button>
          </div>
        </div>

        <div className="flex items-center justify-center gap-3 pt-2">
          <Link
            to="/app/dashboard"
            className="px-4 py-2 rounded-xl bg-[#23483D] hover:bg-[#1a362d] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Return to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
