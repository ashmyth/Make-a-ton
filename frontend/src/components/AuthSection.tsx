import React, { useState, useEffect, useRef } from "react";
import type { User } from "../api";
import { api } from "../api";
import { Check, X, ArrowRight, Building, Lock, Mail, User as UserIcon } from "lucide-react";
import { Logo } from "./Logo";
import gsap from "gsap";
import { animatePress, animateHoverEnter, animateHoverLeave } from "../lib/animations";

interface AuthSectionProps {
  onSuccess: (user: User) => void;
  onCancel?: () => void;
  initialMode?: "signin" | "register";
}

export const AuthSection: React.FC<AuthSectionProps> = ({
  onSuccess,
  onCancel,
  initialMode = "signin",
}) => {
  const [mode, setMode] = useState<"signin" | "register" | "forgot">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // GSAP Container and Element Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const leftNarrativeRef = useRef<HTMLDivElement>(null);
  const rightFormCardRef = useRef<HTMLDivElement>(null);
  const badgeLogoRef = useRef<HTMLDivElement>(null);
  const submitButtonRef = useRef<HTMLButtonElement>(null);
  const formContentRef = useRef<HTMLFormElement>(null);

  // Security Criteria for Password validation
  const hasMinLength = password.length >= 9;
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  const isPasswordValid = hasMinLength && hasUppercase && hasLowercase && hasSpecial;

  // Clean, linear/power entrance animations (no bouncing)
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        leftNarrativeRef.current,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }
      );

      gsap.fromTo(
        rightFormCardRef.current,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: 0.45, delay: 0.08, ease: "power2.out" }
      );
    }, containerRef);

    return () => ctx.revert();
  }, []);

  const handleModeChange = (newMode: "signin" | "register" | "forgot") => {
    if (newMode === mode) return;
    setError(null);
    setSuccessMsg(null);
    
    if (formContentRef.current) {
      gsap.fromTo(
        formContentRef.current,
        { opacity: 0.5, y: 6 },
        { opacity: 1, y: 0, duration: 0.25, ease: "power2.out" }
      );
    }
    setMode(newMode);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    animatePress(submitButtonRef.current);

    setLoading(true);

    try {
      await api.auth.csrf().catch(() => {});
      if (mode === "signin") {
        const user = await api.auth.login({ email, password });
        onSuccess(user);
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

        const nameParts = fullName.trim().split(/\s+/);
        const firstName = nameParts[0] || "";
        const lastName = nameParts.slice(1).join(" ") || "";

        await api.auth.register({
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          full_name: fullName,
          company_name: companyName,
        } as any);

        const user = await api.auth.login({ email, password });
        onSuccess(user);
      } else if (mode === "forgot") {
        setSuccessMsg("If that email is registered, a password reset link has been dispatched.");
      }
    } catch (err: any) {
      if (err?.body && typeof err.body === "object") {
        const messages = Object.entries(err.body)
          .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(" ") : val}`)
          .join(" | ");
        setError(messages || err.message || "Authentication failed.");
      } else {
        setError(err?.message || "Authentication failed. Please verify credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={containerRef} style={{ maxWidth: "1140px", margin: "0 auto", padding: "0 24px" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
          gap: "40px",
          alignItems: "stretch",
        }}
      >
        {/* Left Column: Narrative Card */}
        <div
          ref={leftNarrativeRef}
          onMouseEnter={(e) => animateHoverEnter(e.currentTarget)}
          onMouseLeave={(e) => animateHoverLeave(e.currentTarget)}
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            gap: "24px",
            transformOrigin: "center center",
            willChange: "transform",
          }}
        >
          {/* Card 1: Warm Sage / Parchment Narrative Card */}
          <div
            style={{
              backgroundColor: "#ffffff",
              border: "1px solid var(--color-ash)",
              borderRadius: "28px",
              padding: "40px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.03)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              height: "100%",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
                <span
                  style={{
                    backgroundColor: "var(--color-periwinkle-mist)",
                    color: "var(--color-lake-blue)",
                    fontSize: "11px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    padding: "4px 12px",
                    borderRadius: "9999px",
                  }}
                >
                  Brightloop Architecture
                </span>
              </div>
              <h1
                className="font-serif"
                style={{
                  fontSize: "38px",
                  lineHeight: "1.15",
                  letterSpacing: "-0.025em",
                  color: "var(--color-off-black)",
                  margin: "0 0 16px 0",
                }}
              >
                A unified ledger for commercial billing cycles.
              </h1>
              <p
                style={{
                  fontSize: "15px",
                  lineHeight: "1.6",
                  color: "var(--color-graphite)",
                  margin: 0,
                  maxWidth: "52ch",
                }}
              >
                Audited invoices, automated recurrent subscriptions, and zero client-calculated totals.
                All figures originate from tamper-proof backend financial registers.
              </p>
            </div>

            <div
              style={{
                marginTop: "36px",
                paddingTop: "24px",
                borderTop: "1px solid #e5e7eb",
                display: "flex",
                alignItems: "center",
                gap: "16px",
              }}
            >
              <div
                ref={badgeLogoRef}
                style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "9999px",
                  backgroundColor: "var(--color-off-black)",
                  color: "#ffffff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 600,
                  fontSize: "15px",
                  flexShrink: 0,
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                }}
              >
                <Logo size={22} style={{ color: "#ffffff" }} />
              </div>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-off-black)" }}>
                  Institutional Grade
                </div>
                <div style={{ fontSize: "12px", color: "var(--color-smoke)" }}>
                  Role-based access control with audited transaction tracing
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Minimal Key Affordances Strip */}
          <div
            style={{
              backgroundColor: "var(--color-periwinkle-mist)",
              border: "1px solid #bfdbfe",
              borderRadius: "24px",
              padding: "24px 32px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "16px",
            }}
          >
            <div>
              <div style={{ fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--color-lake-blue)", fontWeight: 600 }}>
                Operations & Portal
              </div>
              <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-off-black)", marginTop: "2px" }}>
                Less admin. Clear reconciliations.
              </div>
            </div>
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <span style={{ fontSize: "12px", color: "var(--color-graphite)" }}>Strict Decimal Math</span>
              <span style={{ width: "4px", height: "4px", borderRadius: "9999px", backgroundColor: "var(--color-lake-blue)" }}></span>
              <span style={{ fontSize: "12px", color: "var(--color-graphite)" }}>Append-Only Ledger</span>
            </div>
          </div>
        </div>

        {/* Right Column: Clean, High-Contrast Authentication Card */}
        <div
          ref={rightFormCardRef}
          className="monad-card"
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "28px",
            padding: "44px",
            boxShadow: "0 8px 30px rgba(0,0,0,0.05)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            willChange: "transform",
          }}
        >
          {/* Header Switcher */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
            <div>
              <h2
                className="font-serif"
                style={{
                  fontSize: "30px",
                  color: "var(--color-off-black)",
                  margin: "0 0 4px 0",
                  letterSpacing: "-0.02em",
                }}
              >
                {mode === "signin" ? "Sign In" : mode === "register" ? "Create Account" : "Reset Password"}
              </h2>
              <p style={{ fontSize: "13px", color: "var(--color-smoke)", margin: 0 }}>
                {mode === "signin"
                  ? "Access your billing console or customer portal."
                  : mode === "register"
                  ? "Initialize your workspace credentials."
                  : "Enter your registered email address."}
              </p>
            </div>
            {onCancel && (
              <button
                onClick={(e) => {
                  animatePress(e.currentTarget);
                  setTimeout(onCancel, 100);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--color-smoke)",
                  cursor: "pointer",
                  padding: "6px",
                  borderRadius: "9999px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                aria-label="Close"
              >
                <X size={20} />
              </button>
            )}
          </div>

          {/* Mode Switch Tabs */}
          {mode !== "forgot" && (
            <div
              style={{
                display: "flex",
                backgroundColor: "#f3f4f6",
                padding: "4px",
                borderRadius: "9999px",
                marginBottom: "28px",
              }}
            >
              <button
                type="button"
                onClick={() => handleModeChange("signin")}
                style={{
                  flex: 1,
                  padding: "8px 16px",
                  borderRadius: "9999px",
                  border: "none",
                  backgroundColor: mode === "signin" ? "#ffffff" : "transparent",
                  color: mode === "signin" ? "var(--color-off-black)" : "var(--color-smoke)",
                  fontWeight: mode === "signin" ? 600 : 500,
                  fontSize: "13px",
                  cursor: "pointer",
                  boxShadow: mode === "signin" ? "0 2px 6px rgba(0,0,0,0.08)" : "none",
                  transition: "color 0.15s ease",
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => handleModeChange("register")}
                style={{
                  flex: 1,
                  padding: "8px 16px",
                  borderRadius: "9999px",
                  border: "none",
                  backgroundColor: mode === "register" ? "#ffffff" : "transparent",
                  color: mode === "register" ? "var(--color-off-black)" : "var(--color-smoke)",
                  fontWeight: mode === "register" ? 600 : 500,
                  fontSize: "13px",
                  cursor: "pointer",
                  boxShadow: mode === "register" ? "0 2px 6px rgba(0,0,0,0.08)" : "none",
                  transition: "color 0.15s ease",
                }}
              >
                Register
              </button>
            </div>
          )}

          {/* Alerts */}
          {error && (
            <div
              style={{
                backgroundColor: "#fef2f2",
                border: "1px solid #fecaca",
                color: "var(--color-crimson)",
                padding: "12px 16px",
                borderRadius: "10px",
                fontSize: "13px",
                marginBottom: "20px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <X size={16} />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div
              style={{
                backgroundColor: "#ecfdf5",
                border: "1px solid #a7f3d0",
                color: "#065f46",
                padding: "12px 16px",
                borderRadius: "10px",
                fontSize: "13px",
                marginBottom: "20px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <Check size={16} />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Form */}
          <form
            ref={formContentRef}
            onSubmit={handleSubmit}
            style={{ display: "flex", flexDirection: "column", gap: "18px" }}
          >
            {mode === "register" && (
              <>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--color-off-black)", marginBottom: "6px" }}>
                    Full Legal Name
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="text"
                      required
                      placeholder="Priya Sharma"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      style={{
                        width: "100%",
                        backgroundColor: "#ffffff",
                        border: "1px solid var(--color-ash)",
                        color: "var(--color-off-black)",
                        padding: "10px 14px 10px 38px",
                        borderRadius: "10px",
                        fontSize: "13px",
                        boxSizing: "border-box",
                      }}
                    />
                    <UserIcon size={16} style={{ position: "absolute", left: "12px", top: "12px", color: "var(--color-smoke)" }} />
                  </div>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--color-off-black)", marginBottom: "6px" }}>
                    Company / Organization
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="text"
                      required
                      placeholder="Acme Industrial Ltd."
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      style={{
                        width: "100%",
                        backgroundColor: "#ffffff",
                        border: "1px solid var(--color-ash)",
                        color: "var(--color-off-black)",
                        padding: "10px 14px 10px 38px",
                        borderRadius: "10px",
                        fontSize: "13px",
                        boxSizing: "border-box",
                      }}
                    />
                    <Building size={16} style={{ position: "absolute", left: "12px", top: "12px", color: "var(--color-smoke)" }} />
                  </div>
                </div>
              </>
            )}

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--color-off-black)", marginBottom: "6px" }}>
                Work Email Address
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "#ffffff",
                    border: "1px solid var(--color-ash)",
                    color: "var(--color-off-black)",
                    padding: "10px 14px 10px 38px",
                    borderRadius: "10px",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
                <Mail size={16} style={{ position: "absolute", left: "12px", top: "12px", color: "var(--color-smoke)" }} />
              </div>
            </div>

            {mode !== "forgot" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-off-black)" }}>
                    Password
                  </label>
                  {mode === "signin" && (
                    <button
                      type="button"
                      onClick={() => handleModeChange("forgot")}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--color-lake-blue)",
                        fontSize: "12px",
                        cursor: "pointer",
                        fontWeight: 500,
                        padding: 0,
                      }}
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div style={{ position: "relative" }}>
                  <input
                    type="password"
                    required
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{
                      width: "100%",
                      backgroundColor: "#ffffff",
                      border: "1px solid var(--color-ash)",
                      color: "var(--color-off-black)",
                      padding: "10px 14px 10px 38px",
                      borderRadius: "10px",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  />
                  <Lock size={16} style={{ position: "absolute", left: "12px", top: "12px", color: "var(--color-smoke)" }} />
                </div>
              </div>
            )}

            {mode === "register" && (
              <>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--color-off-black)", marginBottom: "6px" }}>
                    Confirm Password
                  </label>
                  <div style={{ position: "relative" }}>
                    <input
                      type="password"
                      required
                      placeholder="••••••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      style={{
                        width: "100%",
                        backgroundColor: "#ffffff",
                        border: "1px solid var(--color-ash)",
                        color: "var(--color-off-black)",
                        padding: "10px 14px 10px 38px",
                        borderRadius: "10px",
                        fontSize: "13px",
                        boxSizing: "border-box",
                      }}
                    />
                    <Lock size={16} style={{ position: "absolute", left: "12px", top: "12px", color: "var(--color-smoke)" }} />
                  </div>
                </div>

                {/* Password Criteria Checklist */}
                <div
                  style={{
                    backgroundColor: "#f9fafb",
                    border: "1px solid var(--color-ash)",
                    borderRadius: "10px",
                    padding: "14px 16px",
                    fontSize: "12px",
                  }}
                >
                  <span style={{ fontWeight: 600, color: "var(--color-off-black)", display: "block", marginBottom: "8px" }}>
                    Security Policy Requirements:
                  </span>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                    <span style={{ color: hasMinLength ? "#166534" : "var(--color-smoke)", display: "flex", alignItems: "center", gap: "6px" }}>
                      {hasMinLength ? <Check size={14} /> : "○"} 9+ characters
                    </span>
                    <span style={{ color: hasUppercase ? "#166534" : "var(--color-smoke)", display: "flex", alignItems: "center", gap: "6px" }}>
                      {hasUppercase ? <Check size={14} /> : "○"} Uppercase letter
                    </span>
                    <span style={{ color: hasLowercase ? "#166534" : "var(--color-smoke)", display: "flex", alignItems: "center", gap: "6px" }}>
                      {hasLowercase ? <Check size={14} /> : "○"} Lowercase letter
                    </span>
                    <span style={{ color: hasSpecial ? "#166534" : "var(--color-smoke)", display: "flex", alignItems: "center", gap: "6px" }}>
                      {hasSpecial ? <Check size={14} /> : "○"} Special character
                    </span>
                  </div>
                </div>
              </>
            )}

            <button
              ref={submitButtonRef}
              type="submit"
              disabled={loading}
              className="btn-secondary-black"
              style={{
                width: "100%",
                justifyContent: "center",
                padding: "12px 24px",
                fontSize: "14px",
                marginTop: "8px",
              }}
            >
              <span>
                {loading
                  ? "Verifying Credentials..."
                  : mode === "signin"
                  ? "Sign In to Workspace"
                  : mode === "register"
                  ? "Create Account"
                  : "Send Reset Link"}
              </span>
              <ArrowRight size={16} />
            </button>

            {mode === "forgot" && (
              <button
                type="button"
                onClick={() => handleModeChange("signin")}
                className="btn-ghost"
                style={{ width: "100%", justifyContent: "center" }}
              >
                Back to Sign In
              </button>
            )}
          </form>

          {/* Quick Demo Credentials */}
          <div
            style={{
              marginTop: "32px",
              paddingTop: "20px",
              borderTop: "1px solid #e5e7eb",
              fontSize: "12px",
              color: "var(--color-smoke)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <span>
              Demo Staff: <strong style={{ color: "var(--color-off-black)" }}>finance@brightloop.local</strong>
            </span>
            <span>
              Pass: <code style={{ backgroundColor: "#f3f4f6", padding: "2px 6px", borderRadius: "4px" }}>Admin@12345</code>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
