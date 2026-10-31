import { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { CustomerPortal } from "./components/CustomerPortal";
import { FinanceConsole } from "./components/FinanceConsole";
import { CommercialConsole } from "./components/CommercialConsole";
import { LoginModal } from "./components/LoginModal";
import { api, type User } from "./api";

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeView, setActiveView] = useState<"portal" | "commercial" | "finance">("commercial");
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  useEffect(() => {
    // Check if session is already active
    api.auth.getMe()
      .then((user) => {
        setCurrentUser(user);
        if (user.role === "FINANCE") {
          setActiveView("finance");
        } else if (user.role === "OPERATIONS" || user.role === "ADMINISTRATOR") {
          setActiveView("commercial");
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

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    if (user.role === "FINANCE") {
      setActiveView("finance");
    } else if (user.role === "OPERATIONS" || user.role === "ADMINISTRATOR") {
      setActiveView("commercial");
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
        {activeView === "portal" && <CustomerPortal />}
        {activeView === "commercial" && <CommercialConsole />}
        {activeView === "finance" && <FinanceConsole />}
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
