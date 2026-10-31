import { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { CustomerPortal } from "./components/CustomerPortal";
import { FinanceConsole } from "./components/FinanceConsole";
import { LoginModal } from "./components/LoginModal";
import { api } from "./api";

export function App() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [activeView, setActiveView] = useState<"portal" | "finance">("portal");
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  useEffect(() => {
    // Check if session is already active
    api.auth.getMe()
      .then((user) => {
        setCurrentUser(user);
        if (user.role === "FINANCE" || user.role === "ADMINISTRATOR") {
          setActiveView("finance");
        } else {
          setActiveView("portal");
        }
      })
      .catch(() => {
        // Not logged in yet
        setIsLoginModalOpen(true);
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

  const handleLoginSuccess = (user: any) => {
    setCurrentUser(user);
    if (user.role === "FINANCE" || user.role === "ADMINISTRATOR") {
      setActiveView("finance");
    } else {
      setActiveView("portal");
    }
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#000000", color: "#eeeeee" }}>
      <Navbar
        currentUser={currentUser}
        activeView={activeView}
        onSwitchView={setActiveView}
        onLogout={handleLogout}
        onOpenLogin={() => setIsLoginModalOpen(true)}
      />

      <main>
        {activeView === "portal" ? <CustomerPortal /> : <FinanceConsole />}
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
