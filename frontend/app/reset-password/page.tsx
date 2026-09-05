"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

const API_BASE = "/api/v1";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const value = searchParams.get("token");

    if (!value) {
      setError("This password reset link is invalid.");
      return;
    }

    setToken(value);
  }, [searchParams]);

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setError("");
    setMessage("");

    if (!token) {
      setError("This password reset link is invalid.");
      return;
    }

    if (password.length < 8) {
      setError(
        "Password must contain at least 8 characters.",
      );
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/auth/reset-password`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token,
            password,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.detail ||
            "Unable to reset your password.",
        );
        return;
      }

      setMessage(
        "Password updated successfully. Redirecting to sign in...",
      );

      setTimeout(() => {
        router.replace("/login");
      }, 1200);
    } catch {
      setError(
        "Unable to connect to AI Job Hunter.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px",
      }}
    >
      <section
        style={{
          width: "100%",
          maxWidth: "460px",
          padding: "40px",
          borderRadius: "24px",
          border: "1px solid #e5e7eb",
          background: "#ffffff",
        }}
      >
        <div style={{ marginBottom: "28px" }}>
          <div
            style={{
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.14em",
              marginBottom: "12px",
            }}
          >
            ACCOUNT RECOVERY
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: "32px",
              lineHeight: 1.1,
            }}
          >
            Create a new
            <br />
            password.
          </h1>

          <p
            style={{
              marginTop: "14px",
              color: "#667085",
              lineHeight: 1.6,
            }}
          >
            Choose a new password for your
            AI Job Hunter account.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <label
            htmlFor="password"
            style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: 600,
            }}
          >
            New password
          </label>

          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            placeholder="At least 8 characters"
            autoComplete="new-password"
            minLength={8}
            required
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "13px 14px",
              marginBottom: "18px",
              borderRadius: "10px",
              border: "1px solid #d0d5dd",
            }}
          />

          <label
            htmlFor="confirmPassword"
            style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: 600,
            }}
          >
            Confirm password
          </label>

          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(event) =>
              setConfirmPassword(event.target.value)
            }
            placeholder="Repeat your password"
            autoComplete="new-password"
            minLength={8}
            required
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "13px 14px",
              marginBottom: "18px",
              borderRadius: "10px",
              border: "1px solid #d0d5dd",
            }}
          />

          {error && (
            <p
              role="alert"
              style={{
                color: "#b42318",
                margin: "0 0 16px",
              }}
            >
              {error}
            </p>
          )}

          {message && (
            <p
              role="status"
              style={{
                color: "#027a48",
                margin: "0 0 16px",
              }}
            >
              {message}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !token}
            style={{
              width: "100%",
              padding: "14px",
              border: 0,
              borderRadius: "10px",
              fontWeight: 700,
              cursor:
                loading || !token
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            {loading
              ? "Updating password..."
              : "Update password"}
          </button>
        </form>
      </section>
    </main>
  );
}


export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
