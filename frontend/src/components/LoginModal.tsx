import React from "react";
import type { User } from "../api";
import { AuthSection } from "./AuthSection";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onSuccess }) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(17, 24, 39, 0.6)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "20px",
        overflowY: "auto",
      }}
    >
      <div style={{ width: "100%", maxWidth: "1040px" }}>
        <AuthSection onSuccess={onSuccess} onCancel={onClose} />
      </div>
    </div>
  );
};
