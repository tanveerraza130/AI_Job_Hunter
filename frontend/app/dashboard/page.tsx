"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Dashboard from "@/components/dashboard/Dashboard";
import SessionRedirect from "@/components/auth/SessionRedirect";

function DashboardAuthHandler({
  onReady,
}: {
  onReady: () => void;
}) {
  const searchParams = useSearchParams();
  const handledRef = useRef(false);

  useEffect(() => {
    if (handledRef.current) return;
    handledRef.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const googleSuccess = searchParams.get("google_success");

    if (googleSuccess === "1" && code && state) {
      // Remove callback parameters before making the exchange request.
      window.history.replaceState(
        {},
        document.title,
        "/dashboard",
      );

      void (async () => {
        try {
          const response = await fetch("/api/v1/auth/google/exchange", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
            body: JSON.stringify({ code, state }),
          });

          if (!response.ok) {
            throw new Error("Google authorization-code exchange failed.");
          }

          const exchange = await response.json();
          if (typeof exchange.access_token !== "string") {
            throw new Error("Google exchange returned no access token.");
          }

          localStorage.setItem(
            "ai_job_hunter_token",
            exchange.access_token,
          );
          onReady();
        } catch {
          localStorage.removeItem("ai_job_hunter_token");
          window.location.replace("/login");
        }
      })();

      return;
    }

    // Existing non-Google sessions can mount the dashboard normally.
    onReady();
  }, [searchParams, onReady]);

  return null;
}

export default function DashboardPage() {
  const [authReady, setAuthReady] = useState(false);

  const handleAuthReady = () => {
    setAuthReady(true);
  };

  return (
    <>
      <Suspense fallback={null}>
        <DashboardAuthHandler
          onReady={handleAuthReady}
        />
      </Suspense>

      {authReady && <SessionRedirect mode="dashboard"><Dashboard /></SessionRedirect>}
    </>
  );
}
