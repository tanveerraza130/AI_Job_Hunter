"use client";

import { ReactNode, useEffect, useState } from "react";

const TOKEN_KEY = "ai_job_hunter_token";

type SessionRedirectProps = {
  mode: "public" | "dashboard";
  children: ReactNode;
};

export default function SessionRedirect({
  mode,
  children,
}: SessionRedirectProps) {
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);

    if (mode === "public") {
      if (token) {
        window.location.replace("/dashboard");
        return;
      }

      setAllowed(true);
      return;
    }

    if (!token) {
      window.location.replace("/login");
      return;
    }

    setAllowed(true);
  }, [mode]);

  if (!allowed) {
    return null;
  }

  return <>{children}</>;
}
