"use client";

import {
  ArrowLeft,
  Check,
  LoaderCircle,
  Save,
} from "lucide-react";
import { useEffect, useState } from "react";
import ProfileAccountCard from "./ProfileAccountCard";
import ProfilePersonalCard from "./ProfilePersonalCard";
import ProfileCareerCard from "./ProfileCareerCard";
import styles from "./ProfileManagement.module.css";
import type {
  ManagedProfile,
  ProfileFormState,
} from "./profileManagement.types";

const API_BASE = "/api/v1";

function createForm(profile: ManagedProfile): ProfileFormState {
  return {
    full_name: profile.full_name || "",
    phone: profile.phone || "",
    preferred_location: profile.preferred_location || "",
    role_level: profile.role_level || "",
    experience_years: profile.experience_years || "",
    current_ctc_lpa: String(profile.current_ctc_lpa ?? ""),
    expected_ctc_lpa: String(profile.expected_ctc_lpa ?? ""),
    resume_path: profile.resume_path || "",
  };
}

export default function ProfileManagement() {
  const [profile, setProfile] = useState<ManagedProfile | null>(null);
  const [form, setForm] = useState<ProfileFormState | null>(null);
  const [email, setEmail] = useState("");
  const [initialForm, setInitialForm] =
    useState<ProfileFormState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadProfile() {
    const token = localStorage.getItem("ai_job_hunter_token");

    if (!token) {
      window.location.href = "/login";
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/profile`, {
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        localStorage.removeItem("ai_job_hunter_token");
        window.location.href = "/login";
        return;
      }

      const data = await response.json();

      if (!response.ok || !data.profile) {
        throw new Error(
          data.detail || "Unable to load your profile.",
        );
      }

      const nextProfile = data.profile as ManagedProfile;
      const nextForm = createForm(nextProfile);

      setProfile(nextProfile);
      setForm(nextForm);
      setInitialForm(nextForm);
      setEmail(data.profile?.email || data.email || "");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your profile.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  function updateField(
    field: keyof ProfileFormState,
    value: string,
  ) {
    setMessage("");
    setError("");

    setForm((current) =>
      current
        ? {
            ...current,
            [field]: value,
          }
        : current,
    );
  }

  function cancelChanges() {
    if (!initialForm) return;
    setForm({ ...initialForm });
    setMessage("");
    setError("");
  }

  async function saveProfile() {
    if (!form || !profile) return;

    const currentCtc = Number(form.current_ctc_lpa);
    const expectedCtc = Number(form.expected_ctc_lpa);

    if (!form.full_name.trim()) {
      setError("Full name is required.");
      return;
    }

    if (!form.preferred_location.trim()) {
      setError("Preferred location is required.");
      return;
    }

    if (!form.role_level.trim()) {
      setError("Role level is required.");
      return;
    }

    if (!form.experience_years.trim()) {
      setError("Experience is required.");
      return;
    }

    if (!Number.isFinite(currentCtc) || currentCtc < 0) {
      setError("Please enter a valid current CTC.");
      return;
    }

    if (!Number.isFinite(expectedCtc) || expectedCtc < 0) {
      setError("Please enter a valid expected CTC.");
      return;
    }

    if (expectedCtc < currentCtc) {
      setError("Expected CTC cannot be lower than current CTC.");
      return;
    }

    const token = localStorage.getItem("ai_job_hunter_token");

    if (!token) {
      window.location.href = "/login";
      return;
    }

    setSaving(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch(`${API_BASE}/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: form.full_name.trim(),
          phone: form.phone.trim() || null,
          // Sent for compatibility only.
          // Backend ignores it once the profile exists.
          profile_id: profile.profile_id,
          preferred_location: form.preferred_location.trim(),
          role_level: form.role_level.trim(),
          experience_years: form.experience_years.trim(),
          current_ctc_lpa: currentCtc,
          expected_ctc_lpa: expectedCtc,
          resume_path: form.resume_path.trim() || null,
        }),
      });

      const data = await response.json();

      if (response.status === 401) {
        localStorage.removeItem("ai_job_hunter_token");
        window.location.href = "/login";
        return;
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to save your profile.",
        );
      }

      const nextProfile = data.profile as ManagedProfile;
      const nextForm = createForm(nextProfile);

      setProfile(nextProfile);
      setForm(nextForm);
      setInitialForm(nextForm);
      setMessage("Profile updated successfully.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to save your profile.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className={styles.page}>
        <div className={styles.loading}>
          Loading your profile…
        </div>
      </main>
    );
  }

  if (error && !profile) {
    return (
      <main className={styles.page}>
        <div className={styles.errorPage}>
          <div>
            <strong>Unable to load your profile</strong>
            <div>{error}</div>
          </div>
        </div>
      </main>
    );
  }

  if (!profile || !form) return null;

  const dirty =
    JSON.stringify(form) !== JSON.stringify(initialForm);

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <div className={styles.topbar}>
          <button
            type="button"
            className={styles.back}
            onClick={() => {
              window.location.href = "/dashboard";
            }}
          >
            <ArrowLeft size={15} />
            Back to dashboard
          </button>
        </div>

        <header className={styles.hero}>
          <span className={styles.eyebrow}>PROFILE MANAGEMENT</span>
          <h1>Your profile</h1>
          <p>
            Keep your professional information up to date. Your account
            identity and selected job profile remain protected.
          </p>
        </header>

        <div className={styles.stack}>
          <ProfileAccountCard
            email={email || "Authenticated account"}
            profileId={profile.profile_id}
          />

          <ProfilePersonalCard
            fullName={form.full_name}
            phone={form.phone}
            onChange={updateField}
          />

          <ProfileCareerCard
            values={{
              preferred_location: form.preferred_location,
              role_level: form.role_level,
              experience_years: form.experience_years,
              current_ctc_lpa: form.current_ctc_lpa,
              expected_ctc_lpa: form.expected_ctc_lpa,
              resume_path: form.resume_path,
            }}
            onChange={updateField}
          />
        </div>

        <div className={styles.actions}>
          <div
            className={`${styles.status} ${
              message
                ? styles.success
                : error
                  ? styles.error
                  : ""
            }`}
          >
            {message ? (
              <span>
                <Check size={13} /> {message}
              </span>
            ) : error ? (
              error
            ) : dirty ? (
              "You have unsaved changes."
            ) : (
              "Your profile is up to date."
            )}
          </div>

          <div className={styles.actionButtons}>
            <button
              type="button"
              className={styles.cancel}
              onClick={cancelChanges}
              disabled={!dirty || saving}
            >
              Cancel
            </button>

            <button
              type="button"
              className={styles.save}
              onClick={saveProfile}
              disabled={!dirty || saving}
            >
              {saving ? (
                <LoaderCircle size={15} className="profileSpin" />
              ) : (
                <Save size={15} />
              )}
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
