import { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { CustomerPortal } from "./components/CustomerPortal";
import { StaffConsoleShell } from "./components/StaffConsoleShell";
import { CommercialConsole } from "./components/CommercialConsole";
import { AuthSection } from "./components/AuthSection";
import { LoadingScreen } from "./components/LoadingScreen";
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
        // Allow a brief moment for the progress bar animation
        setTimeout(() => {
          setLoading(false);
        }, 800);
      });
  }, []);

  const handleLogout = async () => {
    try {
      await api.auth.logout();
    } catch {
      // ignore
    }
    setCurrentUser(null);
  };

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    if (["FINANCE", "ADMINISTRATOR", "OPERATIONS"].includes(user.role)) {
      setActiveView("console");
    } else {
      setActiveView("portal");
    }
  };

  // Full-screen Loading Screen with Brand Logo & Progress Bar
  if (loading) {
    return <LoadingScreen message="Initializing Brightloop workspace..." minDuration={0.8} />;
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
        }}
      >
        <main style={{ width: "100%", maxWidth: "1140px" }}>
          <AuthSection onSuccess={handleLoginSuccess} />
        </main>
      </div>
    );
  }

  // Authenticated App with Navbar
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--color-parchment)", color: "var(--color-off-black)" }}>
      <Navbar
        currentUser={currentUser}
        activeView={activeView}
        onSwitchView={(view) => setActiveView(view)}
        onLogout={handleLogout}
        onOpenLogin={() => {}}
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
  );
}

export default App;
