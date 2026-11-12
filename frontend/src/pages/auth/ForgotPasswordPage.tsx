import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Compass, Mail, ArrowRight, CheckCircle2 } from 'lucide-react';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setSubmitted(true);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="h-10 w-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-lg">
              <Compass className="h-6 w-6" />
            </div>
            <span className="font-heading font-bold text-2xl text-white">ArchiCraft AI</span>
          </Link>
          <h1 className="text-xl font-bold text-white font-heading">Reset Password</h1>
          <p className="text-xs text-slate-400">
            Enter your account email to receive a password reset link.
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-5">
          {submitted ? (
            <div className="text-center space-y-3 py-4">
              <div className="h-12 w-12 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center mx-auto">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-bold text-white">Reset Link Dispatched</h3>
              <p className="text-xs text-slate-400">
                A password reset authorization link has been simulated for <strong className="text-white">{email}</strong>.
              </p>
              <Link
                to="/reset-password?token=demo_token_123"
                className="inline-block px-4 py-2 bg-teal-600 text-white rounded-xl text-xs font-semibold mt-2"
              >
                Proceed to Reset Password Page
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1.5">Registered Email</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    placeholder="name@example.pk"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder:text-slate-400 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold shadow-md transition-colors flex items-center justify-center gap-2"
              >
                <span>Send Reset Link</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </form>
          )}

          <div className="text-center pt-2 border-t border-slate-800/80 text-xs text-slate-400">
            Remembered your password?{' '}
            <Link to="/login" className="text-teal-400 hover:text-teal-300 font-semibold">
              Return to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
