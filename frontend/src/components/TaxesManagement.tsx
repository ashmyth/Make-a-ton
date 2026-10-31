import React, { useState } from "react";
import { Plus, X } from "lucide-react";

interface TaxRule {
  id: string;
  name: string;
  rate: string;
  applies_to: string;
  effective_from: string;
  effective_to: string;
  status: "ACTIVE" | "ARCHIVED";
}

export const TaxesManagement: React.FC = () => {
  const [taxes, setTaxes] = useState<TaxRule[]>([
    {
      id: "TAX-001",
      name: "GST 18%",
      rate: "18.00%",
      applies_to: "All SaaS Products",
      effective_from: "2025-04-01",
      effective_to: "Open",
      status: "ACTIVE",
    },
    {
      id: "TAX-002",
      name: "Zero Rated Export",
      rate: "0.00%",
      applies_to: "International Clients",
      effective_from: "2025-04-01",
      effective_to: "Open",
      status: "ACTIVE",
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [rate, setRate] = useState("18.00");

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const newTax: TaxRule = {
      id: `TAX-00${taxes.length + 1}`,
      name,
      rate: `${rate}%`,
      applies_to: "All products",
      effective_from: "2026-01-01",
      effective_to: "Open",
      status: "ACTIVE",
    };
    setTaxes([...taxes, newTax]);
    setIsModalOpen(false);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Financial Governance
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Tax Rules
          </h1>
        </div>
        <button onClick={() => { setName(""); setIsModalOpen(true); }} className="btn-primary-blue">
          <Plus size={14} />
          <span>New Tax</span>
        </button>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>NAME</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>RATE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>APPLIES TO</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>EFFECTIVE DATES</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
            </tr>
          </thead>
          <tbody>
            {taxes.map((t) => (
              <tr key={t.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{t.name}</td>
                <td style={{ padding: "14px 16px", fontWeight: 500 }}>{t.rate}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{t.applies_to}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>
                  {t.effective_from} — {t.effective_to}
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <span className="badge-pill badge-active">{t.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
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
          }}
        >
          <div className="monad-card" style={{ width: "100%", maxWidth: "420px", backgroundColor: "#ffffff" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <h2 className="font-serif" style={{ fontSize: "24px", margin: 0 }}>Create Tax Rule</h2>
              <button onClick={() => setIsModalOpen(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-smoke)" }}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Tax Rule Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. EU VAT Standard"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Percentage Rate (%)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="18.00"
                  value={rate}
                  onChange={(e) => setRate(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div style={{ marginTop: "16px", display: "flex", gap: "12px" }}>
                <button type="submit" className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                  Save Tax Rule
                </button>
                <button type="button" onClick={() => setIsModalOpen(false)} className="btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
