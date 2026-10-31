import React, { useState } from "react";
import { api, ApiError, type User } from "../api";
import { X } from "lucide-react";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

function formatLoginError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.fieldErrors) {
      return Object.entries(err.fieldErrors)
        .map(([f, msgs]) => `${f}: ${msgs.join(" ")}`)
        .join(" | ");
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Failed to sign in.";
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const user = await api.auth.login({ email, password });
      onSuccess(user);
      onClose();
    } catch (err: unknown) {
      setError(formatLoginError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (quickEmail: string, quickPass: string) => {
    setEmail(quickEmail);
    setPassword(quickPass);
    setLoading(true);
    setError(null);
    try {
      const user = await api.auth.login({ email: quickEmail, password: quickPass });
      onSuccess(user);
      onClose();
    } catch (err: unknown) {
      setError(formatLoginError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: "460px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ background: "#fff313", color: "#000000", fontWeight: 700, padding: "2px 6px", borderRadius: "4px", fontSize: "12px" }}>
              AUTH
            </div>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee" }}>Sign In to Brightloop</h2>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "#888888", cursor: "pointer" }}>
            <X size={18} />
          </button>
        </div>

        {error && (
          <div style={{ background: "rgba(255, 77, 77, 0.2)", border: "1px solid #ff4d4d", borderRadius: "6px", padding: "10px 14px", color: "#ff4d4d", fontSize: "12px", marginBottom: "16px" }}>
            {error}
          </div>
        )}

        {/* Quick Demo Logins */}
        <div style={{ marginBottom: "20px", background: "#111111", border: "1px solid #2a2a2a", borderRadius: "6px", padding: "12px" }}>
          <div style={{ fontSize: "11px", color: "#afafaf", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "8px" }}>
            Quick Demo Accounts:
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            <button
              type="button"
              onClick={() => handleQuickLogin("finance@brightloop.io", "FinanceSecure@123")}
              className="btn-secondary"
              style={{ fontSize: "11px", padding: "6px 8px", justifyContent: "center" }}
            >
              Finance Staff
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("admin@brightloop.io", "AdminSecure@123")}
              className="btn-secondary"
              style={{ fontSize: "11px", padding: "6px 8px", justifyContent: "center" }}
            >
              Admin Staff
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("alice@acmecorp.com", "CustomerSecure@123")}
              className="btn-secondary"
              style={{ fontSize: "11px", padding: "6px 8px", justifyContent: "center", borderColor: "#fff313", color: "#fff313" }}
            >
              Customer: Acme Corp
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("david@cloudscale.io", "CustomerSecure@123")}
              className="btn-secondary"
              style={{ fontSize: "11px", padding: "6px 8px", justifyContent: "center", borderColor: "#fff313", color: "#fff313" }}
            >
              Customer: CloudScale
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
            />
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#afafaf", marginBottom: "4px" }}>Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{ width: "100%", background: "#000000", border: "1px solid #4b4b4b", color: "#eeeeee", padding: "8px 12px", borderRadius: "6px", fontSize: "13px" }}
            />
          </div>

          <button type="submit" className="btn-yellow" style={{ width: "100%", justifyContent: "center" }} disabled={loading}>
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
};
