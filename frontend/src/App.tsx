import { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { CustomerPortal } from "./components/CustomerPortal";
import { StaffConsoleShell } from "./components/StaffConsoleShell";
import { CommercialConsole } from "./components/CommercialConsole";
import { LoginModal } from "./components/LoginModal";
import { api, type User } from "./api";

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeView, setActiveView] = useState<"portal" | "console" | "commercial">("portal");
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [, setLoading] = useState(true);

  useEffect(() => {
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
        // Not logged in yet
        setIsLoginModalOpen(true);
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
    setIsLoginModalOpen(true);
  };

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    if (["FINANCE", "ADMINISTRATOR", "OPERATIONS"].includes(user.role)) {
      setActiveView("console");
    } else {
      setActiveView("portal");
    }
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--color-parchment)", color: "var(--color-off-black)" }}>
      <Navbar
        currentUser={currentUser}
        activeView={activeView}
        onSwitchView={setActiveView}
        onLogout={handleLogout}
        onOpenLogin={() => setIsLoginModalOpen(true)}
      />

      <main>
        {activeView === "portal" ? (
          <div style={{ maxWidth: "1080px", margin: "0 auto", padding: "32px 24px" }}>
            <CustomerPortal />
          </div>
        ) : activeView === "commercial" ? (
          <CommercialConsole />
        ) : currentUser ? (
          <StaffConsoleShell currentUser={currentUser} />
        ) : (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--color-smoke)" }}>
            Please sign in to access the Staff Console.
          </div>
        )}
      </main>

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onSuccess={handleLoginSuccess}
      />
    </div>
  );
}

export default App;
