import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Customer, CustomerType, PaymentTerms } from '../../types';

export const CustomerManagement: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ACTIVE');
  const [typeFilter, setTypeFilter] = useState<string>('');

  // Selected customer for detail/edit
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Create form state
  const [customerType, setCustomerType] = useState<CustomerType>('INDIVIDUAL');
  const [displayName, setDisplayName] = useState('');
  const [contactPerson, setContactPerson] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [billingStreet, setBillingStreet] = useState('');
  const [billingCity, setBillingCity] = useState('');
  const [billingState, setBillingState] = useState('');
  const [billingPostalCode, setBillingPostalCode] = useState('');
  const [billingCountry, setBillingCountry] = useState('United States');
  const [taxIdentifier, setTaxIdentifier] = useState('');
  const [paymentTerms, setPaymentTerms] = useState<PaymentTerms>('NET_30');

  // Link portal form state
  const [portalEmail, setPortalEmail] = useState('');
  const [portalPassword, setPortalPassword] = useState('');

  const loadCustomers = async () => {
    setLoading(true);
    try {
      const res = await api.customers.list({
        search,
        status: statusFilter,
        customer_type: typeFilter,
      });
      setCustomers(res.results || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load customers.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadCustomers();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, statusFilter, typeFilter]);

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const newCust = await api.customers.create({
        customer_type: customerType,
        display_name: displayName,
        contact_person: contactPerson,
        email,
        phone,
        billing_street: billingStreet,
        billing_city: billingCity,
        billing_state: billingState,
        billing_postal_code: billingPostalCode,
        billing_country: billingCountry,
        tax_identifier: taxIdentifier,
        payment_terms: paymentTerms,
      });
      setSuccessMsg(`Customer ${newCust.display_name} (${newCust.customer_code}) created successfully.`);
      setShowCreateModal(false);
      resetCreateForm();
      loadCustomers();
    } catch (err: any) {
      setError(err.message || 'Failed to create customer.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleArchiveToggle = async (customer: Customer) => {
    setError(null);
    setSuccessMsg(null);
    try {
      if (customer.status === 'ACTIVE') {
        if (!confirm(`Archive customer ${customer.display_name}? Historical quotations and invoices will remain intact.`)) {
          return;
        }
        await api.customers.archive(customer.id);
        setSuccessMsg(`Customer ${customer.display_name} has been archived.`);
      } else {
        await api.customers.unarchive(customer.id);
        setSuccessMsg(`Customer ${customer.display_name} has been reactivated.`);
      }
      loadCustomers();
      if (selectedCustomer?.id === customer.id) {
        setSelectedCustomer(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update customer status.');
    }
  };

  const handleLinkPortal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomer) return;
    setError(null);
    setSubmitting(true);
    try {
      await api.customers.linkPortal(selectedCustomer.id, {
        email: portalEmail,
        password: portalPassword,
      });
      setSuccessMsg(`Portal login successfully linked for ${selectedCustomer.display_name}.`);
      setShowLinkModal(false);
      setPortalEmail('');
      setPortalPassword('');
      loadCustomers();
    } catch (err: any) {
      setError(err.message || 'Failed to link portal account.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetCreateForm = () => {
    setDisplayName('');
    setContactPerson('');
    setEmail('');
    setPhone('');
    setBillingStreet('');
    setBillingCity('');
    setBillingState('');
    setBillingPostalCode('');
    setTaxIdentifier('');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Customer CRM Foundation
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage business and individual customer records, billing addresses, tax IDs, and portal access.
          </p>
        </div>
        <button
          onClick={() => {
            setError(null);
            setSuccessMsg(null);
            setShowCreateModal(true);
          }}
          className="inline-flex items-center px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-950 font-semibold text-sm rounded-lg shadow-sm transition-colors"
        >
          + New Customer Record
        </button>
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

      {/* Filters Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
        <div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email, code (CUST-...), or contact..."
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
        </div>
        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
          >
            <option value="ACTIVE">Status: Active Only</option>
            <option value="ARCHIVED">Status: Archived Only</option>
            <option value="">Status: All Records</option>
          </select>
        </div>
        <div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
          >
            <option value="">Type: All Types</option>
            <option value="BUSINESS">Type: Business</option>
            <option value="INDIVIDUAL">Type: Individual</option>
          </select>
        </div>
      </div>

      {/* Customers Table */}
      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading customers...</div>
      ) : customers.length === 0 ? (
        <div className="text-center py-12 bg-slate-50 dark:bg-slate-900 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
          <p className="text-slate-500">No customer records found matching your filters.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-3 font-semibold">Code / Customer</th>
                  <th className="px-6 py-3 font-semibold">Type</th>
                  <th className="px-6 py-3 font-semibold">Contact & Email</th>
                  <th className="px-6 py-3 font-semibold">Payment Terms</th>
                  <th className="px-6 py-3 font-semibold">Portal Account</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {customers.map((cust) => (
                  <tr
                    key={cust.id}
                    className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 dark:text-slate-100">
                        {cust.display_name}
                      </div>
                      <div className="text-xs font-mono text-amber-500 font-semibold">
                        {cust.customer_code}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {cust.customer_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div>{cust.email}</div>
                      {cust.contact_person && (
                        <div className="text-xs text-slate-500">Contact: {cust.contact_person}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs font-medium">
                      {cust.payment_terms.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {cust.portal_user_email ? (
                        <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                          ✓ {cust.portal_user_email}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">No Portal Link</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          cust.status === 'ACTIVE'
                            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                            : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                        }`}
                      >
                        {cust.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => setSelectedCustomer(cust)}
                        className="text-xs font-semibold px-2.5 py-1.5 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200"
                      >
                        Details
                      </button>
                      <button
                        onClick={() => handleArchiveToggle(cust)}
                        className={`text-xs font-semibold px-2.5 py-1.5 rounded transition-colors ${
                          cust.status === 'ACTIVE'
                            ? 'hover:bg-amber-50 text-amber-600 dark:hover:bg-amber-950/40'
                            : 'hover:bg-emerald-50 text-emerald-600 dark:hover:bg-emerald-950/40'
                        }`}
                      >
                        {cust.status === 'ACTIVE' ? 'Archive' : 'Restore'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Customer Details Drawer / Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-xl w-full p-6 text-slate-900 dark:text-slate-100">
            <div className="flex justify-between items-start border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
              <div>
                <span className="text-xs font-mono font-bold text-amber-500">
                  {selectedCustomer.customer_code}
                </span>
                <h3 className="text-xl font-bold">{selectedCustomer.display_name}</h3>
                <span className="text-xs text-slate-500">
                  Customer Type: {selectedCustomer.customer_type}
                </span>
              </div>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-slate-500 font-semibold uppercase">Email</div>
                  <div>{selectedCustomer.email}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 font-semibold uppercase">Phone</div>
                  <div>{selectedCustomer.phone || '—'}</div>
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-500 font-semibold uppercase">Contact Person</div>
                <div>{selectedCustomer.contact_person || '—'}</div>
              </div>

              <div>
                <div className="text-xs text-slate-500 font-semibold uppercase">Billing Address</div>
                <div className="text-slate-700 dark:text-slate-300">
                  {selectedCustomer.full_billing_address || 'No billing address recorded.'}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-slate-500 font-semibold uppercase">Tax Identifier</div>
                  <div>{selectedCustomer.tax_identifier || 'None'}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 font-semibold uppercase">Payment Terms</div>
                  <div className="font-mono">{selectedCustomer.payment_terms}</div>
                </div>
              </div>

              <div className="border-t border-slate-200 dark:border-slate-800 pt-3">
                <div className="text-xs text-slate-500 font-semibold uppercase mb-1">
                  Linked Portal Account
                </div>
                {selectedCustomer.portal_user_email ? (
                  <div className="text-emerald-600 dark:text-emerald-400 font-medium">
                    Account: {selectedCustomer.portal_user_email} (Customer Portal Active)
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500 italic">No portal account linked</span>
                    <button
                      onClick={() => {
                        setPortalEmail(selectedCustomer.email);
                        setShowLinkModal(true);
                      }}
                      className="text-xs font-semibold px-3 py-1 bg-amber-400 hover:bg-amber-300 text-slate-950 rounded-lg shadow-sm"
                    >
                      Link / Create Portal Account
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-slate-200 dark:border-slate-800 pt-4 mt-6">
              <button
                type="button"
                onClick={() => setSelectedCustomer(null)}
                className="px-4 py-2 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Link Portal Account Modal */}
      {showLinkModal && selectedCustomer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 text-slate-900 dark:text-slate-100">
            <h3 className="text-lg font-bold mb-2">Link Customer Portal User</h3>
            <p className="text-xs text-slate-500 mb-4">
              Create portal credentials for <strong>{selectedCustomer.display_name}</strong> to allow them to view their subscriptions, invoices, and payment history.
            </p>
            <form onSubmit={handleLinkPortal} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Portal Login Email
                </label>
                <input
                  type="email"
                  required
                  value={portalEmail}
                  onChange={(e) => setPortalEmail(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Initial Password (PRD 9+ Chars, Upper, Lower, Special)
                </label>
                <input
                  type="password"
                  required
                  value={portalPassword}
                  onChange={(e) => setPortalPassword(e.target.value)}
                  placeholder="PortalUser@123"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowLinkModal(false)}
                  className="px-4 py-2 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-950 text-sm font-bold rounded-lg shadow-sm"
                >
                  {submitting ? 'Linking...' : 'Grant Portal Access'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Customer Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full p-6 text-slate-900 dark:text-slate-100 my-8">
            <div className="flex justify-between items-center mb-4 border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-lg font-bold">New Customer CRM Record</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCustomer} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Customer Type
                  </label>
                  <select
                    value={customerType}
                    onChange={(e) => setCustomerType(e.target.value as CustomerType)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  >
                    <option value="INDIVIDUAL">Individual Customer</option>
                    <option value="BUSINESS">Business / Corporate Account</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Display Name / Company Name
                  </label>
                  <input
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder={customerType === 'BUSINESS' ? 'Acme Global Inc' : 'Jane Doe'}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Primary Email
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="contact@company.com"
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
                    placeholder="+1 (555) 000-0000"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Contact Person
                  </label>
                  <input
                    type="text"
                    value={contactPerson}
                    onChange={(e) => setContactPerson(e.target.value)}
                    placeholder="Alice Johnson"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
              </div>

              <div className="border-t border-slate-200 dark:border-slate-800 pt-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Billing Address (Snapshotted on Invoices)
                </h4>
                <div className="space-y-3">
                  <div>
                    <input
                      type="text"
                      value={billingStreet}
                      onChange={(e) => setBillingStreet(e.target.value)}
                      placeholder="Street Address, Suite / Unit"
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                    />
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    <div>
                      <input
                        type="text"
                        value={billingCity}
                        onChange={(e) => setBillingCity(e.target.value)}
                        placeholder="City"
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        value={billingState}
                        onChange={(e) => setBillingState(e.target.value)}
                        placeholder="State / Region"
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        value={billingPostalCode}
                        onChange={(e) => setBillingPostalCode(e.target.value)}
                        placeholder="Postal Code"
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        value={billingCountry}
                        onChange={(e) => setBillingCountry(e.target.value)}
                        placeholder="Country"
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 border-t border-slate-200 dark:border-slate-800 pt-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Tax Identifier (VAT / GST / EIN)
                  </label>
                  <input
                    type="text"
                    value={taxIdentifier}
                    onChange={(e) => setTaxIdentifier(e.target.value)}
                    placeholder="US-EIN-948271049"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Default Payment Terms
                  </label>
                  <select
                    value={paymentTerms}
                    onChange={(e) => setPaymentTerms(e.target.value as PaymentTerms)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                  >
                    <option value="IMMEDIATE">Due Immediately</option>
                    <option value="NET_15">Net 15 Days</option>
                    <option value="NET_30">Net 30 Days</option>
                    <option value="NET_60">Net 60 Days</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-950 text-sm font-bold rounded-lg shadow-sm"
                >
                  {submitting ? 'Saving...' : 'Save Customer Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

