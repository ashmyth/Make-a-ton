import React, { useState } from "react";
import { Plus, X, Check } from "lucide-react";

interface QuoteLine {
  id: string;
  product: string;
  variant: string;
  qty: number;
  unit_price: string;
  tax: string;
  amount: string;
}

interface Quotation {
  id: string;
  number: string;
  customer: string;
  plan: string;
  total: string;
  issued: string;
  expires: string;
  status: "DRAFT" | "CONFIRMED" | "EXPIRED";
  lines: QuoteLine[];
}

interface QuotationsManagementProps {
  initialTab?: "quotations" | "templates";
}

export const QuotationsManagement: React.FC<QuotationsManagementProps> = ({ initialTab = "quotations" }) => {
  const [activeTab, setActiveTab] = useState<"quotations" | "templates">(initialTab);
  const [quotations, setQuotations] = useState<Quotation[]>([
    {
      id: "q-1",
      number: "Q-0231",
      customer: "Acme Corporation",
      plan: "Pro Monthly",
      total: "17,054.00",
      issued: "2026-10-28",
      expires: "2026-11-15",
      status: "DRAFT",
      lines: [
        { id: "l-1", product: "Cloud SaaS Platform Seat", variant: "Odoo", qty: 10, unit_price: "1560.00", tax: "18%", amount: "18408.00" },
      ],
    },
    {
      id: "q-2",
      number: "Q-0230",
      customer: "Bright Tech Inc",
      plan: "Annual Enterprise Saver",
      total: "8,500.00",
      issued: "2026-10-20",
      expires: "2026-11-05",
      status: "CONFIRMED",
      lines: [
        { id: "l-2", product: "Dedicated High-Throughput Node", variant: "None", qty: 1, unit_price: "8500.00", tax: "0%", amount: "8500.00" },
      ],
    },
  ]);

  const [selectedQuote, setSelectedQuote] = useState<Quotation | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  // Quote Builder State
  const [customer, setCustomer] = useState("Acme Corporation");
  const [plan, setPlan] = useState("Pro Monthly");
  const [lines, setLines] = useState<QuoteLine[]>([
    { id: "l-1", product: "Cloud SaaS Platform Seat", variant: "Odoo", qty: 10, unit_price: "1560.00", tax: "18%", amount: "18408.00" },
    { id: "l-2", product: "Enterprise 24/7 SLA Support", variant: "Gold", qty: 1, unit_price: "1000.00", tax: "18%", amount: "1180.00" },
  ]);

  const handleOpenNew = () => {
    setSelectedQuote(null);
    setIsEditorOpen(true);
  };

  const handleOpenEdit = (q: Quotation) => {
    setSelectedQuote(q);
    setCustomer(q.customer);
    setPlan(q.plan);
    setLines(q.lines);
    setIsEditorOpen(true);
  };

  const handleAddLine = () => {
    setLines([
      ...lines,
      {
        id: `l-${Date.now()}`,
        product: "Dedicated High-Throughput Node",
        variant: "None",
        qty: 1,
        unit_price: "2400.00",
        tax: "18%",
        amount: "2832.00",
      },
    ]);
  };

  const handleConfirmQuote = () => {
    if (selectedQuote) {
      setQuotations(
        quotations.map((q) => (q.id === selectedQuote.id ? { ...q, status: "CONFIRMED" } : q))
      );
    }
    setIsEditorOpen(false);
  };

  return (
    <div>
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Commercial Proposals
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            {activeTab === "quotations" ? "Quotations" : "Quotation Templates"}
          </h1>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <div
            style={{
              display: "inline-flex",
              backgroundColor: "#ffffff",
              border: "1px solid var(--color-ash)",
              borderRadius: "9999px",
              padding: "3px",
            }}
          >
            <button
              onClick={() => setActiveTab("quotations")}
              style={{
                padding: "6px 14px",
                borderRadius: "9999px",
                fontSize: "11px",
                textTransform: "uppercase",
                fontWeight: 500,
                border: "none",
                cursor: "pointer",
                backgroundColor: activeTab === "quotations" ? "var(--color-off-black)" : "transparent",
                color: activeTab === "quotations" ? "#ffffff" : "var(--color-graphite)",
              }}
            >
              Quotations
            </button>
            <button
              onClick={() => setActiveTab("templates")}
              style={{
                padding: "6px 14px",
                borderRadius: "9999px",
                fontSize: "11px",
                textTransform: "uppercase",
                fontWeight: 500,
                border: "none",
                cursor: "pointer",
                backgroundColor: activeTab === "templates" ? "var(--color-off-black)" : "transparent",
                color: activeTab === "templates" ? "#ffffff" : "var(--color-graphite)",
              }}
            >
              Templates
            </button>
          </div>
          <button onClick={handleOpenNew} className="btn-primary-blue">
            <Plus size={14} />
            <span>New Quotation</span>
          </button>
        </div>
      </div>

      {/* Quotations List */}
      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>NUMBER</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CUSTOMER</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>PLAN</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>TOTAL</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ISSUED</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>EXPIRES</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}></th>
            </tr>
          </thead>
          <tbody>
            {quotations.map((q) => (
              <tr
                key={q.id}
                style={{ borderBottom: "1px solid var(--color-ash)", cursor: "pointer" }}
                onClick={() => handleOpenEdit(q)}
              >
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{q.number}</td>
                <td style={{ padding: "14px 16px", fontWeight: 500 }}>{q.customer}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{q.plan}</td>
                <td style={{ padding: "14px 16px" }}>
                  ${q.total.split(".")[0]}.<span className="money-decimal">{q.total.split(".")[1] || "00"}</span>
                </td>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{q.issued}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>
                  {q.expires} <span style={{ color: "#d97706", fontSize: "10px" }}>(Expires in 3 days)</span>
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <span className={`badge-pill ${q.status === "CONFIRMED" ? "badge-active" : "badge-pending"}`}>
                    {q.status}
                  </span>
                </td>
                <td style={{ padding: "14px 16px", textAlign: "right" }}>
                  <button className="btn-ghost" style={{ padding: "4px 12px", fontSize: "11px" }}>
                    View / Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Interactive Quotation Builder Fullscreen Modal */}
      {isEditorOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(36, 36, 36, 0.4)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "24px",
          }}
        >
          <div
            className="monad-card"
            style={{
              width: "100%",
              maxWidth: "960px",
              maxHeight: "90vh",
              overflowY: "auto",
              backgroundColor: "var(--color-parchment)",
              padding: "32px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
              <div>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
                  Quotation Editor
                </span>
                <h2 className="font-serif" style={{ fontSize: "32px", margin: "4px 0 0 0" }}>
                  {selectedQuote ? selectedQuote.number : "Draft Quotation Q-0232"}
                </h2>
              </div>
              <div style={{ display: "flex", gap: "10px" }}>
                <button onClick={handleConfirmQuote} className="btn-primary-blue">
                  <Check size={14} />
                  <span>Confirm Quotation</span>
                </button>
                <button onClick={() => setIsEditorOpen(false)} style={{ background: "none", border: "none", cursor: "pointer" }}>
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Header parameters */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr 1fr",
                gap: "16px",
                backgroundColor: "#ffffff",
                padding: "20px",
                borderRadius: "12px",
                border: "1px solid var(--color-ash)",
                marginBottom: "24px",
              }}
            >
              <div>
                <label style={{ fontSize: "10px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block" }}>
                  Customer
                </label>
                <select
                  value={customer}
                  onChange={(e) => setCustomer(e.target.value)}
                  style={{ width: "100%", border: "none", outline: "none", fontSize: "13px", fontWeight: 500, fontFamily: "var(--font-mono)", marginTop: "4px" }}
                >
                  <option value="Acme Corporation">Acme Corporation</option>
                  <option value="Bright Tech Inc">Bright Tech Inc</option>
                  <option value="Cyberdyne Systems">Cyberdyne Systems</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: "10px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block" }}>
                  Plan
                </label>
                <select
                  value={plan}
                  onChange={(e) => setPlan(e.target.value)}
                  style={{ width: "100%", border: "none", outline: "none", fontSize: "13px", fontWeight: 500, fontFamily: "var(--font-mono)", marginTop: "4px" }}
                >
                  <option value="Pro Monthly">Pro Monthly</option>
                  <option value="Annual Enterprise Saver">Annual Enterprise Saver</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: "10px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block" }}>
                  Start Date
                </label>
                <input
                  type="date"
                  defaultValue="2026-11-01"
                  style={{ width: "100%", border: "none", outline: "none", fontSize: "12px", fontFamily: "var(--font-mono)", marginTop: "4px" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "10px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block" }}>
                  Payment Terms
                </label>
                <select
                  defaultValue="Net 30"
                  style={{ width: "100%", border: "none", outline: "none", fontSize: "13px", fontWeight: 500, fontFamily: "var(--font-mono)", marginTop: "4px" }}
                >
                  <option value="Net 30">Net 30 Days</option>
                  <option value="Immediate">Immediate</option>
                  <option value="Net 15">Net 15 Days</option>
                </select>
              </div>
            </div>

            {/* Line items table */}
            <div style={{ marginBottom: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <span style={{ fontSize: "12px", fontWeight: 600, textTransform: "uppercase" }}>Line Items & Products</span>
                <button onClick={handleAddLine} className="btn-ghost" style={{ padding: "4px 12px", fontSize: "11px" }}>
                  + Add Line
                </button>
              </div>

              <div className="monad-card" style={{ padding: 0, overflow: "hidden", backgroundColor: "#ffffff" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--color-ash)", backgroundColor: "rgba(246,243,241,0.5)" }}>
                      <th style={{ padding: "10px 14px", textAlign: "left", color: "var(--color-smoke)" }}>PRODUCT</th>
                      <th style={{ padding: "10px 14px", textAlign: "left", color: "var(--color-smoke)" }}>VARIANT</th>
                      <th style={{ padding: "10px 14px", textAlign: "center", color: "var(--color-smoke)" }}>QTY</th>
                      <th style={{ padding: "10px 14px", textAlign: "right", color: "var(--color-smoke)" }}>UNIT PRICE</th>
                      <th style={{ padding: "10px 14px", textAlign: "center", color: "var(--color-smoke)" }}>TAX</th>
                      <th style={{ padding: "10px 14px", textAlign: "right", color: "var(--color-smoke)" }}>AMOUNT</th>
                      <th style={{ width: "40px" }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {lines.map((line, idx) => (
                      <tr key={line.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                        <td style={{ padding: "12px 14px", fontWeight: 500 }}>{line.product}</td>
                        <td style={{ padding: "12px 14px", color: "var(--color-graphite)" }}>{line.variant}</td>
                        <td style={{ padding: "12px 14px", textAlign: "center" }}>{line.qty}</td>
                        <td style={{ padding: "12px 14px", textAlign: "right" }}>${line.unit_price}</td>
                        <td style={{ padding: "12px 14px", textAlign: "center" }}>{line.tax}</td>
                        <td style={{ padding: "12px 14px", textAlign: "right", fontWeight: 600 }}>${line.amount}</td>
                        <td style={{ padding: "12px 14px", textAlign: "center" }}>
                          <button
                            onClick={() => setLines(lines.filter((_, i) => i !== idx))}
                            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-smoke)" }}
                          >
                            <X size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Validation Checklist & Totals Strip */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px", alignItems: "flex-start" }}>
              <div
                style={{
                  backgroundColor: "#ffffff",
                  padding: "16px 20px",
                  borderRadius: "12px",
                  border: "1px solid var(--color-ash)",
                }}
              >
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "8px" }}>
                  Backend Preview Validation
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "11px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#166534" }}>
                    <Check size={12} />
                    <span>Minimum plan seat quantity met (≥ 1)</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#166534" }}>
                    <Check size={12} />
                    <span>Start date is before quote expiry</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#166534" }}>
                    <Check size={12} />
                    <span>Quotation active and not expired</span>
                  </div>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: "#ffffff",
                  padding: "16px 20px",
                  borderRadius: "12px",
                  border: "1px solid var(--color-ash)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  fontSize: "12px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-graphite)" }}>
                  <span>Subtotal</span>
                  <span>$15,800.00</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#166534" }}>
                  <span>Discount (WELCOME10)</span>
                  <span>-$500.00</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-graphite)" }}>
                  <span>Tax (18% GST)</span>
                  <span>+$2,754.00</span>
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontWeight: 600,
                    fontSize: "16px",
                    borderTop: "1px solid var(--color-ash)",
                    paddingTop: "8px",
                    color: "var(--color-off-black)",
                  }}
                >
                  <span>Total</span>
                  <span>
                    $17,054.<span className="money-decimal">00</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
