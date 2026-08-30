"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Dashboard from "@/components/dashboard/Dashboard";

function DashboardAuthHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    const googleSuccess = searchParams.get("google_success");

    if (googleSuccess === "1" && token) {
      localStorage.setItem("ai_job_hunter_token", token);
      router.replace("/dashboard");
    }
  }, [router, searchParams]);

  return null;
}

export default function DashboardPage() {
  return (
    <>
      <Suspense fallback={null}>
        <DashboardAuthHandler />
      </Suspense>

      <Dashboard />
    </>
  );
}
