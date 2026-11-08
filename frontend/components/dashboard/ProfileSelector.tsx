"use client";

import { useState } from "react";
import { ChevronDown, User } from "lucide-react";

const AVAILABLE_PROFILES = [
  { id: "crm_manager", label: "CRM Manager" },
  { id: "crm_implementation_manager", label: "CRM Implementation Manager" },
] as const;

type Props = {
  currentProfileId: string;
  onChange: (profileId: string) => void;
};

export default function ProfileSelector({ currentProfileId, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const current = AVAILABLE_PROFILES.find(
    (p) => p.id === currentProfileId
  ) || AVAILABLE_PROFILES[0];

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 14px",
          borderRadius: 10,
          border: "1px solid #d8d2ff",
          background: "#fff",
          color: "#5c43ef",
          fontSize: 13,
          fontWeight: 700,
          cursor: "pointer",
        }}
      >
        <User size={14} />
        {current.label}
        <ChevronDown size={12} style={{ opacity: 0.6 }} />
      </button>

      {open && (
        <div
          role="listbox"
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            zIndex: 100,
            minWidth: 240,
            padding: 6,
            borderRadius: 10,
            border: "1px solid #e4e7ec",
            background: "#fff",
            boxShadow: "0 8px 24px rgba(16,24,40,0.12)",
          }}
        >
          {AVAILABLE_PROFILES.map((profile) => {
            const isActive = profile.id === currentProfileId;
            return (
              <button
                key={profile.id}
                type="button"
                role="option"
                aria-selected={isActive}
                onClick={() => {
                  setOpen(false);
                  onChange(profile.id);
                }}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "10px 12px",
                  textAlign: "left",
                  border: 0,
                  borderRadius: 8,
                  background: isActive ? "#eef2ff" : "transparent",
                  color: isActive ? "#4f46e5" : "#344054",
                  fontSize: 13,
                  fontWeight: isActive ? 700 : 600,
                  cursor: "pointer",
                }}
              >
                {profile.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
