import {
  ChevronDown,
  BriefcaseBusiness,
  UserRound,
  Sparkles,
} from "lucide-react";

interface HeaderProps {
  profileId: string;
  profiles: string[];
  onProfileChange: (profileId: string) => void;
}

function formatProfile(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function Header({
  profileId,
  profiles,
  onProfileChange,
}: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-mark">
          <Sparkles size={17} strokeWidth={2.5} />
        </div>
        <div className="brand-copy">
          <div className="brand-title">AI Job Hunter</div>
          <div className="brand-subtitle">Intelligent career matching</div>
        </div>
      </div>

      <div className="header-actions">
        <label className="profile-select">
          <BriefcaseBusiness size={14} />
          <select
            value={profileId}
            onChange={(event) => onProfileChange(event.target.value)}
            aria-label="Select profile"
          >
            <option value="">Select profile</option>
            {profiles.map((profile) => (
              <option key={profile} value={profile}>
                {formatProfile(profile)}
              </option>
            ))}
          </select>
          <ChevronDown size={14} />
        </label>

        <div className="user-chip" aria-label="Current candidate">
          <span className="user-avatar">
            <UserRound size={14} />
          </span>
          <span className="user-label">Candidate</span>
        </div>
      </div>
    </header>
  );
}

