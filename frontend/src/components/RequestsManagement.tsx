import React, { useState } from "react";

interface CustomerRequestItem {
  id: string;
  date: string;
  customer: string;
  subscription: string;
  type: "PAUSE" | "CANCEL" | "RENEW";
  notes: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
}

export const RequestsManagement: React.FC = () => {
  const [requests, setRequests] = useState<CustomerRequestItem[]>([
    {
      id: "req-1",
      date: "2026-10-28",
      customer: "Acme Corporation",
      subscription: "SUB-0098",
      type: "PAUSE",
      notes: "Holding billing for seasonal server maintenance.",
      status: "PENDING",
    },
    {
      id: "req-2",
      date: "2026-10-29",
      customer: "Zed Co",
      subscription: "SUB-0044",
      type: "CANCEL",
      notes: "Project completed. Please terminate at cycle end.",
      status: "PENDING",
    },
    {
      id: "req-3",
      date: "2026-10-30",
      customer: "Bright Tech Inc",
      subscription: "SUB-0102",
      type: "RENEW",
      notes: "Early contract extension approval.",
      status: "PENDING",
    },
  ]);

  const [activeRequest, setActiveRequest] = useState<CustomerRequestItem | null>(null);
  const [decisionNote, setDecisionNote] = useState("");

  const handleResolve = (status: "APPROVED" | "REJECTED") => {
    if (!activeRequest) return;
    setRequests(
      requests.map((r) => (r.id === activeRequest.id ? { ...r, status } : r))
    );
    setActiveRequest(null);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Customer Operations
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Customer Requests Inbox
          </h1>
        </div>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>DATE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CUSTOMER</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>SUBSCRIPTION</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>REQUEST TYPE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CUSTOMER NOTE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}></th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{r.date}</td>
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{r.customer}</td>
                <td style={{ padding: "14px 16px" }}>{r.subscription}</td>
                <td style={{ padding: "14px 16px" }}>
                  <span className="badge-pill badge-neutral">{r.type}</span>
                </td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>"{r.notes}"</td>
                <td style={{ padding: "14px 16px" }}>
                  <span
                    className={`badge-pill ${
                      r.status === "APPROVED"
                        ? "badge-active"
                        : r.status === "PENDING"
                        ? "badge-pending"
                        : "badge-overdue"
                    }`}
                  >
                    {r.status}
                  </span>
                </td>
                <td style={{ padding: "14px 16px", textAlign: "right" }}>
                  {r.status === "PENDING" ? (
                    <button onClick={() => { setActiveRequest(r); setDecisionNote(""); }} className="btn-primary-blue" style={{ padding: "4px 12px", fontSize: "11px" }}>
                      Review
                    </button>
                  ) : (
                    <span style={{ fontSize: "11px", color: "var(--color-smoke)" }}>Resolved</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {activeRequest && (
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
          <div className="monad-card" style={{ width: "100%", maxWidth: "460px", backgroundColor: "#ffffff" }}>
            <h2 className="font-serif" style={{ fontSize: "24px", margin: "0 0 8px 0" }}>
              Review {activeRequest.type} Request
            </h2>
            <div style={{ backgroundColor: "var(--color-parchment)", padding: "12px", borderRadius: "8px", fontSize: "12px", marginBottom: "16px" }}>
              <div><strong>Customer:</strong> {activeRequest.customer}</div>
              <div><strong>Target:</strong> {activeRequest.subscription}</div>
              <div style={{ marginTop: "4px", color: "var(--color-graphite)" }}>
                <strong>Customer note:</strong> "{activeRequest.notes}"
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                Decision Note
              </label>
              <textarea
                value={decisionNote}
                onChange={(e) => setDecisionNote(e.target.value)}
                placeholder="Approved per customer confirmation call..."
                rows={2}
                style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid var(--color-ash)", boxSizing: "border-box", fontSize: "12px" }}
              />
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button onClick={() => handleResolve("APPROVED")} className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                Approve & Apply
              </button>
              <button onClick={() => handleResolve("REJECTED")} className="btn-ghost" style={{ flex: 1, justifyContent: "center", color: "#991b1b" }}>
                Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
