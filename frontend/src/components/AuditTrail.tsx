import React, { useState } from "react";

interface AuditEntry {
  id: string;
  time: string;
  user: string;
  entity: string;
  action: string;
  change: string;
}

export const AuditTrail: React.FC = () => {
  const [logs] = useState<AuditEntry[]>([
    {
      id: "log-1",
      time: "31 Oct 11:02",
      user: "Priya (Finance)",
      entity: "INV-0412",
      action: "CONFIRMED",
      change: "status: Draft → Confirmed",
    },
    {
      id: "log-2",
      time: "31 Oct 10:55",
      user: "System",
      entity: "SUB-0098",
      action: "BILLED",
      change: "recurring run: Nov 1 - Nov 30",
    },
    {
      id: "log-3",
      time: "31 Oct 09:30",
      user: "Alice (Admin)",
      entity: "bob@brightloop.io",
      action: "ROLE_CHANGE",
      change: "role: None → OPERATIONS",
    },
    {
      id: "log-4",
      time: "30 Oct 14:15",
      user: "Priya (Finance)",
      entity: "PAY-0231",
      action: "PAYMENT_RECORD",
      change: "allocated: $3,000.00 to INV-0412",
    },
  ]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Immutable Security & Compliance
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Audit Trail
          </h1>
        </div>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>TIME (UTC)</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ACTOR</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>TARGET ENTITY</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ACTION</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CHANGE SUMMARY</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{l.time}</td>
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{l.user}</td>
                <td style={{ padding: "14px 16px", fontWeight: 500 }}>{l.entity}</td>
                <td style={{ padding: "14px 16px" }}>
                  <span className="badge-pill badge-neutral">{l.action}</span>
                </td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{l.change}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
