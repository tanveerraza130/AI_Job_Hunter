"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Dashboard from "@/components/dashboard/Dashboard";

function DashboardAuthHandler({
  onReady,
}: {
  onReady: () => void;
}) {
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    const googleSuccess = searchParams.get("google_success");

    /*
     * Google authentication arrives at:
     * /dashboard?google_success=1&token=...
     *
     * Store the token BEFORE Dashboard mounts.
     * This prevents Dashboard from starting with an empty
     * localStorage token and entering the loading state.
     */
    if (googleSuccess === "1" && token) {
      localStorage.setItem(
        "ai_job_hunter_token",
        token,
      );

      /*
       * Remove the temporary OAuth query parameters
       * without causing another navigation/remount.
       */
      window.history.replaceState(
        {},
        document.title,
        "/dashboard",
      );
    }

    /*
     * Dashboard may now safely mount because:
     * - Google token has been stored, if present
     * - normal email-login sessions already have their token
     */
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

      {authReady && <Dashboard />}
    </>
  );
}
