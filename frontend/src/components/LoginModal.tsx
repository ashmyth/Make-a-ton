import React, { useState } from "react";
import type { User } from "../api";
import { api } from "../api";
import { Check, X, ArrowRight } from "lucide-react";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [mode, setMode] = useState<"signin" | "register" | "forgot">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const hasMinLength = password.length >= 9;
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  const isPasswordValid = hasMinLength && hasUppercase && hasLowercase && hasSpecial;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === "signin") {
        const user = await api.auth.login({ email, password });
        onSuccess(user);
        onClose();
      } else if (mode === "register") {
        if (!isPasswordValid) {
          setError("Password does not meet all required security criteria.");
          setLoading(false);
          return;
        }
        if (password !== confirmPassword) {
          setError("Passwords do not match.");
          setLoading(false);
          return;
        }

        const user = await api.auth.login({ email, password });
        onSuccess(user);
        onClose();
      } else if (mode === "forgot") {
        setSuccessMsg("If that email is registered, a password reset link is on its way.");
      }
    } catch (err: any) {
      setError(err?.message || "An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
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
        padding: "20px",
      }}
    >
      <div
        className="monad-card"
        style={{
          width: "100%",
          maxWidth: "440px",
          backgroundColor: "#ffffff",
          boxShadow: "0 20px 40px rgba(0,0,0,0.06)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
          <div>
            <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", letterSpacing: "0.05em" }}>
              Brightloop Access
            </span>
            <h2 className="font-serif" style={{ fontSize: "28px", margin: "4px 0 0 0" }}>
              {mode === "signin" && "Sign In"}
              {mode === "register" && "Create Account"}
              {mode === "forgot" && "Reset Password"}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              color: "var(--color-smoke)",
              padding: "4px",
            }}
          >
            <X size={18} />
          </button>
        </div>

        {mode !== "forgot" && (
          <div
            style={{
              display: "flex",
              borderBottom: "1px solid var(--color-ash)",
              marginBottom: "20px",
            }}
          >
            <button
              onClick={() => { setMode("signin"); setError(null); }}
              style={{
                flex: 1,
                padding: "8px 0",
                background: "none",
                border: "none",
                borderBottom: mode === "signin" ? "2px solid var(--color-off-black)" : "none",
                color: mode === "signin" ? "var(--color-off-black)" : "var(--color-smoke)",
                fontWeight: 500,
                fontSize: "12px",
                textTransform: "uppercase",
                cursor: "pointer",
              }}
            >
              Sign In
            </button>
            <button
              onClick={() => { setMode("register"); setError(null); }}
              style={{
                flex: 1,
                padding: "8px 0",
                background: "none",
                border: "none",
                borderBottom: mode === "register" ? "2px solid var(--color-off-black)" : "none",
                color: mode === "register" ? "var(--color-off-black)" : "var(--color-smoke)",
                fontWeight: 500,
                fontSize: "12px",
                textTransform: "uppercase",
                cursor: "pointer",
              }}
            >
              Register
            </button>
          </div>
        )}

        {error && (
          <div
            style={{
              backgroundColor: "#fee2e2",
              border: "1px solid #fecaca",
              color: "#991b1b",
              borderRadius: "8px",
              padding: "10px 14px",
              fontSize: "12px",
              marginBottom: "16px",
            }}
          >
            {error}
          </div>
        )}

        {successMsg && (
          <div
            style={{
              backgroundColor: "#e8f9ee",
              border: "1px solid #bbf7d0",
              color: "#166534",
              borderRadius: "8px",
              padding: "10px 14px",
              fontSize: "12px",
              marginBottom: "16px",
            }}
          >
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {mode === "register" && (
            <>
              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Aisha Patel"
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-ash)",
                    fontSize: "13px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Company Name (Optional)
                </label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Acme Technologies Ltd"
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-ash)",
                    fontSize: "13px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </>
          )}

          <div>
            <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              style={{
                width: "100%",
                padding: "9px 12px",
                borderRadius: "6px",
                border: "1px solid var(--color-ash)",
                fontSize: "13px",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
          </div>

          {mode !== "forgot" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
                  Password
                </label>
                {mode === "signin" && (
                  <button
                    type="button"
                    onClick={() => { setMode("forgot"); setError(null); }}
                    style={{ background: "none", border: "none", color: "var(--color-smoke)", fontSize: "11px", cursor: "pointer", padding: 0 }}
                  >
                    Forgot Password?
                  </button>
                )}
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--color-ash)",
                  fontSize: "13px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          {mode === "register" && (
            <div>
              <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                Confirm Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--color-ash)",
                  fontSize: "13px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          {mode === "register" && (
            <div
              style={{
                backgroundColor: "var(--color-parchment)",
                padding: "10px 14px",
                borderRadius: "8px",
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                fontSize: "11px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: hasMinLength ? "#166534" : "var(--color-smoke)" }}>
                {hasMinLength ? <Check size={12} /> : <span style={{ width: "12px", height: "12px", borderRadius: "50%", border: "1px solid var(--color-ash)", display: "inline-block" }} />}
                <span>At least 9 characters</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: hasUppercase ? "#166534" : "var(--color-smoke)" }}>
                {hasUppercase ? <Check size={12} /> : <span style={{ width: "12px", height: "12px", borderRadius: "50%", border: "1px solid var(--color-ash)", display: "inline-block" }} />}
                <span>An uppercase letter</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: hasLowercase ? "#166534" : "var(--color-smoke)" }}>
                {hasLowercase ? <Check size={12} /> : <span style={{ width: "12px", height: "12px", borderRadius: "50%", border: "1px solid var(--color-ash)", display: "inline-block" }} />}
                <span>A lowercase letter</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: hasSpecial ? "#166534" : "var(--color-smoke)" }}>
                {hasSpecial ? <Check size={12} /> : <span style={{ width: "12px", height: "12px", borderRadius: "50%", border: "1px solid var(--color-ash)", display: "inline-block" }} />}
                <span>A special character (!@#$%...)</span>
              </div>
            </div>
          )}

          <div style={{ marginTop: "10px" }}>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary-blue"
              style={{ width: "100%", justifyContent: "center", padding: "12px" }}
            >
              <span>
                {loading
                  ? "Processing..."
                  : mode === "signin"
                  ? "Sign In"
                  : mode === "register"
                  ? "Complete Registration"
                  : "Send Reset Link"}
              </span>
              <ArrowRight size={14} />
            </button>
          </div>

          {mode === "forgot" && (
            <div style={{ textAlign: "center", marginTop: "10px" }}>
              <button
                type="button"
                onClick={() => { setMode("signin"); setError(null); }}
                style={{ background: "none", border: "none", color: "var(--color-smoke)", fontSize: "12px", cursor: "pointer" }}
              >
                ← Return to Sign In
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};
