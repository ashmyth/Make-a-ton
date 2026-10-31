import React, { useState } from "react";
import { Plus, X } from "lucide-react";

interface Plan {
  id: string;
  code: string;
  name: string;
  interval: "MONTHLY" | "QUARTERLY" | "ANNUAL";
  min_quantity: number;
  available_from: string;
  available_to: string;
  default_payment_terms: string;
  default_unit_price: string;
  allow_pause: boolean;
  allow_renewal: boolean;
  allow_early_closure: boolean;
  auto_close_at_expiry: boolean;
  status: "ACTIVE" | "ARCHIVED";
}

export const PlansManagement: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([
    {
      id: "PLAN-001",
      code: "PLAN-PRO-M",
      name: "Pro Monthly",
      interval: "MONTHLY",
      min_quantity: 1,
      available_from: "2026-01-01",
      available_to: "2026-12-31",
      default_payment_terms: "Net 30",
      default_unit_price: "900.00",
      allow_pause: true,
      allow_renewal: true,
      allow_early_closure: true,
      auto_close_at_expiry: false,
      status: "ACTIVE",
    },
    {
      id: "PLAN-002",
      code: "PLAN-ANNUAL-SAVER",
      name: "Annual Enterprise Saver",
      interval: "ANNUAL",
      min_quantity: 5,
      available_from: "2026-01-01",
      available_to: "2026-12-31",
      default_payment_terms: "Net 30",
      default_unit_price: "8500.00",
      allow_pause: true,
      allow_renewal: true,
      allow_early_closure: false,
      auto_close_at_expiry: true,
      status: "ACTIVE",
    },
  ]);

  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);

  // Form states
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [interval, setInterval] = useState<"MONTHLY" | "QUARTERLY" | "ANNUAL">("MONTHLY");
  const [minQty, setMinQty] = useState(1);
  const [defaultPrice, setDefaultPrice] = useState("900.00");
  const [allowPause, setAllowPause] = useState(true);
  const [allowRenewal, setAllowRenewal] = useState(true);
  const [allowEarlyClosure, setAllowEarlyClosure] = useState(true);
  const [autoClose, setAutoClose] = useState(false);

  const handleOpenNew = () => {
    setSelectedPlan(null);
    setCode("");
    setName("");
    setInterval("MONTHLY");
    setMinQty(1);
    setDefaultPrice("900.00");
    setAllowPause(true);
    setAllowRenewal(true);
    setAllowEarlyClosure(true);
    setAutoClose(false);
    setIsEditorOpen(true);
  };

  const handleOpenEdit = (plan: Plan) => {
    setSelectedPlan(plan);
    setCode(plan.code);
    setName(plan.name);
    setInterval(plan.interval);
    setMinQty(plan.min_quantity);
    setDefaultPrice(plan.default_unit_price);
    setAllowPause(plan.allow_pause);
    setAllowRenewal(plan.allow_renewal);
    setAllowEarlyClosure(plan.allow_early_closure);
    setAutoClose(plan.auto_close_at_expiry);
    setIsEditorOpen(true);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedPlan) {
      setPlans(
        plans.map((p) =>
          p.id === selectedPlan.id
            ? {
                ...p,
                code,
                name,
                interval,
                min_quantity: minQty,
                default_unit_price: defaultPrice,
                allow_pause: allowPause,
                allow_renewal: allowRenewal,
                allow_early_closure: allowEarlyClosure,
                auto_close_at_expiry: autoClose,
              }
            : p
        )
      );
    } else {
      const newPlan: Plan = {
        id: `PLAN-00${plans.length + 1}`,
        code,
        name,
        interval,
        min_quantity: minQty,
        available_from: "2026-01-01",
        available_to: "2026-12-31",
        default_payment_terms: "Net 30",
        default_unit_price: defaultPrice,
        allow_pause: allowPause,
        allow_renewal: allowRenewal,
        allow_early_closure: allowEarlyClosure,
        auto_close_at_expiry: autoClose,
        status: "ACTIVE",
      };
      setPlans([...plans, newPlan]);
    }
    setIsEditorOpen(false);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Billing Cadence & Intervals
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Subscription Plans
          </h1>
        </div>
        <button onClick={handleOpenNew} className="btn-primary-blue">
          <Plus size={14} />
          <span>New Plan</span>
        </button>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CODE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>NAME</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>INTERVAL</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>MIN QTY</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>DEFAULT PRICE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>BEHAVIOR</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}></th>
            </tr>
          </thead>
          <tbody>
            {plans.map((plan) => (
              <tr
                key={plan.id}
                style={{ borderBottom: "1px solid var(--color-ash)", cursor: "pointer" }}
                onClick={() => handleOpenEdit(plan)}
              >
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{plan.code}</td>
                <td style={{ padding: "14px 16px", fontWeight: 500 }}>{plan.name}</td>
                <td style={{ padding: "14px 16px" }}>
                  <span className="badge-pill badge-neutral">{plan.interval}</span>
                </td>
                <td style={{ padding: "14px 16px" }}>{plan.min_quantity} seat(s)</td>
                <td style={{ padding: "14px 16px" }}>
                  ${plan.default_unit_price.split(".")[0]}.
                  <span className="money-decimal">{plan.default_unit_price.split(".")[1] || "00"}</span>
                </td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>
                  {plan.allow_pause && "Pause "}
                  {plan.allow_renewal && "• Renew "}
                  {plan.auto_close_at_expiry && "• Auto-close"}
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <span className="badge-pill badge-active">{plan.status}</span>
                </td>
                <td style={{ padding: "14px 16px", textAlign: "right" }}>
                  <button className="btn-ghost" style={{ padding: "4px 12px", fontSize: "11px" }}>
                    Configure
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Plan Drawer Modal */}
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
            justifyContent: "flex-end",
            zIndex: 100,
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "500px",
              backgroundColor: "var(--color-parchment)",
              height: "100%",
              boxShadow: "-10px 0 30px rgba(0,0,0,0.1)",
              padding: "32px",
              overflowY: "auto",
              boxSizing: "border-box",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
              <div>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
                  {selectedPlan ? `Configure ${selectedPlan.code}` : "Plan Definition"}
                </span>
                <h2 className="font-serif" style={{ fontSize: "28px", margin: "4px 0 0 0" }}>
                  {selectedPlan ? "Edit Plan Rules" : "Create New Plan"}
                </h2>
              </div>
              <button
                onClick={() => setIsEditorOpen(false)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-smoke)" }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Plan Code
                </label>
                <input
                  type="text"
                  required
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="e.g. PLAN-PRO-M"
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-ash)",
                    fontSize: "13px",
                    fontFamily: "var(--font-mono)",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Plan Display Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Pro Monthly Standard"
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-ash)",
                    fontSize: "13px",
                    fontFamily: "var(--font-mono)",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                    Billing Cadence
                  </label>
                  <select
                    value={interval}
                    onChange={(e: any) => setInterval(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "9px 12px",
                      borderRadius: "6px",
                      border: "1px solid var(--color-ash)",
                      fontSize: "12px",
                      fontFamily: "var(--font-mono)",
                      boxSizing: "border-box",
                    }}
                  >
                    <option value="MONTHLY">Monthly</option>
                    <option value="QUARTERLY">Quarterly</option>
                    <option value="ANNUAL">Annual</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                    Minimum Quantity
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={minQty}
                    onChange={(e) => setMinQty(parseInt(e.target.value) || 1)}
                    style={{
                      width: "100%",
                      padding: "9px 12px",
                      borderRadius: "6px",
                      border: "1px solid var(--color-ash)",
                      fontSize: "13px",
                      fontFamily: "var(--font-mono)",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Default Unit Price ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={defaultPrice}
                  onChange={(e) => setDefaultPrice(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-ash)",
                    fontSize: "13px",
                    fontFamily: "var(--font-mono)",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              {/* Lifecycle behavior toggles */}
              <div style={{ marginTop: "8px", borderTop: "1px solid var(--color-ash)", paddingTop: "14px" }}>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "8px" }}>
                  Lifecycle Behaviors
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                    <input type="checkbox" checked={allowPause} onChange={(e) => setAllowPause(e.target.checked)} />
                    <span>Allow customer & ops to pause</span>
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                    <input type="checkbox" checked={allowRenewal} onChange={(e) => setAllowRenewal(e.target.checked)} />
                    <span>Allow automatic & requested renewals</span>
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                    <input type="checkbox" checked={allowEarlyClosure} onChange={(e) => setAllowEarlyClosure(e.target.checked)} />
                    <span>Allow early contract termination</span>
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                    <input type="checkbox" checked={autoClose} onChange={(e) => setAutoClose(e.target.checked)} />
                    <span>Auto-close at end of period</span>
                  </label>
                </div>
              </div>

              <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
                <button type="submit" className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                  Save Plan
                </button>
                <button type="button" onClick={() => setIsEditorOpen(false)} className="btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
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
