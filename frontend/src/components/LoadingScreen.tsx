import React, { useEffect, useRef } from "react";
import gsap from "gsap";
import { Logo } from "./Logo";

interface LoadingScreenProps {
  message?: string;
  onFinish?: () => void;
  minDuration?: number;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = "Initializing Brightloop...",
  onFinish,
  minDuration = 2.8,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const logoCircleRef = useRef<HTMLDivElement>(null);
  const progressFillRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // 1. Clean, smooth entrance for the brand logo badge (no bounce)
      gsap.fromTo(
        logoCircleRef.current,
        { opacity: 0, y: -6 },
        { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }
      );

      // 2. Smooth progress bar animation with easeInOut
      gsap.fromTo(
        progressFillRef.current,
        { width: "0%" },
        {
          width: "100%",
          duration: minDuration,
          ease: "power1.inOut",
          onComplete: () => {
            if (onFinish) {
              gsap.to(containerRef.current, {
                opacity: 0,
                duration: 0.3,
                ease: "power2.out",
                onComplete: onFinish,
              });
            }
          },
        }
      );

      // 3. Subtle text reveal
      if (textRef.current) {
        gsap.fromTo(
          textRef.current,
          { opacity: 0, y: 4 },
          { opacity: 1, y: 0, duration: 0.4, delay: 0.15, ease: "power2.out" }
        );
      }
    }, containerRef);

    return () => ctx.revert();
  }, [minDuration, onFinish]);

  return (
    <div
      ref={containerRef}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "var(--color-parchment)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "28px",
        }}
      >
        {/* Brand Circular Symbol Badge */}
        <div
          ref={logoCircleRef}
          style={{
            width: "68px",
            height: "68px",
            borderRadius: "9999px",
            backgroundColor: "var(--color-off-black)",
            color: "#ffffff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 8px 24px rgba(36, 36, 36, 0.08)",
          }}
        >
          <Logo size={28} style={{ color: "#ffffff" }} />
        </div>

        {/* Minimal Progress Bar */}
        <div
          style={{
            width: "220px",
            height: "3px",
            backgroundColor: "var(--color-ash)",
            borderRadius: "9999px",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <div
            ref={progressFillRef}
            style={{
              height: "100%",
              width: "0%",
              backgroundColor: "var(--color-off-black)",
              borderRadius: "9999px",
            }}
          />
        </div>

        {/* Subtle helper text */}
        {message && (
          <div
            ref={textRef}
            style={{
              fontSize: "12px",
              fontFamily: "var(--font-mono)",
              color: "var(--color-smoke)",
              letterSpacing: "0.02em",
              marginTop: "4px",
            }}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
};
