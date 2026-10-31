import React, { useState } from 'react';
import { api } from '../../services/api';
import { UserProfile } from '../../types';

interface AuthModalProps {
  onLoginSuccess: (user: UserProfile) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onLoginSuccess }) => {
  const [tab, setTab] = useState<'login' | 'register' | 'forgot' | 'reset'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLocked, setIsLocked] = useState(false);

  // Password rules validation for PRD §7.1
  const hasMinLength = (p: string) => p.length >= 9;
  const hasUpper = (p: string) => /[A-Z]/.test(p);
  const hasLower = (p: string) => /[a-z]/.test(p);
  const hasSpecial = (p: string) => /[^a-zA-Z0-9]/.test(p);
  const isPasswordValid = (p: string) =>
    hasMinLength(p) && hasUpper(p) && hasLower(p) && hasSpecial(p);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setIsLocked(false);
    try {
      const user = await api.auth.login({ email, password });
      onLoginSuccess(user);
    } catch (err: any) {
      if (err.status === 429) {
        setIsLocked(true);
        setError('Account temporarily locked due to 5 consecutive failed attempts. Please wait 15 minutes.');
      } else if (err.status === 403) {
        setError('This account has been deactivated. Please contact an administrator.');
      } else {
        setError(err.message || 'Invalid email or password.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPasswordValid(password)) {
      setError('Password must meet all PRD security criteria.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const user = await api.auth.register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      });
      setSuccessMsg('Account registered successfully! Logging you in...');
      setTimeout(() => onLoginSuccess(user), 1000);
    } catch (err: any) {
      setError(err.message || 'Failed to register account.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.auth.passwordResetRequest(email);
      setSuccessMsg(res.message);
    } catch (err: any) {
      setError(err.message || 'Error requesting password reset.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPasswordValid(newPassword)) {
      setError('New password must meet all PRD security criteria.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.auth.passwordResetConfirm({
        token: resetToken,
        new_password: newPassword,
      });
      setSuccessMsg(res.message + ' You may now log in.');
      setTab('login');
    } catch (err: any) {
      setError(err.message || 'Invalid or expired password reset token.');
    } finally {
      setLoading(false);
    }
  };

  const renderPasswordHints = (pwd: string) => (
    <div className="mt-2 text-xs space-y-1 bg-slate-50 dark:bg-slate-900/50 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
      <div className="font-semibold text-slate-600 dark:text-slate-400 mb-1">
        PRD Password Security Rules:
      </div>
      <div className={hasMinLength(pwd) ? 'text-emerald-600 font-medium' : 'text-slate-500'}>
        {hasMinLength(pwd) ? '✓' : '○'} At least 9 characters
      </div>
      <div className={hasUpper(pwd) ? 'text-emerald-600 font-medium' : 'text-slate-500'}>
        {hasUpper(pwd) ? '✓' : '○'} At least one uppercase letter (A-Z)
      </div>
      <div className={hasLower(pwd) ? 'text-emerald-600 font-medium' : 'text-slate-500'}>
        {hasLower(pwd) ? '✓' : '○'} At least one lowercase letter (a-z)
      </div>
      <div className={hasSpecial(pwd) ? 'text-emerald-600 font-medium' : 'text-slate-500'}>
        {hasSpecial(pwd) ? '✓' : '○'} At least one special character (!@#$%^&*)
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 text-slate-900 dark:text-slate-100">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-amber-400 text-slate-950 font-black text-xl mb-3 shadow-md">
            BL
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Brightloop Platform</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Subscription Management & Customer Foundation
          </p>
        </div>

        {error && (
          <div
            className={`mb-4 p-3 rounded-lg text-sm font-medium ${
              isLocked
                ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-800'
                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900'
            }`}
          >
            {error}
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3 rounded-lg text-sm bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            {successMsg}
          </div>
        )}

        {tab === 'login' && (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@brightloop.io"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setError(null);
                    setSuccessMsg(null);
                    setTab('forgot');
                  }}
                  className="text-xs text-amber-500 hover:text-amber-600 underline"
                >
                  Forgot password?
                </button>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg transition-colors shadow-sm disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>

            <div className="text-center pt-2 text-xs text-slate-500">
              Need a portal account?{' '}
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setSuccessMsg(null);
                  setTab('register');
                }}
                className="text-amber-500 font-semibold hover:underline"
              >
                Register here
              </button>
            </div>
          </form>
        )}

        {tab === 'register' && (
          <form onSubmit={handleRegister} className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  required
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="customer@example.com"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create strong password"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
              {renderPasswordHints(password)}
            </div>

            <button
              type="submit"
              disabled={loading || !isPasswordValid(password)}
              className="w-full py-2.5 px-4 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg transition-colors shadow-sm disabled:opacity-50"
            >
              {loading ? 'Creating Account...' : 'Register Account'}
            </button>

            <div className="text-center pt-2 text-xs text-slate-500">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setSuccessMsg(null);
                  setTab('login');
                }}
                className="text-amber-500 font-semibold hover:underline"
              >
                Sign in
              </button>
            </div>
          </form>
        )}

        {tab === 'forgot' && (
          <form onSubmit={handleForgotPassword} className="space-y-4">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Enter your registered email address. If an account exists, a single-use password reset link will be issued.
            </p>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg"
            >
              {loading ? 'Sending Request...' : 'Send Reset Link'}
            </button>
            <div className="flex justify-between items-center text-xs text-slate-500 pt-2">
              <button
                type="button"
                onClick={() => setTab('login')}
                className="text-amber-500 hover:underline"
              >
                Back to Sign in
              </button>
              <button
                type="button"
                onClick={() => setTab('reset')}
                className="text-amber-500 hover:underline"
              >
                Have a reset token?
              </button>
            </div>
          </form>
        )}

        {tab === 'reset' && (
          <form onSubmit={handleResetConfirm} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Reset Token
              </label>
              <input
                type="text"
                required
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                placeholder="Paste token received in email"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                New Password
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new secure password"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
              {renderPasswordHints(newPassword)}
            </div>
            <button
              type="submit"
              disabled={loading || !isPasswordValid(newPassword)}
              className="w-full py-2.5 px-4 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg"
            >
              {loading ? 'Updating Password...' : 'Reset Password'}
            </button>
            <div className="text-center text-xs text-slate-500 pt-2">
              <button
                type="button"
                onClick={() => setTab('login')}
                className="text-amber-500 hover:underline"
              >
                Back to Sign in
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

