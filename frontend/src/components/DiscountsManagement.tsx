import React, { useState } from "react";
import { Plus, X } from "lucide-react";

interface DiscountRule {
  id: string;
  name: string;
  type: "PERCENT" | "FIXED";
  value: string;
  scope: string;
  min_criteria: string;
  valid_dates: string;
  used_count: string;
  status: "ACTIVE" | "EXPIRED";
}

export const DiscountsManagement: React.FC = () => {
  const [discounts, setDiscounts] = useState<DiscountRule[]>([
    {
      id: "DISC-001",
      name: "WELCOME10",
      type: "PERCENT",
      value: "10%",
      scope: "Subscription",
      min_criteria: "Min 5 seats",
      valid_dates: "Nov 01 - Dec 31",
      used_count: "12 / 50",
      status: "ACTIVE",
    },
    {
      id: "DISC-002",
      name: "ENTERPRISE500",
      type: "FIXED",
      value: "$500.00",
      scope: "Product",
      min_criteria: "Order > $5,000",
      valid_dates: "Open",
      used_count: "3 / ∞",
      status: "ACTIVE",
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState<"PERCENT" | "FIXED">("PERCENT");
  const [value, setValue] = useState("10");

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const newDisc: DiscountRule = {
      id: `DISC-00${discounts.length + 1}`,
      name: name.toUpperCase(),
      type,
      value: type === "PERCENT" ? `${value}%` : `$${value}`,
      scope: "Subscription",
      min_criteria: "None",
      valid_dates: "Open",
      used_count: "0 / 100",
      status: "ACTIVE",
    };
    setDiscounts([...discounts, newDisc]);
    setIsModalOpen(false);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Promotional Engine
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Discounts & Coupons
          </h1>
        </div>
        <button onClick={() => { setName(""); setIsModalOpen(true); }} className="btn-primary-blue">
          <Plus size={14} />
          <span>New Discount</span>
        </button>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CODE / NAME</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>TYPE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>VALUE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>SCOPE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CRITERIA</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>VALIDITY</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>USAGE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
            </tr>
          </thead>
          <tbody>
            {discounts.map((d) => (
              <tr key={d.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{d.name}</td>
                <td style={{ padding: "14px 16px" }}>{d.type}</td>
                <td style={{ padding: "14px 16px", fontWeight: 500 }}>{d.value}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{d.scope}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{d.min_criteria}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{d.valid_dates}</td>
                <td style={{ padding: "14px 16px" }}>{d.used_count}</td>
                <td style={{ padding: "14px 16px" }}>
                  <span className="badge-pill badge-active">{d.status}</span>
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
              <h2 className="font-serif" style={{ fontSize: "24px", margin: 0 }}>Create Discount Rule</h2>
              <button onClick={() => setIsModalOpen(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-smoke)" }}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Discount Code Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4ACCELERATE"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                    Type
                  </label>
                  <select
                    value={type}
                    onChange={(e: any) => setType(e.target.value)}
                    style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "12px" }}
                  >
                    <option value="PERCENT">Percentage (%)</option>
                    <option value="FIXED">Fixed Amount ($)</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                    Value
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                  />
                </div>
              </div>

              <div style={{ marginTop: "16px", display: "flex", gap: "12px" }}>
                <button type="submit" className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                  Save Discount
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
