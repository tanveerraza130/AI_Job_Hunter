export interface ManagedProfile {
  user_id: string;
  full_name: string;
  phone: string | null;
  profile_id: string;
  preferred_location: string;
  role_level: string;
  experience_years: string;
  current_ctc_lpa: number;
  expected_ctc_lpa: number;
  resume_path: string | null;
}

export interface ProfileFormState {
  full_name: string;
  phone: string;
  preferred_location: string;
  role_level: string;
  experience_years: string;
  current_ctc_lpa: string;
  expected_ctc_lpa: string;
  resume_path: string;
}
