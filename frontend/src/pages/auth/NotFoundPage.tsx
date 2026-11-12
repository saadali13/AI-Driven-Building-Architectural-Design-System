import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, Home, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[75vh] flex items-center justify-center px-4 py-12">
      <div className="text-center space-y-5 max-w-md bg-white border border-[#E2E7E1] rounded-3xl p-8 shadow-sm">
        <div className="h-16 w-16 rounded-2xl bg-[#DCE7DE] border border-[#23483D]/20 text-[#23483D] flex items-center justify-center mx-auto">
          <Compass className="h-8 w-8 animate-spin-slow" />
        </div>
        <div className="space-y-1.5">
          <span className="text-xs font-mono font-bold text-[#B86F50]">ERROR 404</span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#202923] font-heading">Page Not Found</h1>
          <p className="text-xs text-[#68736C]">
            The requested architectural blueprint, report, or workspace route does not exist.
          </p>
        </div>
        <div className="flex items-center justify-center gap-3 pt-2">
          <Link
            to="/"
            className="px-4 py-2 rounded-xl bg-[#23483D] hover:bg-[#1a362d] text-white text-xs font-semibold flex items-center gap-2 shadow-xs transition-colors"
          >
            <Home className="h-3.5 w-3.5" />
            <span>Return Home</span>
          </Link>
          <Link
            to="/app/dashboard"
            className="px-4 py-2 rounded-xl bg-white hover:bg-[#F7F7F2] border border-[#E2E7E1] text-[#202923] text-xs font-semibold flex items-center gap-2 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Go to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
