"use client";

import styles from "./Section5.module.css";

type IconName =
  | "dashboard"
  | "applications"
  | "interview"
  | "offer"
  | "reminder"
  | "analytics"
  | "folder"
  | "bolt"
  | "bell"
  | "chart"
  | "arrow"
  | "review"
  | "target"
  | "search"
  | "calendar"
  | "hourglass"
  | "flag"
  | "spark"
  | "flowApplied"
  | "flowReview"
  | "flowInterview"
  | "flowOffer";

function Icon({
  name,
  size = 24,
}: {
  name: IconName;
  size?: number;
}) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "dashboard":
      return (
        <svg {...common}>
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
          <path d="M6.5 5.5h.01M17.5 5.5h.01M6.5 17.5h.01M17.5 17.5h.01" />
        </svg>
      );

    case "applications":
      return (
        <svg {...common}>
          <rect x="4" y="3.5" width="16" height="17" rx="2.5" />
          <path d="M8 3.5V2.8a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v.7" />
          <path d="M8 8h8M8 12h5M8 16h4" />
          <path d="M16.5 15.5l1.2 1.2 2.4-2.6" />
        </svg>
      );

    case "interview":
      return (
        <svg {...common}>
          <rect x="3" y="4" width="18" height="15" rx="2.5" />
          <path d="M7 9h10M7 13h6" />
          <circle cx="17" cy="15" r="2.5" />
          <path d="M15.2 17l-1.1 2.2 2.5-1.1" />
        </svg>
      );

    case "offer":
      return (
        <svg {...common}>
          <path d="M5 7.5h14v13H5z" />
          <path d="M8 7.5V5.8A2.8 2.8 0 0 1 10.8 3h2.4A2.8 2.8 0 0 1 16 5.8v1.7" />
          <path d="M5 12h14M12 7.5V20" />
          <path d="M9 12a2 2 0 0 1 3-1.7A2 2 0 0 1 15 12" />
        </svg>
      );

    case "reminder":
      return (
        <svg {...common}>
          <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 8.5h18C21 16 18 16 18 9Z" />
          <path d="M10 20a2.2 2.2 0 0 0 4 0" />
          <path d="M12 3V1.8" />
        </svg>
      );

    case "analytics":
      return (
        <svg {...common}>
          <path d="M4 19.5V14M10 19.5V9M16 19.5V5M22 19.5V2.5" />
          <path d="M3 20h20" />
          <path d="M4 11l5-4 5 2 7-6" />
          <circle cx="4" cy="11" r="1" />
          <circle cx="9" cy="7" r="1" />
          <circle cx="14" cy="9" r="1" />
          <circle cx="21" cy="3" r="1" />
        </svg>
      );

    case "folder":
      return (
        <svg {...common}>
          <path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2h7.5A2.5 2.5 0 0 1 21 9.5v8A2.5 2.5 0 0 1 18.5 20h-13A2.5 2.5 0 0 1 3 17.5Z" />
          <path d="M3 9h18" />
        </svg>
      );

    case "bolt":
      return (
        <svg {...common}>
          <path d="M13.5 2 5 13h6l-1 9 8.5-12h-6Z" />
          <path d="m13 5-3.5 5h3" />
        </svg>
      );

    case "bell":
      return (
        <svg {...common}>
          <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 8.5h18C21 16 18 16 18 9Z" />
          <path d="M9.8 20a2.5 2.5 0 0 0 4.4 0" />
          <circle cx="18.5" cy="5.5" r="2.2" />
        </svg>
      );

    case "chart":
      return (
        <svg {...common}>
          <path d="M4 19V5M4 19h17" />
          <path d="m7 15 4-4 3 2 6-7" />
          <circle cx="7" cy="15" r="1" />
          <circle cx="11" cy="11" r="1" />
          <circle cx="14" cy="13" r="1" />
          <circle cx="20" cy="6" r="1" />
        </svg>
      );

    case "arrow":
      return (
        <svg {...common}>
          <path d="M4 12h15" />
          <path d="m13 6 6 6-6 6" />
          <path d="M4 7v10" />
        </svg>
      );

    case "review":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M8 12.5 10.5 15 16 9.5" />
        </svg>
      );

    case "target":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <circle cx="12" cy="12" r="5" />
          <circle cx="12" cy="12" r="1.8" />
          <path d="m17.8 6.2 2.7-2.7M20.5 3.5v3M20.5 3.5h-3" />
        </svg>
      );

    case "search":
      return (
        <svg {...common}>
          <circle cx="10.8" cy="10.8" r="6.5" />
          <path d="m16 16 4.8 4.8" />
          <path d="M8.5 10.8h4.6M10.8 8.5v4.6" />
        </svg>
      );

    case "calendar":
      return (
        <svg {...common}>
          <rect x="3.5" y="5" width="17" height="16" rx="2.5" />
          <path d="M7 3v4M17 3v4M3.5 9.5h17" />
          <path d="M7.5 13h.01M12 13h.01M16.5 13h.01M7.5 17h.01M12 17h.01" />
        </svg>
      );

    case "hourglass":
      return (
        <svg {...common}>
          <path d="M6 3h12M6 21h12" />
          <path d="M8 3c0 4 4 5 4 9s-4 5-4 9M16 3c0 4-4 5-4 9s4 5 4 9" />
          <path d="M9 6h6M9 18h6" />
        </svg>
      );

    case "flag":
      return (
        <svg {...common}>
          <path d="M6 21V4" />
          <path d="M6 5c4-3 7 3 12 0v9c-5 3-8-3-12 0" />
          <path d="M4 21h4" />
        </svg>
      );

    case "spark":
      return (
        <svg {...common}>
          <path d="m12 2 1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5Z" />
          <path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7Z" />
        </svg>
      );

    case "flowApplied":
      return (
        <svg {...common}>
          <path d="M21 3 3.8 10.2c-.8.35-.75 1.5.08 1.75l6.15 1.9 1.9 6.15c.25.83 1.4.88 1.75.08L21 3Z" />
          <path d="m10.1 13.85 5.15-5.15" />
          <path d="m10.1 13.85-.05 5.25" />
        </svg>
      );

    case "flowReview":
      return (
        <svg {...common}>
          <path d="M6 3.5h8.5L19 8v12.5H6z" />
          <path d="M14 3.5V8h5" />
          <path d="M9 11h6M9 14.5h6M9 18h4" />
          <path d="M9 7.5h2.5" />
        </svg>
      );

    case "flowInterview":
      return (
        <svg {...common}>
          <circle cx="9" cy="8" r="3.2" />
          <circle cx="16.5" cy="9" r="2.6" />
          <path d="M3.5 19c.6-3.2 2.45-5 5.5-5s4.9 1.8 5.5 5" />
          <path d="M13.5 14.5c2.7-.4 5.1 1.1 6 3.9" />
          <path d="M4.5 12.5c-1.2-.9-1.8-2-1.8-3.3" />
        </svg>
      );

    case "flowOffer":
      return (
        <svg {...common}>
          <path d="M8.2 7.2h7.6l2.1 3.1-2.1 3.1H8.2l-2.1-3.1z" />
          <path d="M9.5 7.2V5.8A2.5 2.5 0 0 1 12 3.3a2.5 2.5 0 0 1 2.5 2.5v1.4" />
          <path d="M8.2 13.4 6.8 20.5 12 18l5.2 2.5-1.4-7.1" />
          <path d="M12 9.1v2.6M10.7 10.4h2.6" />
        </svg>
      );

    default:
      return null;
  }
}

