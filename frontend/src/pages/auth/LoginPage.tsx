import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Compass,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';
import { INITIAL_USERS } from '../../data/mockData';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('hamza.tariq@example.pk');
  const [password, setPassword] = useState('demo123456');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      await login(email);
      navigate('/app/dashboard');
    } catch {
      setErrorMessage('Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickRoleLogin = async (role: UserRole) => {
    setIsLoading(true);
    const demoUser = INITIAL_USERS.find((u) => u.role === role);
    if (demoUser) {
      setEmail(demoUser.email);
    }
    await login(demoUser?.email || '', role);
    setIsLoading(false);
    navigate('/app/dashboard');
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        {/* Brand header */}
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="h-10 w-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-lg shadow-teal-900/40">
              <Compass className="h-6 w-6" />
            </div>
            <span className="font-heading font-bold text-2xl text-white">ArchiCraft AI</span>
          </Link>
          <h1 className="text-xl font-bold text-white font-heading">Sign In to Workspace</h1>
          <p className="text-xs text-slate-400">
            Access your architectural projects, floor plans, and cost estimates.
          </p>
        </div>

        {/* Demo Notice Banner */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 text-xs space-y-2.5">
          <div className="flex items-center justify-between text-teal-400 font-semibold">
            <span className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5" /> 1-Click Sandbox Logins:
            </span>
            <span className="text-[10px] font-mono text-slate-400">FYP EVALUATION MODE</span>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            <button
              type="button"
              onClick={() => handleQuickRoleLogin('customer')}
              className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-emerald-500/60 text-left text-slate-300 transition-colors"
            >
              <p className="font-bold text-emerald-400 text-[11px]">Homeowner</p>
              <p className="text-[10px] text-slate-400 truncate">Hamza Tariq</p>
            </button>
            <button
              type="button"
              onClick={() => handleQuickRoleLogin('architect')}
              className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-teal-500/60 text-left text-slate-300 transition-colors"
            >
              <p className="font-bold text-teal-400 text-[11px]">PCATP Architect</p>
              <p className="text-[10px] text-slate-400 truncate">Ar. Ayesha Mansoor</p>
            </button>
            <button
              type="button"
              onClick={() => handleQuickRoleLogin('admin')}
              className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-purple-500/60 text-left text-slate-300 transition-colors"
            >
              <p className="font-bold text-purple-400 text-[11px]">Administrator</p>
              <p className="text-[10px] text-slate-400 truncate">Bilal Rasheed</p>
            </button>
            <button
              type="button"
              onClick={() => handleQuickRoleLogin('contractor')}
              className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-amber-500/60 text-left text-slate-300 transition-colors"
            >
              <p className="font-bold text-amber-400 text-[11px]">Contractor</p>
              <p className="text-[10px] text-slate-400 truncate">Malik Zafar & Sons</p>
            </button>
          </div>
        </div>

        {/* Form Container */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-5">
          {errorMessage && (
            <div className="p-3 rounded-xl bg-red-950/60 border border-red-800/80 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-300 font-medium mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.pk"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder:text-slate-400 focus:outline-none focus:border-teal-500"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs text-slate-300 font-medium">Password</label>
                <Link to="/forgot-password" className="text-[11px] text-teal-400 hover:text-teal-300">
                  Forgot Password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder:text-slate-400 focus:outline-none focus:border-teal-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 cursor-pointer text-slate-400">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-800 bg-slate-950 text-teal-500 focus:ring-teal-500"
                />
                <span>Remember me on this browser</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs shadow-lg shadow-teal-900/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <span>Sign In to Dashboard</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="text-center pt-2 border-t border-slate-800/80 text-xs text-slate-400">
            Don't have an account?{' '}
            <Link to="/signup" className="text-teal-400 hover:text-teal-300 font-semibold">
              Create Homeowner Account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
