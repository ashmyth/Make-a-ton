import React, { useState, useEffect } from "react";
import { api } from "../api";
import {
  TrendingUp,
  DollarSign,
  AlertCircle,
  Clock,
  Layers,
  Activity,
  PlusCircle,
  RotateCcw,
  RefreshCw,
  FileText,
} from "lucide-react";

export const FinanceConsole: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active view tab in console
  const [activeTab, setActiveTab] = useState<"invoices" | "payments">("invoices");

  // Filter state
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Record Payment Modal
  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("bank_transfer");
  const [externalRef, setExternalRef] = useState("");
  const [paymentNotes, setPaymentNotes] = useState("");
  const [submittingPayment, setSubmittingPayment] = useState(false);
  const [paymentFormError, setPaymentFormError] = useState<string | null>(null);

  // Reverse Payment Modal
  const [reversalTarget, setReversalTarget] = useState<any>(null);
  const [reversalReason, setReversalReason] = useState("");
  const [submittingReversal, setSubmittingReversal] = useState(false);
  const [reversalError, setReversalError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const [metricsData, invoicesData, paymentsData] = await Promise.all([
        api.finance.getDashboardMetrics(params),
        api.finance.getInvoicesReport(statusFilter ? { status: statusFilter } : {}),
        api.finance.getPaymentsReport(),
      ]);

      setMetrics(metricsData);
      setInvoices(invoicesData);
      setPayments(paymentsData);
    } catch (err: any) {
      setError(err.message || "Failed to load finance data. Ensure you are signed in as Finance or Admin staff.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate, statusFilter]);

  const handleOpenRecordPayment = (invoiceId?: string) => {
    setPaymentFormError(null);
    setSelectedInvoiceId(invoiceId || (invoices[0]?.id ?? ""));
    const inv = invoices.find((i) => i.id === (invoiceId || invoices[0]?.id));
    setPaymentAmount(inv ? inv.outstanding_balance : "");
    setPaymentMethod("bank_transfer");
    setExternalRef("");
    setPaymentNotes("");
    setIsRecordModalOpen(true);
  };

  const handleRecordPaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPaymentFormError(null);
    setSubmittingPayment(true);

    try {
      const idempotencyKey = `pay-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      await api.finance.recordPayment({
        invoice_id: selectedInvoiceId,
        amount: parseFloat(paymentAmount),
        method: paymentMethod,
        idempotency_key: idempotencyKey,
        external_reference: externalRef,
        notes: paymentNotes,
      });

      setIsRecordModalOpen(false);
      await fetchData();
    } catch (err: any) {
      setPaymentFormError(err.message || "Failed to record payment.");
    } finally {
      setSubmittingPayment(false);
    }
  };

  const handleReversePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reversalTarget) return;
    setReversalError(null);
    setSubmittingReversal(true);

    try {
      await api.finance.reversePayment(reversalTarget.id, reversalReason);
      setReversalTarget(null);
      setReversalReason("");
      await fetchData();
    } catch (err: any) {
      setReversalError(err.message || "Failed to reverse payment.");
    } finally {
      setSubmittingReversal(false);
    }
  };

  const selectedInvoice = invoices.find((i) => i.id === selectedInvoiceId);

  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Top Header & Quick Action */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "32px", fontWeight: 300, letterSpacing: "-1px", color: "#eeeeee" }}>
            Financial Operations & Reporting
          </h1>
          <p style={{ color: "#afafaf", fontSize: "14px", marginTop: "4px" }}>
            Real-time reconcilable subscription KPIs, payment allocations, and audited ledger.
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <button onClick={fetchData} className="btn-secondary" disabled={loading} title="Refresh Data">
            <RefreshCw size={14} /> {loading ? "Updating..." : "Refresh"}
          </button>
          <button onClick={() => handleOpenRecordPayment()} className="btn-yellow">
            <PlusCircle size={16} /> Record Payment
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: "rgba(255, 77, 77, 0.15)", border: "1px solid #ff4d4d", borderRadius: "6px", padding: "14px 18px", color: "#ff4d4d", marginBottom: "24px", fontSize: "14px" }}>
          {error}
        </div>
      )}

      {/* 7 PRD Metrics Grid (§7.13) */}
      {metrics && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(165px, 1fr))", gap: "16px", marginBottom: "32px" }}>
          {/* 1. Active Subscriptions */}
          <div className="card-carbon">
            <div style={{ display: "flex", justifyContent: "space-between", color: "#afafaf", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              <span>Active Subs</span>
              <Layers size={14} color="#fff313" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 300, color: "#eeeeee", marginTop: "8px" }}>
              {metrics.active_subscriptions}
            </div>
            <div style={{ fontSize: "11px", color: "#888888", marginTop: "4px" }}>
              Includes paused
            </div>
          </div>

          {/* 2. Running Subscriptions */}
          <div className="card-carbon">
            <div style={{ display: "flex", justifyContent: "space-between", color: "#afafaf", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              <span>Running Subs</span>
              <Activity size={14} color="#00e676" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 300, color: "#00e676", marginTop: "8px" }}>
              {metrics.running_subscriptions}
            </div>
            <div style={{ fontSize: "11px", color: "#888888", marginTop: "4px" }}>
              Excludes paused
            </div>
          </div>

          {/* 3. Billed Amount */}
          <div className="card-carbon">
            <div style={{ display: "flex", justifyContent: "space-between", color: "#afafaf", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              <span>Billed Amount</span>
              <FileText size={14} color="#fff313" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 300, color: "#eeeeee", marginTop: "8px" }}>
              ₹{parseFloat(metrics.billed_amount).toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#888888", marginTop: "4px" }}>
              Confirmed & Paid
            </div>
          </div>

          {/* 4. Cash Collected */}
          <div className="card-carbon" style={{ borderColor: "#fff313" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#fff313", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              <span>Cash Collected</span>
              <TrendingUp size={14} color="#fff313" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 600, color: "#fff313", marginTop: "8px" }}>
              ₹{parseFloat(metrics.cash_collected).toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#afafaf", marginTop: "4px" }}>
              Net of reversals
            </div>
          </div>

          {/* 5. Outstanding Balance */}
          <div className="card-carbon">
            <div style={{ display: "flex", justifyContent: "space-between", color: "#afafaf", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              <span>Outstanding</span>
              <DollarSign size={14} color="#eeeeee" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 300, color: "#eeeeee", marginTop: "8px" }}>
              ₹{parseFloat(metrics.outstanding_balance).toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#888888", marginTop: "4px" }}>
              Total receivables
            </div>
          </div>

          {/* 6. Overdue Balance */}
          <div className="card-carbon" style={{ borderColor: metrics.overdue_balance > 0 ? "#ff4d4d" : "#4b4b4b" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#ff4d4d", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              <span>Overdue Debt</span>
              <AlertCircle size={14} color="#ff4d4d" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 300, color: "#ff4d4d", marginTop: "8px" }}>
              ₹{parseFloat(metrics.overdue_balance).toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#888888", marginTop: "4px" }}>
              Due date passed
            </div>
          </div>

          {/* 7. Overdue Count */}
          <div className="card-carbon" style={{ borderColor: metrics.overdue_invoice_count > 0 ? "#ff4d4d" : "#4b4b4b" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#ff4d4d", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              <span>Overdue Count</span>
              <Clock size={14} color="#ff4d4d" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 300, color: "#ff4d4d", marginTop: "8px" }}>
              {metrics.overdue_invoice_count}
            </div>
            <div style={{ fontSize: "11px", color: "#888888", marginTop: "4px" }}>
              Invoices delayed
            </div>
          </div>
        </div>
      )}

      {/* Date Filter Bar */}
      <div style={{ background: "#1a1a1a", border: "1px solid #333333", borderRadius: "9px", padding: "14px 20px", display: "flex", alignItems: "center", gap: "16px", marginBottom: "28px", flexWrap: "wrap" }}>
        <span style={{ fontSize: "12px", color: "#afafaf", textTransform: "uppercase", letterSpacing: "0.5px" }}>Filters:</span>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <label style={{ fontSize: "12px", color: "#888888" }}>From:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{ background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "4px", padding: "4px 8px", fontSize: "12px" }}
          />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <label style={{ fontSize: "12px", color: "#888888" }}>To:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{ background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "4px", padding: "4px 8px", fontSize: "12px" }}
          />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <label style={{ fontSize: "12px", color: "#888888" }}>Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "4px", padding: "4px 8px", fontSize: "12px" }}
          >
            <option value="">All Statuses</option>
            <option value="confirmed">Confirmed / Unpaid</option>
            <option value="partially_paid">Partially Paid</option>
            <option value="paid">Paid</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        {(startDate || endDate || statusFilter) && (
          <button
            onClick={() => { setStartDate(""); setEndDate(""); setStatusFilter(""); }}
            style={{ background: "transparent", border: "none", color: "#fff313", fontSize: "12px", cursor: "pointer", textDecoration: "underline" }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: "flex", gap: "16px", borderBottom: "1px solid #333333", marginBottom: "24px" }}>
        <button
          onClick={() => setActiveTab("invoices")}
          style={{
            background: "transparent",
            border: "none",
            borderBottom: activeTab === "invoices" ? "2px solid #fff313" : "2px solid transparent",
            color: activeTab === "invoices" ? "#fff313" : "#afafaf",
            padding: "10px 16px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Invoices & Receivables ({invoices.length})
        </button>
        <button
          onClick={() => setActiveTab("payments")}
          style={{
            background: "transparent",
            border: "none",
            borderBottom: activeTab === "payments" ? "2px solid #fff313" : "2px solid transparent",
            color: activeTab === "payments" ? "#fff313" : "#afafaf",
            padding: "10px 16px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Payments Ledger ({payments.length})
        </button>
      </div>

      {/* Tab 1: Invoices Table */}
      {activeTab === "invoices" && (
        <div className="card-carbon" style={{ padding: "0", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#222222", borderBottom: "1px solid #333333", color: "#afafaf", textTransform: "uppercase", fontSize: "11px", letterSpacing: "0.5px" }}>
                <th style={{ padding: "12px 16px" }}>Invoice #</th>
                <th style={{ padding: "12px 16px" }}>Issue Date</th>
                <th style={{ padding: "12px 16px" }}>Due Date</th>
                <th style={{ padding: "12px 16px" }}>Status</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Total</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Balance Due</th>
                <th style={{ padding: "12px 16px", textAlign: "center" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} style={{ borderBottom: "1px solid #2a2a2a" }}>
                  <td style={{ padding: "12px 16px", fontWeight: 600, color: "#eeeeee" }}>
                    {inv.invoice_number}
                  </td>
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
                    {parseFloat(inv.outstanding_balance) > 0 ? (
                      <button
                        onClick={() => handleOpenRecordPayment(inv.id)}
                        className="btn-yellow"
                        style={{ padding: "4px 10px", fontSize: "11px" }}
                      >
                        Record Payment
                      </button>
                    ) : (
                      <span style={{ fontSize: "12px", color: "#00e676" }}>Fully Settled</span>
                    )}
                  </td>
                </tr>
              ))}
              {invoices.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ padding: "32px", textAlign: "center", color: "#888888" }}>
                    No invoices found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Payments Ledger Table */}
      {activeTab === "payments" && (
        <div className="card-carbon" style={{ padding: "0", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#222222", borderBottom: "1px solid #333333", color: "#afafaf", textTransform: "uppercase", fontSize: "11px", letterSpacing: "0.5px" }}>
                <th style={{ padding: "12px 16px" }}>Date</th>
                <th style={{ padding: "12px 16px" }}>Invoice #</th>
                <th style={{ padding: "12px 16px" }}>Customer</th>
                <th style={{ padding: "12px 16px" }}>Method</th>
                <th style={{ padding: "12px 16px" }}>Reference</th>
                <th style={{ padding: "12px 16px", textAlign: "right" }}>Amount</th>
                <th style={{ padding: "12px 16px" }}>Status</th>
                <th style={{ padding: "12px 16px", textAlign: "center" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #2a2a2a", opacity: p.is_reversed ? 0.6 : 1 }}>
                  <td style={{ padding: "12px 16px", color: "#afafaf" }}>
                    {new Date(p.paid_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: "12px 16px", fontWeight: 600, color: "#eeeeee" }}>
                    {p.invoice_number}
                  </td>
                  <td style={{ padding: "12px 16px", color: "#eeeeee" }}>{p.customer_name}</td>
                  <td style={{ padding: "12px 16px", color: "#afafaf", textTransform: "capitalize" }}>
                    {p.method.replace("_", " ")}
                  </td>
                  <td style={{ padding: "12px 16px", color: "#888888" }}>
                    {p.external_reference || "—"}
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "right", fontWeight: 600, color: p.is_reversed ? "#ff4d4d" : "#00e676" }}>
                    {p.is_reversed ? "-" : "+"}₹{parseFloat(p.amount).toLocaleString()}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className={`badge ${p.is_reversed ? "badge-unpaid" : "badge-paid"}`}>
                      {p.is_reversed ? "REVERSED" : p.status}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "center" }}>
                    {!p.is_reversed ? (
                      <button
                        onClick={() => { setReversalTarget(p); setReversalReason(""); setReversalError(null); }}
                        className="btn-secondary"
                        style={{ padding: "4px 8px", fontSize: "11px", color: "#ff4d4d", borderColor: "#662222" }}
                        title="Audited payment reversal"
                      >
                        <RotateCcw size={12} /> Reverse
                      </button>
                    ) : (
                      <span style={{ fontSize: "11px", color: "#888888" }} title={p.reversal_reason}>
                        Reversed: {p.reversal_reason || "Audited"}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {payments.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: "32px", textAlign: "center", color: "#888888" }}>
                    No payments recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal: Record Payment */}
      {isRecordModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px", color: "#eeeeee" }}>
              Record Payment
            </h2>
            <form onSubmit={handleRecordPaymentSubmit}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "6px" }}>
                  Target Invoice
                </label>
                <select
                  value={selectedInvoiceId}
                  onChange={(e) => {
                    setSelectedInvoiceId(e.target.value);
                    const inv = invoices.find((i) => i.id === e.target.value);
                    if (inv) setPaymentAmount(inv.outstanding_balance);
                  }}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                  required
                >
                  {invoices.map((inv) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoice_number} — Due: ₹{parseFloat(inv.outstanding_balance).toLocaleString()} ({inv.status})
                    </option>
                  ))}
                </select>
                {selectedInvoice && (
                  <div style={{ fontSize: "12px", color: "#fff313", marginTop: "4px" }}>
                    Max allowable payment: ₹{parseFloat(selectedInvoice.outstanding_balance).toLocaleString()}
                  </div>
                )}
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "6px" }}>
                  Payment Amount (INR)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max={selectedInvoice ? selectedInvoice.outstanding_balance : undefined}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "14px", fontWeight: 600 }}
                  required
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "6px" }}>
                  Payment Method
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                >
                  <option value="bank_transfer">Bank Transfer / NEFT / RTGS</option>
                  <option value="upi">UPI</option>
                  <option value="credit_card">Credit Card</option>
                  <option value="debit_card">Debit Card</option>
                  <option value="cheque">Cheque</option>
                  <option value="cash">Cash</option>
                </select>
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "6px" }}>
                  External Reference (UTR / Cheque # / Txn ID)
                </label>
                <input
                  type="text"
                  placeholder="e.g. UTR-HDFC-991823"
                  value={externalRef}
                  onChange={(e) => setExternalRef(e.target.value)}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                />
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "6px" }}>
                  Notes (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Part payment per agreement"
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                />
              </div>

              {paymentFormError && (
                <div style={{ background: "rgba(255, 77, 77, 0.2)", border: "1px solid #ff4d4d", borderRadius: "4px", padding: "8px 12px", color: "#ff4d4d", fontSize: "12px", marginBottom: "16px" }}>
                  {paymentFormError}
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setIsRecordModalOpen(false)}
                  className="btn-secondary"
                  disabled={submittingPayment}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-yellow"
                  disabled={submittingPayment}
                >
                  {submittingPayment ? "Allocating..." : "Confirm & Allocate"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Audited Reversal */}
      {reversalTarget && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ borderColor: "#ff4d4d" }}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "8px", color: "#ff4d4d" }}>
              Audited Payment Reversal
            </h2>
            <p style={{ fontSize: "13px", color: "#afafaf", marginBottom: "16px" }}>
              You are about to reverse payment of <strong>₹{parseFloat(reversalTarget.amount).toLocaleString()}</strong> on invoice <strong>{reversalTarget.invoice_number}</strong>. This will restore the invoice balance and update status.
            </p>

            <form onSubmit={handleReversePaymentSubmit}>
              <div style={{ marginBottom: "18px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "#eeeeee", marginBottom: "6px" }}>
                  Mandatory Reversal Reason (Audit Log)
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Bank bounced payment due to signature mismatch or incorrect entry"
                  value={reversalReason}
                  onChange={(e) => setReversalReason(e.target.value)}
                  style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
                />
              </div>

              {reversalError && (
                <div style={{ background: "rgba(255, 77, 77, 0.2)", border: "1px solid #ff4d4d", borderRadius: "4px", padding: "8px 12px", color: "#ff4d4d", fontSize: "12px", marginBottom: "16px" }}>
                  {reversalError}
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setReversalTarget(null)}
                  className="btn-secondary"
                  disabled={submittingReversal}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ background: "#ff4d4d", color: "#ffffff", border: "none", padding: "8px 16px", borderRadius: "6px", fontWeight: 600, fontSize: "13px", cursor: "pointer" }}
                  disabled={submittingReversal}
                >
                  {submittingReversal ? "Reversing..." : "Confirm Reversal"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
