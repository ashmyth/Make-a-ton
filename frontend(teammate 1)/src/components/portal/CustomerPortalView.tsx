import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Customer } from '../../types';

export const CustomerPortalView: React.FC = () => {
  const [profile, setProfile] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Editable fields per PRD §4.2
  const [contactPerson, setContactPerson] = useState('');
  const [phone, setPhone] = useState('');
  const [street, setStreet] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('');
  const [saving, setSaving] = useState(false);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const cust = await api.customers.myProfile();
      setProfile(cust);
      setContactPerson(cust.contact_person || '');
      setPhone(cust.phone || '');
      setStreet(cust.billing_street || '');
      setCity(cust.billing_city || '');
      setState(cust.billing_state || '');
      setPostalCode(cust.billing_postal_code || '');
      setCountry(cust.billing_country || 'United States');
    } catch (err: any) {
      setError(err.message || 'No linked customer profile found for this portal user.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setError(null);
    setSuccessMsg(null);
    setSaving(true);
    try {
      const updated = await api.customers.update(profile.id, {
        contact_person: contactPerson,
        phone,
        billing_street: street,
        billing_city: city,
        billing_state: state,
        billing_postal_code: postalCode,
        billing_country: country,
      });
      setProfile(updated);
      setSuccessMsg('Profile and billing address updated successfully.');
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Customer Self-Service Portal
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          View your linked account, update contact information, and manage your billing address.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 text-sm">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-sm">
          {successMsg}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading your customer record...</div>
      ) : !profile ? (
        <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 p-6 rounded-xl text-center">
          <h3 className="font-bold text-amber-900 dark:text-amber-200 mb-1">
            Unlinked Portal Account
          </h3>
          <p className="text-sm text-amber-800 dark:text-amber-300">
            This login is not yet linked to an active Customer CRM record. Please ask operations staff to link your account to a customer record.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Readonly Account Details */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
              Account Overview
            </h2>
            <div>
              <div className="text-xs text-slate-500">Customer Reference</div>
              <div className="font-mono font-bold text-amber-500">{profile.customer_code}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Display Name / Company</div>
              <div className="font-bold text-slate-900 dark:text-slate-100">{profile.display_name}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Account Type</div>
              <div className="text-sm font-medium">{profile.customer_type}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Payment Terms</div>
              <div className="font-mono text-sm">{profile.payment_terms}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Tax Identifier</div>
              <div className="text-sm">{profile.tax_identifier || 'None'}</div>
            </div>
            <div className="pt-2 text-xs text-slate-400 italic">
              * Note: Account legal name, payment terms, and status can only be modified by Brightloop operations staff.
            </div>
          </div>

          {/* Editable Self-Service Profile */}
          <div className="md:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4">
              Permitted Profile & Billing Address Updates
            </h2>
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Contact Person Name
                  </label>
                  <input
                    type="text"
                    value={contactPerson}
                    onChange={(e) => setContactPerson(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Billing Street Address
                </label>
                <input
                  type="text"
                  value={street}
                  onChange={(e) => setStreet(e.target.value)}
                  placeholder="Suite, Street Address"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    State / Region
                  </label>
                  <input
                    type="text"
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Postal Code
                  </label>
                  <input
                    type="text"
                    value={postalCode}
                    onChange={(e) => setPostalCode(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Country
                </label>
                <input
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-sm rounded-lg shadow-sm"
                >
                  {saving ? 'Saving Changes...' : 'Save Profile Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

