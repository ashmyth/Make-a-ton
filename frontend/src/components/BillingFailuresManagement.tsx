import React, { useState } from "react";
import { RefreshCw } from "lucide-react";

interface FailureItem {
  id: string;
  subscription: string;
  customer: string;
  period: string;
  error: string;
  tries: number;
  when: string;
  status: "OPEN" | "RESOLVED";
}

export const BillingFailuresManagement: React.FC = () => {
  const [failures, setFailures] = useState<FailureItem[]>([
    {
      id: "f-1",
      subscription: "SUB-0044",
      customer: "Zed Co",
      period: "Oct 1 - Oct 31",
      error: "No active tax rule found for customer jurisdiction (EU)",
      tries: 3,
      when: "31 Oct 02:00",
      status: "OPEN",
    },
    {
      id: "f-2",
      subscription: "SUB-0071",
      customer: "Foo Inc",
      period: "Oct 1 - Oct 31",
      error: "Target plan was archived before snapshot capture",
      tries: 1,
      when: "31 Oct 02:00",
      status: "OPEN",
    },
  ]);

  const [retryingId, setRetryingId] = useState<string | null>(null);

  const handleRetry = (id: string) => {
    setRetryingId(id);
    setTimeout(() => {
      setFailures(
        failures.map((f) => (f.id === id ? { ...f, status: "RESOLVED" } : f))
      );
      setRetryingId(null);
    }, 800);
  };

  const handleRetryAll = () => {
    setRetryingId("all");
    setTimeout(() => {
      setFailures(failures.map((f) => ({ ...f, status: "RESOLVED" })));
      setRetryingId(null);
    }, 1000);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Billing Engine Diagnostics & Recovery
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Billing Failures & Runs
          </h1>
        </div>
        <button
          onClick={handleRetryAll}
          disabled={retryingId !== null}
          className="btn-primary-blue"
        >
          <RefreshCw size={14} className={retryingId ? "animate-spin" : ""} />
          <span>Retry All Open Failures</span>
        </button>
      </div>

      {/* Latest Runs Strip */}
      <div
        className="monad-card"
        style={{
          marginBottom: "24px",
          backgroundColor: "#ffffff",
          padding: "16px 20px",
        }}
      >
        <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "8px" }}>
          Recent Scheduled Billing Runs
        </span>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "16px", fontSize: "12px" }}>
          <div>
            <span style={{ color: "var(--color-smoke)" }}>Run Timestamp:</span>
            <div style={{ fontWeight: 600 }}>31 Oct 02:00 UTC</div>
          </div>
          <div>
            <span style={{ color: "var(--color-smoke)" }}>Subscriptions Due:</span>
            <div style={{ fontWeight: 600 }}>142 due</div>
          </div>
          <div>
            <span style={{ color: "var(--color-smoke)" }}>Invoices Generated:</span>
            <div style={{ fontWeight: 600, color: "#166534" }}>140 success</div>
          </div>
          <div>
            <span style={{ color: "var(--color-smoke)" }}>Failures / Retries:</span>
            <div style={{ fontWeight: 600, color: "#991b1b" }}>2 open failures</div>
          </div>
        </div>
      </div>

      {/* Failures Table */}
      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>SUBSCRIPTION</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CUSTOMER</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>PERIOD</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ERROR REASON</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>TRIES</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>WHEN</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {failures.map((f) => (
              <tr key={f.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{f.subscription}</td>
                <td style={{ padding: "14px 16px", fontWeight: 500 }}>{f.customer}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{f.period}</td>
                <td style={{ padding: "14px 16px", color: "#991b1b" }}>{f.error}</td>
                <td style={{ padding: "14px 16px" }}>{f.tries}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{f.when}</td>
                <td style={{ padding: "14px 16px" }}>
                  <span className={`badge-pill ${f.status === "OPEN" ? "badge-overdue" : "badge-active"}`}>
                    {f.status}
                  </span>
                </td>
                <td style={{ padding: "14px 16px", textAlign: "right" }}>
                  {f.status === "OPEN" ? (
                    <button
                      onClick={() => handleRetry(f.id)}
                      disabled={retryingId === f.id}
                      className="btn-ghost"
                      style={{ padding: "4px 12px", fontSize: "11px" }}
                    >
                      {retryingId === f.id ? "Retrying..." : "Retry"}
                    </button>
                  ) : (
                    <span style={{ fontSize: "11px", color: "#166534" }}>Resolved</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
