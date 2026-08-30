"use client";

import {
  ArrowLeft,
  BriefcaseBusiness,
  Check,
  CheckCircle2,
  FileText,
  GraduationCap,
  LoaderCircle,
  MapPin,
  Save,
  Settings2,
  ShieldCheck,
  Sparkles,
  UserRound,
  Wrench,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import DesktopHeader from "@/components/dashboard/DesktopHeader";

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

function formatProfile(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getCompletion(profile: ManagedProfile) {
  const checks = [
    Boolean(profile.full_name?.trim()),
    Boolean(profile.phone?.trim()),
    Boolean(profile.preferred_location?.trim()),
    Boolean(profile.role_level?.trim()),
    Boolean(profile.experience_years?.trim()),
    Number(profile.current_ctc_lpa) >= 0,
    Number(profile.expected_ctc_lpa) >= 0,
    Boolean(profile.resume_path?.trim()),
  ];

  return Math.round(
    (checks.filter(Boolean).length / checks.length) * 100,
  );
}

export default function ProfileManagement() {
  const [profile, setProfile] =
    useState<ManagedProfile | null>(null);

  const [form, setForm] =
    useState<ProfileFormState | null>(null);

  const [email, setEmail] = useState("");

  const [initialForm, setInitialForm] =
    useState<ProfileFormState | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadProfile() {
    const token = localStorage.getItem(
      "ai_job_hunter_token",
    );

    if (!token) {
      window.location.href = "/login";
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE}/profile`,
        {
          cache: "no-store",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "ai_job_hunter_token",
        );
        window.location.href = "/login";
        return;
      }

      const data = await response.json();

      if (!response.ok || !data.profile) {
        throw new Error(
          data.detail ||
            "Unable to load your profile.",
        );
      }

      const nextProfile =
        data.profile as ManagedProfile;

      const nextForm =
        createForm(nextProfile);

      setProfile(nextProfile);
      setForm(nextForm);
      setInitialForm(nextForm);

      setEmail(
        data.email ||
          data.user?.email ||
          "",
      );
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

    setForm({
      ...initialForm,
    });

    setMessage("");
    setError("");
  }

  async function saveProfile() {
    if (!form || !profile) return;

    const currentCtc =
      Number(form.current_ctc_lpa);

    const expectedCtc =
      Number(form.expected_ctc_lpa);

    if (!form.full_name.trim()) {
      setError("Full name is required.");
      return;
    }

    if (!form.preferred_location.trim()) {
      setError(
        "Preferred location is required.",
      );
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

    if (
      !Number.isFinite(currentCtc) ||
      currentCtc < 0
    ) {
      setError(
        "Please enter a valid current CTC.",
      );
      return;
    }

    if (
      !Number.isFinite(expectedCtc) ||
      expectedCtc < 0
    ) {
      setError(
        "Please enter a valid expected CTC.",
      );
      return;
    }

    if (expectedCtc < currentCtc) {
      setError(
        "Expected CTC cannot be lower than current CTC.",
      );
      return;
    }

    const token = localStorage.getItem(
      "ai_job_hunter_token",
    );

    if (!token) {
      window.location.href = "/login";
      return;
    }

    setSaving(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch(
        `${API_BASE}/profile`,
        {
          method: "PUT",
          headers: {
            "Content-Type":
              "application/json",
            Authorization:
              `Bearer ${token}`,
          },
          body: JSON.stringify({
            full_name:
              form.full_name.trim(),

            phone:
              form.phone.trim() || null,

            profile_id:
              profile.profile_id,

            preferred_location:
              form.preferred_location.trim(),

            role_level:
              form.role_level.trim(),

            experience_years:
              form.experience_years.trim(),

            current_ctc_lpa:
              currentCtc,

            expected_ctc_lpa:
              expectedCtc,

            resume_path:
              form.resume_path.trim() ||
              null,
          }),
        },
      );

      const data =
        await response.json();

      if (response.status === 401) {
        localStorage.removeItem(
          "ai_job_hunter_token",
        );

        window.location.href =
          "/login";

        return;
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to save your profile.",
        );
      }

      const nextProfile =
        data.profile as ManagedProfile;

      const nextForm =
        createForm(nextProfile);

      setProfile(nextProfile);
      setForm(nextForm);
      setInitialForm(nextForm);

      setMessage(
        "Profile updated successfully.",
      );
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

  const completion = useMemo(
    () =>
      profile
        ? getCompletion(profile)
        : 0,
    [profile],
  );

  const dirty =
    JSON.stringify(form) !==
    JSON.stringify(initialForm);

  if (loading) {
    return (
      <main className={styles.page}>
        <div className={styles.loadingPage}>
          <div className={styles.loadingIcon}>
            <LoaderCircle
              size={22}
              className="profileSpin"
            />
          </div>

          <strong>
            Loading your profile
          </strong>

          <span>
            Fetching your authenticated
            profile information…
          </span>
        </div>
      </main>
    );
  }

  if (error && !profile) {
    return (
      <main className={styles.page}>
        <div className={styles.errorPage}>
          <div className={styles.errorIcon}>
            <ShieldCheck size={22} />
          </div>

          <strong>
            Unable to load your profile
          </strong>

          <span>{error}</span>

          <button
            type="button"
            onClick={loadProfile}
          >
            Try again
          </button>
        </div>
      </main>
    );
  }

  if (!profile || !form) {
    return null;
  }

  const profileName =
    formatProfile(profile.profile_id);

  return (
    <main className={styles.page}>
      <DesktopHeader
        profileId={profile.profile_id}
      />

      <div className={styles.shell}>
        <div className={styles.mobileBack}>
          <button
            type="button"
            onClick={() => {
              window.location.href =
                "/dashboard";
            }}
          >
            <ArrowLeft size={15} />
            Dashboard
          </button>
        </div>

        <header className={styles.pageHeader}>
          <div className={styles.pageHeaderIcon}>
            <Sparkles size={18} />
          </div>

          <div>
            <span className={styles.eyebrow}>
              PROFILE MANAGEMENT
            </span>

            <h1>
              Profile Management
            </h1>

            <p>
              Manage your personal and
              career information
            </p>
          </div>
        </header>

        <section className={styles.hero}>
          <div className={styles.heroAvatar}>
            <UserRound size={38} />
          </div>

          <div className={styles.heroCopy}>
            <span>
              Your Profile Summary
            </span>

            <h2>{profileName}</h2>

            <div className={styles.heroMeta}>
              <span
                className={
                  styles.activeBadge
                }
              >
                <CheckCircle2 size={12} />
                Active
              </span>

              <span>
                <MapPin size={13} />
                {profile.preferred_location}
              </span>

              <span>
                <BriefcaseBusiness
                  size={13}
                />
                {profile.role_level}
              </span>
            </div>
          </div>

          <div className={styles.heroAction}>
            <span>
              Profile completion
            </span>

            <strong>
              {completion}%
            </strong>
          </div>
        </section>

        <div className={styles.layout}>
          <aside className={styles.sidebar}>
            <nav
              className={
                styles.sidebarNavigation
              }
            >
              <a
                href="#overview"
                className={
                  styles.sidebarActive
                }
              >
                <Sparkles size={16} />
                Overview
              </a>

              <a href="#personal">
                <UserRound size={16} />
                Personal Information
              </a>

              <a href="#career">
                <BriefcaseBusiness
                  size={16}
                />
                Career Details
              </a>

              <a href="#skills">
                <Wrench size={16} />
                Skills & Tools
              </a>

              <a href="#preferences">
                <Settings2 size={16} />
                Job Preferences
              </a>

              <a href="#resume">
                <FileText size={16} />
                Resume & Documents
              </a>

              <a href="#account">
                <ShieldCheck size={16} />
                Account Settings
              </a>
            </nav>

            <div
              className={
                styles.completionCard
              }
            >
              <span>
                Profile Completion
              </span>

              <div
                className={
                  styles.completionRing
                }
                style={{
                  "--completion":
                    `${completion * 3.6}deg`,
                } as React.CSSProperties}
              >
                <strong>
                  {completion}%
                </strong>

                <small>
                  Complete
                </small>
              </div>

              <p>
                Complete more details
                to improve the relevance
                of your job matches.
              </p>

              <a href="#personal">
                Improve Profile
              </a>
            </div>
          </aside>

          <div className={styles.content}>
            <section
              id="overview"
              className={styles.section}
            >
              <div
                className={
                  styles.sectionHeading
                }
              >
                <div>
                  <span
                    className={
                      styles.eyebrow
                    }
                  >
                    OVERVIEW
                  </span>

                  <h2>
                    Your profile at a glance
                  </h2>

                  <p>
                    A quick view of the
                    information currently
                    connected to your account.
                  </p>
                </div>
              </div>

              <div
                className={
                  styles.statGrid
                }
              >
                <div
                  className={styles.statCard}
                >
                  <div
                    className={
                      styles.statIcon
                    }
                  >
                    <UserRound size={18} />
                  </div>

                  <span>
                    Profile status
                  </span>

                  <strong>
                    Active
                  </strong>

                  <small>
                    Authenticated profile
                  </small>
                </div>

                <div
                  className={styles.statCard}
                >
                  <div
                    className={
                      styles.statIcon
                    }
                  >
                    <MapPin size={18} />
                  </div>

                  <span>
                    Preferred location
                  </span>

                  <strong>
                    {profile.preferred_location}
                  </strong>

                  <small>
                    Current preference
                  </small>
                </div>

                <div
                  className={styles.statCard}
                >
                  <div
                    className={
                      styles.statIcon
                    }
                  >
                    <GraduationCap
                      size={18}
                    />
                  </div>

                  <span>
                    Experience
                  </span>

                  <strong>
                    {profile.experience_years}
                  </strong>

                  <small>
                    Professional experience
                  </small>
                </div>

                <div
                  className={styles.statCard}
                >
                  <div
                    className={
                      styles.statIcon
                    }
                  >
                    <BriefcaseBusiness
                      size={18}
                    />
                  </div>

                  <span>
                    Expected CTC
                  </span>

                  <strong>
                    ₹{profile.expected_ctc_lpa}
                    LPA
                  </strong>

                  <small>
                    Current target
                  </small>
                </div>
              </div>
            </section>

            <section
              className={styles.section}
            >
              <div
                className={
                  styles.sectionHeading
                }
              >
                <div>
                  <span
                    className={
                      styles.eyebrow
                    }
                  >
                    COMPLETE YOUR PROFILE
                  </span>

                  <h2>
                    Build a stronger profile
                  </h2>

                  <p>
                    More complete information
                    helps keep your job
                    recommendations relevant.
                  </p>
                </div>

                <div
                  className={
                    styles.completionMini
                  }
                >
                  {completion}% complete
                </div>
              </div>

              <div
                className={
                  styles.checklist
                }
              >
                <div
                  className={
                    styles.checkItem
                  }
                >
                  <div
                    className={
                      styles.checkIconGreen
                    }
                  >
                    <Check size={15} />
                  </div>

                  <div>
                    <strong>
                      Personal Information
                    </strong>

                    <span>
                      Name and contact details
                    </span>
                  </div>

                  <b>
                    Completed
                  </b>
                </div>

                <div
                  className={
                    styles.checkItem
                  }
                >
                  <div
                    className={
                      styles.checkIcon
                    }
                  >
                    <BriefcaseBusiness
                      size={15}
                    />
                  </div>

                  <div>
                    <strong>
                      Career Details
                    </strong>

                    <span>
                      Role, experience and
                      compensation
                    </span>
                  </div>

                  <div
                    className={
                      styles.progressWrap
                    }
                  >
                    <div
                      className={
                        styles.progressTrack
                      }
                    >
                      <span
                        style={{
                          width: `${Math.min(
                            completion,
                            100,
                          )}%`,
                        }}
                      />
                    </div>

                    <small>
                      {completion}%
                    </small>
                  </div>

                  <a href="#career">
                    Continue
                  </a>
                </div>

                <div
                  className={
                    styles.checkItem
                  }
                >
                  <div
                    className={
                      styles.checkIcon
                    }
                  >
                    <FileText size={15} />
                  </div>

                  <div>
                    <strong>
                      Resume & Documents
                    </strong>

                    <span>
                      Resume attached to
                      your profile
                    </span>
                  </div>

                  {profile.resume_path ? (
                    <b>
                      Completed
                    </b>
                  ) : (
                    <a href="#career">
                      Add resume
                    </a>
                  )}
                </div>
              </div>
            </section>

            <section
              id="account"
              className={styles.editSection}
            >
              <ProfileAccountCard
                email={
                  email ||
                  "Authenticated account"
                }
                profileId={
                  profile.profile_id
                }
              />
            </section>

            <section
              id="personal"
              className={styles.editSection}
            >
              <ProfilePersonalCard
                fullName={form.full_name}
                phone={form.phone}
                onChange={
                  updateField
                }
              />
            </section>

            <section
              id="career"
              className={styles.editSection}
            >
              <ProfileCareerCard
                values={{
                  preferred_location:
                    form.preferred_location,

                  role_level:
                    form.role_level,

                  experience_years:
                    form.experience_years,

                  current_ctc_lpa:
                    form.current_ctc_lpa,

                  expected_ctc_lpa:
                    form.expected_ctc_lpa,

                  resume_path:
                    form.resume_path,
                }}
                onChange={
                  updateField
                }
              />
            </section>

            <section
              id="skills"
              className={
                styles.comingSoon
              }
            >
              <div
                className={
                  styles.comingSoonIcon
                }
              >
                <Wrench size={19} />
              </div>

              <div>
                <strong>
                  Skills & Tools
                </strong>

                <p>
                  Skills and tool preferences
                  will be managed here as
                  this profile area expands.
                </p>
              </div>
            </section>

            <section
              id="preferences"
              className={
                styles.comingSoon
              }
            >
              <div
                className={
                  styles.comingSoonIcon
                }
              >
                <Settings2 size={19} />
              </div>

              <div>
                <strong>
                  Job Preferences
                </strong>

                <p>
                  Advanced job preferences
                  will be added without
                  changing your authenticated
                  profile identity.
                </p>
              </div>
            </section>

            <section
              id="resume"
              className={
                styles.comingSoon
              }
            >
              <div
                className={
                  styles.comingSoonIcon
                }
              >
                <FileText size={19} />
              </div>

              <div>
                <strong>
                  Resume & Documents
                </strong>

                <p>
                  Your current resume reference
                  is managed through the career
                  profile section.
                </p>
              </div>
            </section>

            <div
              className={
                styles.saveBar
              }
            >
              <div>
                {message ? (
                  <span
                    className={
                      styles.successMessage
                    }
                  >
                    <Check size={14} />
                    {message}
                  </span>
                ) : error ? (
                  <span
                    className={
                      styles.errorMessage
                    }
                  >
                    {error}
                  </span>
                ) : dirty ? (
                  <span>
                    You have unsaved changes.
                  </span>
                ) : (
                  <span>
                    Your profile is up to date.
                  </span>
                )}
              </div>

              <div
                className={
                  styles.saveActions
                }
              >
                <button
                  type="button"
                  className={
                    styles.cancel
                  }
                  onClick={
                    cancelChanges
                  }
                  disabled={
                    !dirty || saving
                  }
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className={
                    styles.save
                  }
                  onClick={
                    saveProfile
                  }
                  disabled={
                    !dirty || saving
                  }
                >
                  {saving ? (
                    <LoaderCircle
                      size={15}
                      className="profileSpin"
                    />
                  ) : (
                    <Save size={15} />
                  )}

                  {saving
                    ? "Saving…"
                    : "Save changes"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
