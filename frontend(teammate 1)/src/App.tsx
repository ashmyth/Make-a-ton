import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import { UserProfile } from './types';
import { AuthModal } from './components/auth/AuthModal';
import { StaffManagement } from './components/staff/StaffManagement';
import { CustomerManagement } from './components/customers/CustomerManagement';
import { AuditTrail } from './components/audit/AuditTrail';
import { CustomerPortalView } from './components/portal/CustomerPortalView';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'customers' | 'staff' | 'audit' | 'portal'>('customers');

  const checkAuth = async () => {
    try {
      const user = await api.auth.me();
      setCurrentUser(user);
      if (user.role === 'CUSTOMER') {
        setActiveTab('portal');
      } else {
        setActiveTab('customers');
      }
    } catch {
      setCurrentUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogout = async () => {
    try {
      await api.auth.logout();
    } catch (err) {
      console.error(err);
    } finally {
      setCurrentUser(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-300">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
          <span className="font-medium text-sm">Connecting to Brightloop platform...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-6">
        <header className="flex justify-between items-center max-w-6xl w-full mx-auto">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-amber-400 text-slate-950 font-black flex items-center justify-center text-sm">
              BL
            </span>
            <span className="font-bold tracking-tight text-lg">Brightloop</span>
          </div>
          <div className="text-xs text-slate-400">
            Modular Monolith • Identity & Customer Foundation
          </div>
        </header>

        <AuthModal onLoginSuccess={(user) => {
          setCurrentUser(user);
          setActiveTab(user.role === 'CUSTOMER' ? 'portal' : 'customers');
        }} />

        <footer className="text-center text-xs text-slate-600">
          Brightloop Subscription Management Platform • Python 5.2 / DRF Backend
        </footer>
      </div>
    );
  }

  const isStaff = ['ADMINISTRATOR', 'OPERATIONS', 'FINANCE'].includes(currentUser.role);
  const isAdmin = currentUser.role === 'ADMINISTRATOR';

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-amber-400 text-slate-950 font-black flex items-center justify-center text-sm shadow-sm">
                BL
              </span>
              <span className="font-black tracking-tight text-lg">Brightloop</span>
            </div>

            {/* Navigation tabs */}
            <nav className="flex space-x-1">
              {isStaff && (
                <button
                  onClick={() => setActiveTab('customers')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                    activeTab === 'customers'
                      ? 'bg-amber-400 text-slate-950 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  Customer CRM
                </button>
              )}

              {isAdmin && (
                <button
                  onClick={() => setActiveTab('staff')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                    activeTab === 'staff'
                      ? 'bg-amber-400 text-slate-950 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  Staff Management
                </button>
              )}

              {isAdmin && (
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                    activeTab === 'audit'
                      ? 'bg-amber-400 text-slate-950 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  Audit Trail
                </button>
              )}

              {currentUser.role === 'CUSTOMER' && (
                <button
                  onClick={() => setActiveTab('portal')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                    activeTab === 'portal'
                      ? 'bg-amber-400 text-slate-950 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  Customer Profile
                </button>
              )}
            </nav>
          </div>

          {/* Right identity & logout */}
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-slate-900 dark:text-slate-100">
                {currentUser.full_name}
              </div>
              <div className="flex items-center gap-1.5 justify-end">
                <span
                  className={`inline-block w-1.5 h-1.5 rounded-full ${
                    currentUser.is_active ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  {currentUser.role}
                </span>
                {currentUser.customer_id && (
                  <span className="text-[10px] font-mono text-amber-500 font-bold ml-1">
                    [Linked Customer]
                  </span>
                )}
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'customers' && isStaff && <CustomerManagement />}
        {activeTab === 'staff' && isAdmin && <StaffManagement />}
        {activeTab === 'audit' && isAdmin && <AuditTrail />}
        {activeTab === 'portal' && <CustomerPortalView />}
      </main>

      <footer className="border-t border-slate-200 dark:border-slate-800 py-4 text-center text-xs text-slate-500">
        Brightloop Platform • Teammate 1: Identity, Access & Customer Foundation • PostgreSQL + Argon2id
      </footer>
    </div>
  );
};