const applications = [
  {
    role: "Product Designer",
    company: "Google",
    mark: "G",
    companyClass: "google",
    status: "Interview",
    statusClass: "purple",
    date: "Aug 28, 2026",
    next: "Prep for interview",
    nextIcon: "calendar" as IconName,
  },
  {
    role: "Frontend Engineer",
    company: "Microsoft",
    mark: "M",
    companyClass: "microsoft",
    status: "In Review",
    statusClass: "amber",
    date: "Aug 25, 2026",
    next: "Wait for update",
    nextIcon: "hourglass" as IconName,
  },
  {
    role: "UX Designer",
    company: "Netflix",
    mark: "N",
    companyClass: "netflix",
    status: "Applied",
    statusClass: "blue",
    date: "Aug 22, 2026",
    next: "Follow up in 3 days",
    nextIcon: "reminder" as IconName,
  },
  {
    role: "Data Analyst",
    company: "Amazon",
    mark: "a",
    companyClass: "amazon",
    status: "In Review",
    statusClass: "amber",
    date: "Aug 20, 2026",
    next: "Wait for update",
    nextIcon: "hourglass" as IconName,
  },
  {
    role: "Growth Manager",
    company: "Spotify",
    mark: "●",
    companyClass: "spotify",
    status: "Offer",
    statusClass: "green",
    date: "Aug 18, 2026",
    next: "Review offer",
    nextIcon: "flag" as IconName,
  },
];

