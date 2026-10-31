import { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { CustomerPortal } from "./components/CustomerPortal";
import { StaffConsoleShell } from "./components/StaffConsoleShell";
import { CommercialConsole } from "./components/CommercialConsole";
import { AuthSection } from "./components/AuthSection";
import { api, type User } from "./api";

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeView, setActiveView] = useState<"portal" | "console" | "commercial">("portal");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize CSRF cookie from backend
    api.auth.csrf().catch(() => {});

    // Check if session is already active
    api.auth.getMe()
      .then((user) => {
        setCurrentUser(user);
        if (["FINANCE", "ADMINISTRATOR", "OPERATIONS"].includes(user.role)) {
          setActiveView("console");
        } else {
          setActiveView("portal");
        }
      })
      .catch(() => {
        setCurrentUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleLogout = async () => {
    try {
      await api.auth.logout();
    } catch {
      // ignore
    }
    setCurrentUser(null);
    setActiveView("portal");
  };

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    if (["FINANCE", "ADMINISTRATOR", "OPERATIONS"].includes(user.role)) {
      setActiveView("console");
    } else {
      setActiveView("portal");
    }
  };

  if (loading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "var(--color-parchment)",
          color: "var(--color-smoke)",
          fontFamily: "var(--font-mono)",
          fontSize: "13px",
        }}
      >
        Initializing workspace...
      </div>
    );
  }

  // Pure Standalone Auth Page (Zero top bar or header elements)
  if (!currentUser) {
    return (
      <div
        style={{
          minHeight: "100vh",
          backgroundColor: "var(--color-parchment)",
          color: "var(--color-off-black)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "40px 20px",
          boxSizing: "border-box",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div className="bg-watermark-overlay" aria-hidden="true">
          <img src="/logo.svg" alt="" className="bg-watermark-logo" />
        </div>
        <main style={{ width: "100%", maxWidth: "1140px", position: "relative", zIndex: 1 }}>
          <AuthSection onSuccess={handleLoginSuccess} />
        </main>
      </div>
    );
  }

  // Authenticated App with Navbar
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--color-parchment)", color: "var(--color-off-black)", position: "relative", overflowX: "hidden" }}>
      <div className="bg-watermark-overlay" aria-hidden="true">
        <img src="/logo.svg" alt="" className="bg-watermark-logo" />
      </div>
      <div style={{ position: "relative", zIndex: 1 }}>
        <Navbar
          currentUser={currentUser}
          activeView={activeView}
          onSwitchView={(view) => setActiveView(view)}
          onLogout={handleLogout}
          onOpenLogin={() => setCurrentUser(null)}
        />

        <main>
          {activeView === "portal" ? (
            <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 24px" }}>
              <CustomerPortal />
            </div>
          ) : activeView === "commercial" ? (
            <CommercialConsole />
          ) : (
            <StaffConsoleShell currentUser={currentUser} />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
