import React, { useState, useEffect } from "react";
import {
  api,
  ApiError,
  type PortalOverviewData,
  type Subscription,
  type Invoice,
  type Payment,
  type CustomerRequest,
} from "../api";
import {
  Layers,
  Download,
  AlertCircle,
  Clock,
  MapPin,
  PauseCircle,
  XCircle,
  RotateCw,
} from "lucide-react";

function formatApiError(err: unknown, fallback: string): string {
  if (err instanceof ApiError) {
    if (err.fieldErrors) {
      return Object.entries(err.fieldErrors)
        .map(([field, msgs]) => `${field}: ${msgs.join(" ")}`)
        .join(" | ");
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

interface CustomerPortalProps {
  onOpenLogin?: () => void;
}

export const CustomerPortal: React.FC<CustomerPortalProps> = ({ onOpenLogin }) => {
  const [overview, setOverview] = useState<PortalOverviewData | null>(null);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [requests, setRequests] = useState<CustomerRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active Tab: overview | invoices | subscriptions | payments | profile
  const [activeTab, setActiveTab] = useState<"overview" | "invoices" | "subscriptions" | "payments" | "profile">("overview");

  // Request modal
  const [requestModalSub, setRequestModalSub] = useState<Subscription | null>(null);
  const [requestType, setRequestType] = useState<"pause" | "cancel" | "renew">("pause");
  const [requestNotes, setRequestNotes] = useState("");
  const [submittingRequest, setSubmittingRequest] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState<string | null>(null);

  // Profile Edit Form
  const [profileForm, setProfileForm] = useState({
    contact_person: "",
    phone: "",
    billing_street: "",
    billing_city: "",
    billing_state: "",
    billing_postal_code: "",
    billing_country: "",
  });
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);

  const fetchPortalData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewData, subsData, invsData, paysData, reqsData] = await Promise.all([
        api.portal.getOverview(),
        api.portal.getSubscriptions(),
        api.portal.getInvoices(),
        api.portal.getPayments(),
        api.portal.getRequests(),
      ]);

      setOverview(overviewData);
      setSubscriptions(subsData);
      setInvoices(invsData);
      setPayments(paysData);
      setRequests(reqsData);

      if (overviewData.customer) {
        setProfileForm({
          contact_person: overviewData.customer.contact_person || "",
          phone: overviewData.customer.phone || "",
          billing_street: "",
          billing_city: "",
          billing_state: "",
          billing_postal_code: "",
          billing_country: "",
        });
      }
    } catch (err: unknown) {
      setError(formatApiError(err, "Failed to load portal information. Please ensure you are logged in."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, []);

  const handleOpenRequest = (sub: Subscription, type: "pause" | "cancel" | "renew") => {
    setRequestModalSub(sub);
    setRequestType(type);
    setRequestNotes("");
    setRequestSuccess(null);
  };

  const handleSubmitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestModalSub) return;
    setSubmittingRequest(true);
    try {
      await api.portal.submitRequest({
        subscription: requestModalSub.id,
        request_type: requestType,
        notes: requestNotes,
      });
      setRequestSuccess("Request submitted successfully to Brightloop operations.");
      setTimeout(() => {
        setRequestModalSub(null);
        fetchPortalData();
      }, 1500);
    } catch (err: unknown) {
      setError(formatApiError(err, "Failed to submit request."));
    } finally {
      setSubmittingRequest(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileSuccess(null);
    try {
      await api.portal.updateProfile(profileForm);
      setProfileSuccess("Profile updated successfully.");
      await fetchPortalData();
    } catch (err: unknown) {
      setError(formatApiError(err, "Failed to save profile."));
    } finally {
      setSavingProfile(false);
    }
  };

  if (loading && !overview) {
    return (
      <div style={{ padding: "60px", textAlign: "center", color: "#afafaf" }}>
        Loading customer portal...
      </div>
    );
  }

  if (error && !overview) {
    const isAuthError = error.toLowerCase().includes("authentication") || error.toLowerCase().includes("logged in");
    return (
      <div style={{ maxWidth: "800px", margin: "40px auto", padding: "24px" }} className="card-carbon">
        <div style={{ display: "flex", gap: "12px", alignItems: "center", color: isAuthError ? "#f59e0b" : "#ff4d4d", marginBottom: "16px" }}>
          <AlertCircle size={24} />
          <h2 style={{ fontSize: "18px", fontWeight: 600 }}>
            {isAuthError ? "Sign In Required" : "Portal Access Restricted"}
          </h2>
        </div>
        <p style={{ color: "#afafaf", fontSize: "14px", marginBottom: "20px" }}>
          {isAuthError
            ? "Please sign in or create an account to view your customer portal, active subscriptions, and invoices."
            : error}
        </p>
        <div style={{ display: "flex", gap: "12px" }}>
          {onOpenLogin && (
            <button onClick={onOpenLogin} className="btn-yellow">
              Sign In / Register
            </button>
          )}
          <button onClick={fetchPortalData} className="btn-secondary" style={{ padding: "8px 16px", borderRadius: "6px" }}>
            Retry Access
          </button>
        </div>
      </div>
    );
  }

  const customer = overview?.customer;
  const metrics = overview?.metrics;

  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Customer Header Banner */}
      <div style={{ background: "#1a1a1a", border: "1px solid #333333", borderRadius: "9px", padding: "24px", marginBottom: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h1 style={{ fontSize: "28px", fontWeight: 300, color: "#eeeeee", letterSpacing: "-0.5px" }}>
                {customer?.display_name || "Customer Workspace"}
              </h1>
              <span style={{ background: "#fff313", color: "#000000", fontSize: "11px", fontWeight: 700, padding: "2px 8px", borderRadius: "4px" }}>
                {customer?.customer_code}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "16px", color: "#afafaf", fontSize: "13px", marginTop: "6px" }}>
              <span>Contact: {customer?.contact_person}</span>
              <span>•</span>
              <span>Email: {customer?.email}</span>
              <span>•</span>
              <span>Terms: {customer?.payment_terms}</span>
            </div>
          </div>

          <div style={{ display: "flex", gap: "24px", textAlign: "right" }}>
            <div>
              <div style={{ fontSize: "11px", color: "#afafaf", textTransform: "uppercase" }}>Total Outstanding</div>
              <div style={{ fontSize: "24px", fontWeight: 600, color: parseFloat(metrics?.total_outstanding_balance || "0") > 0 ? "#fff313" : "#00e676" }}>
                ₹{parseFloat(metrics?.total_outstanding_balance || "0").toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Portal Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid #333333", marginBottom: "24px", overflowX: "auto" }}>
        {[
          { id: "overview", label: "Overview" },
          { id: "invoices", label: `Invoices (${invoices.length})` },
          { id: "subscriptions", label: `Subscriptions (${subscriptions.length})` },
          { id: "payments", label: `Payments (${payments.length})` },
          { id: "profile", label: "Billing Profile" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              background: "transparent",
              border: "none",
              borderBottom: activeTab === tab.id ? "2px solid #fff313" : "2px solid transparent",
              color: activeTab === tab.id ? "#fff313" : "#afafaf",
              padding: "10px 18px",
              fontSize: "14px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px", marginBottom: "32px" }}>
            {/* Active Subscriptions Card */}
            <div className="card-carbon">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "12px", color: "#afafaf", textTransform: "uppercase" }}>Active Subscriptions</span>
                <Layers size={16} color="#00e676" />
              </div>
              <div style={{ fontSize: "36px", fontWeight: 300, color: "#eeeeee", margin: "12px 0 4px" }}>
                {metrics?.active_subscriptions || 0}
              </div>
              <p style={{ fontSize: "13px", color: "#888888" }}>
                Provisioned commercial service contracts
              </p>
            </div>

            {/* Unpaid Invoices Card */}
            <div className="card-carbon">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "12px", color: "#afafaf", textTransform: "uppercase" }}>Pending Invoices</span>
                <Clock size={16} color="#fff313" />
              </div>
              <div style={{ fontSize: "36px", fontWeight: 300, color: (metrics?.unpaid_invoices_count ?? 0) > 0 ? "#fff313" : "#00e676", margin: "12px 0 4px" }}>
                {metrics?.unpaid_invoices_count || 0}
              </div>
              <p style={{ fontSize: "13px", color: "#888888" }}>
                {(metrics?.unpaid_invoices_count ?? 0) > 0 ? "Awaiting settlement / bank transfer" : "All accounts up to date"}
              </p>
            </div>

            {/* Billing Address Card */}
            <div className="card-carbon">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "12px", color: "#afafaf", textTransform: "uppercase" }}>Official Billing Entity</span>
                <MapPin size={16} color="#afafaf" />
              </div>
              <div style={{ fontSize: "14px", fontWeight: 600, color: "#eeeeee", marginTop: "12px" }}>
                {customer?.display_name}
              </div>
              <div style={{ fontSize: "13px", color: "#afafaf", marginTop: "4px" }}>
                {customer?.full_billing_address || "No billing address configured."}
              </div>
            </div>
          </div>

          {/* Recent Invoices Section */}
          <div style={{ marginBottom: "32px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "16px" }}>
              Recent Invoices
            </h2>
            <div className="card-carbon" style={{ padding: "0", overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
                <thead>
                  <tr style={{ background: "#222222", borderBottom: "1px solid #333333", color: "#afafaf", textTransform: "uppercase", fontSize: "11px" }}>
                    <th style={{ padding: "12px 16px" }}>Invoice #</th>
                    <th style={{ padding: "12px 16px" }}>Issue Date</th>
                    <th style={{ padding: "12px 16px" }}>Due Date</th>
                    <th style={{ padding: "12px 16px" }}>Status</th>
                    <th style={{ padding: "12px 16px", textAlign: "right" }}>Total</th>
                    <th style={{ padding: "12px 16px", textAlign: "right" }}>Balance Due</th>
                    <th style={{ padding: "12px 16px", textAlign: "center" }}>Download</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.slice(0, 3).map((inv) => (
                    <tr key={inv.id} style={{ borderBottom: "1px solid #2a2a2a" }}>
                      <td style={{ padding: "12px 16px", fontWeight: 600, color: "#eeeeee" }}>{inv.invoice_number}</td>
                      <td style={{ padding: "12px 16px", color: "#afafaf" }}>{inv.issue_date}</td>
                      <td style={{ padding: "12px 16px", color: "#afafaf" }}>{inv.due_date}</td>
                      <td style={{ padding: "12px 16px" }}>
                        <span className={`badge badge-${inv.status === "paid" ? "paid" : inv.status === "partially_paid" ? "partial" : "unpaid"}`}>
                          {inv.status.replace("_", " ")}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right", color: "#eeeeee" }}>
                        ₹{parseFloat(inv.total_amount).toLocaleString()}
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right", fontWeight: 600, color: parseFloat(inv.outstanding_balance) > 0 ? "#fff313" : "#00e676" }}>
                        ₹{parseFloat(inv.outstanding_balance).toLocaleString()}
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "center" }}>
                        <a
                          href={api.portal.getInvoiceDownloadUrl(inv.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-secondary"
                          style={{ padding: "4px 8px", fontSize: "12px" }}
                        >
                          <Download size={12} /> HTML/PDF
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Invoices List */}
      {activeTab === "invoices" && (
        <div className="card-carbon" style={{ padding: "0", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#222222", borderBottom: "1px solid #333333", color: "#afafaf", textTransform: "uppercase", fontSize: "11px" }}>
                <th style={{ padding: "12px 16px" }}>Invoice #</th>
                <th style={{ padding: "12px 16px" }}>Subscription</th>
                <th style={{ padding: "12px 16px" }}>Issue Date</th>
                <th style={{ padding: "12px 16px" }}>Due Date</th>
                <th style={{ padding: "12px 16px" }}>Status</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Total</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Balance Due</th>
                <th style={{ padding: "12px 16px", textAlign: "center" }}>Download</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} style={{ borderBottom: "1px solid #2a2a2a" }}>
                  <td style={{ padding: "12px 16px", fontWeight: 600, color: "#eeeeee" }}>{inv.invoice_number}</td>
                  <td style={{ padding: "12px 16px", color: "#afafaf" }}>{inv.subscription_number || "Direct"}</td>
                  <td style={{ padding: "12px 16px", color: "#afafaf" }}>{inv.issue_date}</td>
                  <td style={{ padding: "12px 16px", color: "#afafaf" }}>{inv.due_date}</td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className={`badge badge-${inv.status === "paid" ? "paid" : inv.status === "partially_paid" ? "partial" : "unpaid"}`}>
                      {inv.status.replace("_", " ")}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "right", color: "#eeeeee" }}>
                    ₹{parseFloat(inv.total_amount).toLocaleString()}
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "right", fontWeight: 600, color: parseFloat(inv.outstanding_balance) > 0 ? "#fff313" : "#00e676" }}>
                    ₹{parseFloat(inv.outstanding_balance).toLocaleString()}
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "center" }}>
                    <a
                      href={api.portal.getInvoiceDownloadUrl(inv.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="btn-secondary"
                      style={{ padding: "4px 8px", fontSize: "12px" }}
                    >
                      <Download size={12} /> HTML/PDF
                    </a>
                  </td>
                </tr>
              ))}
              {invoices.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: "32px", textAlign: "center", color: "#888888" }}>
                    No invoices issued to your account yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Subscriptions List */}
      {activeTab === "subscriptions" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
          {subscriptions.map((sub) => (
            <div key={sub.id} className="card-carbon" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                  <div>
                    <span style={{ fontSize: "11px", color: "#fff313", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                      {sub.billing_interval} interval
                    </span>
                    <h3 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginTop: "2px" }}>
                      {sub.plan_name}
                    </h3>
                    <div style={{ fontSize: "12px", color: "#888888" }}>#{sub.subscription_number}</div>
                  </div>
                  <span className={`badge badge-${sub.is_paused ? "paused" : "active"}`}>
                    {sub.is_paused ? "PAUSED" : sub.status}
                  </span>
                </div>

                <div style={{ borderTop: "1px solid #333333", borderBottom: "1px solid #333333", padding: "12px 0", margin: "16px 0", fontSize: "13px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                    <span style={{ color: "#afafaf" }}>Start Date:</span>
                    <span style={{ color: "#eeeeee" }}>{sub.start_date}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                    <span style={{ color: "#afafaf" }}>Next Scheduled Billing:</span>
                    <span style={{ color: "#eeeeee" }}>{sub.next_billing_date || "Continuous"}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#afafaf" }}>Currency:</span>
                    <span style={{ color: "#eeeeee" }}>{sub.currency}</span>
                  </div>
                </div>
              </div>

              {/* Self-Service Actions */}
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", paddingTop: "8px" }}>
                {!sub.is_paused ? (
                  <button onClick={() => handleOpenRequest(sub, "pause")} className="btn-secondary" style={{ padding: "6px 10px", fontSize: "12px" }}>
                    <PauseCircle size={14} /> Request Pause
                  </button>
                ) : (
                  <button onClick={() => handleOpenRequest(sub, "renew")} className="btn-secondary" style={{ padding: "6px 10px", fontSize: "12px" }}>
                    <RotateCw size={14} /> Request Resume
                  </button>
                )}
                <button onClick={() => handleOpenRequest(sub, "renew")} className="btn-secondary" style={{ padding: "6px 10px", fontSize: "12px" }}>
                  <RotateCw size={14} /> Request Renewal
                </button>
                <button onClick={() => handleOpenRequest(sub, "cancel")} className="btn-secondary" style={{ padding: "6px 10px", fontSize: "12px", color: "#ff4d4d", borderColor: "#662222" }}>
                  <XCircle size={14} /> Request Cancel
                </button>
              </div>
            </div>
          ))}
          {subscriptions.length === 0 && (
            <div style={{ padding: "40px", textAlign: "center", color: "#888888" }} className="card-carbon">
              No subscriptions found.
            </div>
          )}

          {/* Pending Service Requests */}
          {requests.length > 0 && (
            <div style={{ gridColumn: "1 / -1", marginTop: "24px" }} className="card-carbon">
              <h3 style={{ fontSize: "16px", fontWeight: 600, color: "#eeeeee", marginBottom: "12px" }}>
                Submitted Service Requests
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {requests.map((r) => (
                  <div key={r.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", background: "#1a1a1a", border: "1px solid #333333", borderRadius: "6px", fontSize: "13px" }}>
                    <div>
                      <span style={{ fontWeight: 600, color: "#fff313", textTransform: "uppercase" }}>{r.request_type}</span>
                      <span style={{ color: "#afafaf", marginLeft: "12px" }}>Subscription: {r.subscription_number}</span>
                      {r.notes && <span style={{ color: "#888888", marginLeft: "12px" }}>"{r.notes}"</span>}
                    </div>
                    <span className="badge badge-partial">{r.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Payments History */}
      {activeTab === "payments" && (
        <div className="card-carbon" style={{ padding: "0", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#222222", borderBottom: "1px solid #333333", color: "#afafaf", textTransform: "uppercase", fontSize: "11px" }}>
                <th style={{ padding: "12px 16px" }}>Date</th>
                <th style={{ padding: "12px 16px" }}>Invoice #</th>
                <th style={{ padding: "12px 16px" }}>Method</th>
                <th style={{ padding: "12px 16px" }}>Reference</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Amount</th>
                <th style={{ padding: "12px 16px" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #2a2a2a" }}>
                  <td style={{ padding: "12px 16px", color: "#afafaf" }}>{new Date(p.paid_at).toLocaleDateString()}</td>
                  <td style={{ padding: "12px 16px", fontWeight: 600, color: "#eeeeee" }}>{p.invoice_number}</td>
                  <td style={{ padding: "12px 16px", color: "#afafaf", textTransform: "capitalize" }}>
                    {p.method.replace("_", " ")}
                  </td>
                  <td style={{ padding: "12px 16px", color: "#888888" }}>{p.external_reference || "—"}</td>
                  <td style={{ padding: "12px 16px", textAlign: "right", fontWeight: 600, color: "#00e676" }}>
                    +₹{parseFloat(p.amount).toLocaleString()}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className="badge badge-paid">{p.status}</span>
                  </td>
                </tr>
              ))}
              {payments.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "#888888" }}>
                    No payment history recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 5: Profile & Billing Settings */}
      {activeTab === "profile" && (
        <div style={{ maxWidth: "640px" }} className="card-carbon">
          <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "4px" }}>
            Customer Profile & Billing Contact
          </h2>
          <p style={{ fontSize: "13px", color: "#afafaf", marginBottom: "20px" }}>
            Per PRD §4.2, customers may edit contact details and billing addresses. Commercial tax identifiers and payment terms are managed by Brightloop finance administrators.
          </p>

          {profileSuccess && (
            <div style={{ background: "rgba(0, 230, 118, 0.15)", border: "1px solid #00e676", color: "#00e676", padding: "10px 14px", borderRadius: "6px", fontSize: "13px", marginBottom: "16px" }}>
              {profileSuccess}
            </div>
          )}

          <form onSubmit={handleSaveProfile}>
            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>Contact Person</label>
              <input
                type="text"
                value={profileForm.contact_person}
                onChange={(e) => setProfileForm({ ...profileForm, contact_person: e.target.value })}
                style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
              />
            </div>

            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>Phone Number</label>
              <input
                type="text"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
              />
            </div>

            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>Billing Street</label>
              <input
                type="text"
                value={profileForm.billing_street}
                onChange={(e) => setProfileForm({ ...profileForm, billing_street: e.target.value })}
                style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>City</label>
                <input
                  type="text"
                  value={profileForm.billing_city}
                  onChange={(e) => setProfileForm({ ...profileForm, billing_city: e.target.value })}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>State</label>
                <input
                  type="text"
                  value={profileForm.billing_state}
                  onChange={(e) => setProfileForm({ ...profileForm, billing_state: e.target.value })}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>Postal Code</label>
                <input
                  type="text"
                  value={profileForm.billing_postal_code}
                  onChange={(e) => setProfileForm({ ...profileForm, billing_postal_code: e.target.value })}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>Country</label>
                <input
                  type="text"
                  value={profileForm.billing_country}
                  onChange={(e) => setProfileForm({ ...profileForm, billing_country: e.target.value })}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                />
              </div>
            </div>

            <button type="submit" className="btn-yellow" disabled={savingProfile}>
              {savingProfile ? "Saving Profile..." : "Save Profile Changes"}
            </button>
          </form>
        </div>
      )}

      {/* Modal: Self-Service Subscription Request */}
      {requestModalSub && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "8px" }}>
              Submit Subscription Request
            </h2>
            <p style={{ fontSize: "13px", color: "#afafaf", marginBottom: "16px" }}>
              Subscription #{requestModalSub.subscription_number} — {requestModalSub.plan_name}
            </p>

            {requestSuccess ? (
              <div style={{ background: "rgba(0, 230, 118, 0.15)", border: "1px solid #00e676", color: "#00e676", padding: "12px", borderRadius: "6px", fontSize: "13px" }}>
                {requestSuccess}
              </div>
            ) : (
              <form onSubmit={handleSubmitRequest}>
                <div style={{ marginBottom: "14px" }}>
                  <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "6px" }}>
                    Request Type
                  </label>
                  <select
                    value={requestType}
                    onChange={(e) => setRequestType(e.target.value as any)}
                    style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                  >
                    <option value="pause">Pause Subscription</option>
                    <option value="renew">Renew Subscription</option>
                    <option value="cancel">Cancel Subscription</option>
                  </select>
                </div>

                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "6px" }}>
                    Reason or Instructions for Operations Staff
                  </label>
                  <textarea
                    rows={3}
                    placeholder="e.g. Please pause for 30 days due to project maintenance"
                    value={requestNotes}
                    onChange={(e) => setRequestNotes(e.target.value)}
                    style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                  />
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    type="button"
                    onClick={() => setRequestModalSub(null)}
                    className="btn-secondary"
                    disabled={submittingRequest}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-yellow"
                    disabled={submittingRequest}
                  >
                    {submittingRequest ? "Submitting..." : "Submit Request"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
