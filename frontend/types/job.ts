export interface ScoreBreakdown {
  skill_match: number;
  tool_match: number;
  experience_match: number;
  salary_match: number;
  work_mode_match: number;
  jd_match?: number | null;
  title_match?: number | null;
  negative_penalty?: number | null;
  matched_skills: string[];
  matched_tools: string[];
  missing_skills: string[];
  missing_tools: string[];
  strengths: string[];
}

export interface Job {
  job_id: string;
  title: string;
  company: string;
  location: string | null;
  portal: string | null;
  job_url?: string | null;
  posted_date?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  experience_min?: number | null;
  experience_max?: number | null;
  employment_type?: string | null;
  skills: string[];
  overall_score: number | null;
  skill_score: number | null;
  tool_score: number | null;
  experience_score: number | null;
  salary_score: number | null;
  work_mode_score: number | null;
  score_breakdown?: ScoreBreakdown | null;
  search_score?: number | null;
  match_reason?: string[];
  rank?: number | null;
}

export interface JobListResponse {
  total: number;
  page: number;
  page_size: number;
  jobs: Job[];
}

export interface JobFilterOptions {
  locations: string[];
  skills: string[];
  tools: string[];
  portals: string[];
  companies: string[];
}

export interface DashboardSummary {
  total_jobs: number;
  average_score: number;
  high_match_jobs: number;
  companies_count: number;
  locations_count: number;
  latest_search_date: string | null;
}

export interface JobDetail extends Job {
  description: string | null;

  score?: {
    job_id: string;
    profile_id: string;
    overall_score: number;
    skill_score: number;
    tool_score: number;
    experience_score: number;
    salary_score: number;
    work_mode_score: number;
    score_breakdown?: ScoreBreakdown | null;
    scored_at?: string | null;
  } | null;

  search_score?: number | null;
  match_reason?: string[];
}