const stages = [
  {
    label: "Applied",
    icon: "flowApplied" as IconName,
    className: "purple",
  },
  {
    label: "In Review",
    icon: "flowReview" as IconName,
    className: "amber",
  },
  {
    label: "Interview",
    icon: "flowInterview" as IconName,
    className: "blue",
  },
  {
    label: "Offer",
    icon: "flowOffer" as IconName,
    className: "green",
  },
];


const handleStartTracking = () => {
  const token = localStorage.getItem("ai_job_hunter_token");

  window.location.href = token ? "/dashboard" : "/signup";
};

export default function Section5() {
  return (
    <section className={styles.section} id="application-tracking">

      <div className={styles.container}>
        <div className={styles.copy}>
          <div className={styles.eyebrow}>
            <span>
              <Icon name="analytics" size={14} />
            </span>
            APPLICATION TRACKING
          </div>

          <h2>
            All your applications.
            <br />
            <span>Always in sight.</span>
          </h2>

          <p className={styles.description}>
            Track every job you apply to, see its status clearly and keep the
            next step visible.
          </p>

          <div className={styles.features}>
            <div className={styles.feature}>
              <div className={`${styles.featureIcon} ${styles.iconPurple}`}>
                <Icon name="folder" size={25} />
              </div>
              <div>
                <strong>One Place</strong>
                <span>All your applications, from every source.</span>
              </div>
            </div>

            <div className={styles.feature}>
              <div className={`${styles.featureIcon} ${styles.iconPink}`}>
                <Icon name="bolt" size={25} />
              </div>
              <div>
                <strong>Live Updates</strong>
                <span>Track status from Applied to Offer.</span>
              </div>
            </div>

            <div className={styles.feature}>
              <div className={`${styles.featureIcon} ${styles.iconOrange}`}>
                <Icon name="bell" size={25} />
              </div>
              <div>
                <strong>Smart Reminders</strong>
                <span>Get notified about interviews and follow-ups.</span>
              </div>
            </div>

            <div className={styles.feature}>
              <div className={`${styles.featureIcon} ${styles.iconBlue}`}>
                <Icon name="chart" size={25} />
              </div>
              <div>
                <strong>Stay on Top</strong>
                <span>See your progress and next steps clearly.</span>
              </div>
            </div>
          </div>

          <button className={styles.primaryButton} type="button" onClick={handleStartTracking}>
            <span>Start Tracking — Free</span>
            <Icon name="flowApplied" size={18} />
          </button>

          <div className={styles.microLine}>
            MORE CLARITY. MORE CONTROL. A CLEARER JOB SEARCH.
          </div>
        </div>

        <div className={styles.visual}>
          <div className={styles.mountain}>
            <div className={styles.mountainGlow} />
            <div className={styles.mountainBack} />
            <div className={styles.mountainFront} />
            <div className={styles.mountainPath} />
            <span className={styles.mountainStar}>✦</span>
          </div>



          <div className={styles.dashboard}>
            <aside className={styles.sidebar}>
              <div className={styles.brand}>
                <span className={styles.brandIcon}>
                  <Icon name="spark" size={16} />
                </span>
                <strong>AI Job Hunter</strong>
              </div>

              <nav className={styles.navigation}>
                <div className={styles.navItem}>
                  <Icon name="dashboard" size={15} />
                  <span>Dashboard</span>
                </div>

                <div className={`${styles.navItem} ${styles.navActive}`}>
                  <Icon name="applications" size={15} />
                  <span>My Applications</span>
                </div>

                <div className={styles.navItem}>
                  <Icon name="interview" size={15} />
                  <span>Interviews</span>
                </div>

                <div className={styles.navItem}>
                  <Icon name="offer" size={15} />
                  <span>Offers</span>
                </div>

                <div className={styles.navItem}>
                  <Icon name="reminder" size={15} />
                  <span>Reminders</span>
                </div>

                <div className={styles.navItem}>
                  <Icon name="analytics" size={15} />
                  <span>Analytics</span>
                </div>
              </nav>
            </aside>

            <div className={styles.dashboardMain}>
              <div className={styles.dashboardHeader}>
                <div className={styles.mobileBrand}>
                  <span>
                    <Icon name="spark" size={13} />
                  </span>
                  AI Job Hunter
                </div>

                <div className={styles.search}>
                  <Icon name="search" size={14} />
                  <span>Search jobs, companies...</span>
                </div>

                <div className={styles.avatar}>TR</div>
              </div>

              <div className={styles.dashboardTitle}>
                <div>
                  <span>APPLICATION TRACKING</span>
                  <h3>My Applications</h3>
                </div>
                <div className={styles.menu}>•••</div>
              </div>

              <div className={styles.summaryCards}>
                <div className={`${styles.summaryCard} ${styles.summaryBlue}`}>
                  <span className={styles.summaryIcon}>
                    <Icon name="flowApplied" size={21} />
                  </span>
                  <div>
                    <strong>48</strong>
                    <span>Applied</span>
                  </div>
                </div>

                <div className={`${styles.summaryCard} ${styles.summaryAmber}`}>
                  <span className={styles.summaryIcon}>
                    <Icon name="review" size={21} />
                  </span>
                  <div>
                    <strong>12</strong>
                    <span>In Review</span>
                  </div>
                </div>

                <div className={`${styles.summaryCard} ${styles.summaryPurple}`}>
                  <span className={styles.summaryIcon}>
                    <Icon name="target" size={21} />
                  </span>
                  <div>
                    <strong>8</strong>
                    <span>Interview</span>
                  </div>
                </div>

                <div className={`${styles.summaryCard} ${styles.summaryGreen}`}>
                  <span className={styles.summaryIcon}>
                    <Icon name="offer" size={21} />
                  </span>
                  <div>
                    <strong>3</strong>
                    <span>Offer</span>
                  </div>
                </div>
              </div>

              <div className={styles.applicationTable}>
                <div className={styles.tableHeader}>
                  <span>JOB TITLE</span>
                  <span>COMPANY</span>
                  <span>STATUS</span>
                  <span>APPLIED ON</span>
                  <span>NEXT STEP</span>
                  <span />
                </div>

                {applications.map((application) => (
                  <div
                    className={styles.applicationRow}
                    key={`${application.role}-${application.company}`}
                  >
                    <div className={styles.roleCell}>
                      <span className={styles.roleIcon}>
                        <Icon name="spark" size={12} />
                      </span>
                      <strong>{application.role}</strong>
                    </div>

                    <div className={styles.companyCell}>
                      <span
                        className={`${styles.companyMark} ${
                          styles[application.companyClass]
                        }`}
                      >
                        {application.mark}
                      </span>
                      <span>{application.company}</span>
                    </div>

                    <span
                      className={`${styles.statusPill} ${
                        styles[application.statusClass]
                      }`}
                    >
                      <i />
                      {application.status}
                    </span>

                    <span className={styles.dateCell}>
                      {application.date}
                    </span>

                    <div className={styles.nextCell}>
                      <Icon name={application.nextIcon} size={15} />
                      <span>{application.next}</span>
                    </div>

                    <span className={styles.rowMenu}>•••</span>
                  </div>
                ))}
              </div>

              <div className={styles.dashboardBottom}>
                <span className={styles.bottomIcon}>
                  <Icon name="reminder" size={15} />
                </span>
                <div>
                  <strong>Keep the next step visible</strong>
                  <span>Follow-ups and upcoming actions stay easy to spot.</span>
                </div>
                <span className={styles.bottomArrow}>→</span>
              </div>
            </div>
          </div>

          <div className={styles.reminderCard}>
            <span className={styles.reminderIcon}>
              <Icon name="bell" size={24} />
            </span>
            <div>
              <strong>Interview Reminder</strong>
              <span>Google · Product Designer</span>
              <span>Tomorrow · 11:00 AM</span>
            </div>
            <span className={styles.reminderArrow}>→</span>
          </div>


        </div>
      </div>

      <div className={styles.bottomFlow}>
        {stages.map((stage, index) => (
          <div className={styles.flowStage} key={stage.label}>
            <div
              className={`${styles.flowIcon} ${
                styles[`flow${stage.className}`]
              }`}
            >
              <Icon name={stage.icon} size={21} />
            </div>

            <strong>{stage.label}</strong>

            {index < stages.length - 1 && (
              <div className={styles.flowConnector}>
                <span />
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
