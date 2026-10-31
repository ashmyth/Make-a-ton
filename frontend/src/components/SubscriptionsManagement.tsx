import React, { useState } from "react";

interface SubscriptionItem {
  id: string;
  number: string;
  customer: string;
  plan: string;
  lifecycle: "ACTIVE" | "PAUSED" | "EXPIRED" | "CANCELLED";
  run_state: "RUNNING" | "PAUSED" | "SUSPENDED";
  next_billing: string;
  expiry: string;
  amount: string;
}

export const SubscriptionsManagement: React.FC = () => {
  const [filterState, setFilterState] = useState<"ALL" | "ACTIVE" | "PAUSED" | "EXPIRED">("ALL");
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>([
    {
      id: "sub-1",
      number: "SUB-0098",
      customer: "Acme Corporation",
      plan: "Pro Monthly",
      lifecycle: "ACTIVE",
      run_state: "RUNNING",
      next_billing: "2026-11-01",
      expiry: "2026-12-31",
      amount: "1,200.00",
    },
    {
      id: "sub-2",
      number: "SUB-0102",
      customer: "Acme Corporation",
      plan: "Add-on Pack",
      lifecycle: "ACTIVE",
      run_state: "PAUSED",
      next_billing: "—",
      expiry: "2026-12-31",
      amount: "250.00",
    },
    {
      id: "sub-3",
      number: "SUB-0044",
      customer: "Zed Co",
      plan: "Annual Enterprise Saver",
      lifecycle: "ACTIVE",
      run_state: "RUNNING",
      next_billing: "2026-12-01",
      expiry: "2026-12-31",
      amount: "8,500.00",
    },
  ]);

  const [selectedSub, setSelectedSub] = useState<SubscriptionItem | null>(null);
  const [dialogAction, setDialogAction] = useState<"pause" | "renew" | "close" | null>(null);
  const [actionReason, setActionReason] = useState("");

  const handleOpenAction = (sub: SubscriptionItem, action: "pause" | "renew" | "close") => {
    setSelectedSub(sub);
    setDialogAction(action);
    setActionReason("");
  };

  const handleConfirmAction = () => {
    if (!selectedSub || !dialogAction) return;

    setSubscriptions(
      subscriptions.map((s) => {
        if (s.id === selectedSub.id) {
          if (dialogAction === "pause") {
            return { ...s, run_state: "PAUSED" };
          } else if (dialogAction === "renew") {
            return { ...s, expiry: "2027-12-31" };
          } else if (dialogAction === "close") {
            return { ...s, lifecycle: "EXPIRED", run_state: "SUSPENDED" };
          }
        }
        return s;
      })
    );
    setDialogAction(null);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Lifecycle Operations
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Active Subscriptions
          </h1>
        </div>
        <div
          style={{
            display: "inline-flex",
            backgroundColor: "#ffffff",
            border: "1px solid var(--color-ash)",
            borderRadius: "9999px",
            padding: "3px",
          }}
        >
          {(["ALL", "ACTIVE", "PAUSED", "EXPIRED"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilterState(tab)}
              style={{
                padding: "6px 14px",
                borderRadius: "9999px",
                fontSize: "11px",
                textTransform: "uppercase",
                fontWeight: 500,
                border: "none",
                cursor: "pointer",
                backgroundColor: filterState === tab ? "var(--color-off-black)" : "transparent",
                color: filterState === tab ? "#ffffff" : "var(--color-graphite)",
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>NUMBER</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CUSTOMER</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>PLAN</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>RUN STATE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>NEXT BILLING</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>EXPIRY</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>AMOUNT / PERIOD</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {subscriptions
              .filter((s) => (filterState === "ALL" ? true : s.run_state === filterState || s.lifecycle === filterState))
              .map((s) => (
                <tr key={s.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                  <td style={{ padding: "14px 16px", fontWeight: 600 }}>{s.number}</td>
                  <td style={{ padding: "14px 16px", fontWeight: 500 }}>{s.customer}</td>
                  <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{s.plan}</td>
                  <td style={{ padding: "14px 16px" }}>
                    <span className={`badge-pill ${s.run_state === "RUNNING" ? "badge-active" : "badge-pending"}`}>
                      {s.run_state}
                    </span>
                  </td>
                  <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{s.next_billing}</td>
                  <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{s.expiry}</td>
                  <td style={{ padding: "14px 16px" }}>
                    ${s.amount.split(".")[0]}.<span className="money-decimal">{s.amount.split(".")[1] || "00"}</span>
                  </td>
                  <td style={{ padding: "14px 16px", textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "6px" }}>
                      {s.run_state === "RUNNING" ? (
                        <button
                          onClick={() => handleOpenAction(s, "pause")}
                          className="btn-ghost"
                          style={{ padding: "4px 8px", fontSize: "10px" }}
                        >
                          Pause
                        </button>
                      ) : (
                        <button
                          onClick={() => handleOpenAction(s, "renew")}
                          className="btn-ghost"
                          style={{ padding: "4px 8px", fontSize: "10px" }}
                        >
                          Resume
                        </button>
                      )}
                      <button
                        onClick={() => handleOpenAction(s, "renew")}
                        className="btn-ghost"
                        style={{ padding: "4px 8px", fontSize: "10px" }}
                      >
                        Renew
                      </button>
                      <button
                        onClick={() => handleOpenAction(s, "close")}
                        className="btn-ghost"
                        style={{ padding: "4px 8px", fontSize: "10px", color: "#991b1b" }}
                      >
                        Close
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Action Dialog */}
      {dialogAction && selectedSub && (
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
          <div className="monad-card" style={{ width: "100%", maxWidth: "440px", backgroundColor: "#ffffff" }}>
            <h2 className="font-serif" style={{ fontSize: "24px", margin: "0 0 12px 0" }}>
              {dialogAction === "pause" && `Pause Subscription ${selectedSub.number}?`}
              {dialogAction === "renew" && `Renew ${selectedSub.number}?`}
              {dialogAction === "close" && `Close ${selectedSub.number}?`}
            </h2>
            <p style={{ fontSize: "12px", color: "var(--color-smoke)", margin: "0 0 16px 0" }}>
              {dialogAction === "pause" && "No recurring invoices will generate while paused. Resume whenever ready."}
              {dialogAction === "renew" && "Extends subscription term and schedules the next billing run."}
              {dialogAction === "close" && "Terminates contract. Requires explicit audit reason."}
            </p>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                Reason for action
              </label>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="Required for immutable audit logging..."
                rows={2}
                style={{ width: "100%", padding: "8px", fontSize: "12px", borderRadius: "6px", border: "1px solid var(--color-ash)", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button onClick={handleConfirmAction} className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                Confirm
              </button>
              <button onClick={() => setDialogAction(null)} className="btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
