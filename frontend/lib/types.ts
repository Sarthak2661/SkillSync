export type Kpis = {
  run_id: string;
  job_postings: number;
  course_listings: number;
  unique_skills: number;
  high_opportunity_skills: number;
  high_value_skills: number;
  historical_runs_available: number;
  quality_warnings: number;
  job_skill_coverage: number;
  course_skill_coverage: number;
  top_opportunity_skill: string;
};

export type SkillGap = {
  skill: string;
  category: string;
  job_demand: number;
  course_supply: number;
  gap_score: number;
  demand_score: number;
  growth_score: number;
  salary_premium_score: number;
  course_supply_score: number;
  saturation_score: number;
  opportunity_index: number;
  opportunity_label: string;
  market_direction: string;
  target_job_roles: string;
  role_families: string;
  onet_wage_median_annual?: number | null;
  onet_growth_outlook?: string | null;
  bls_growth_percent?: number | null;
  onet_soc_codes?: string | null;
  onet_reference_url?: string | null;
  taxonomy_source?: string | null;
};

export type Trend = {
  run_id: string;
  run_timestamp: string;
  source_name: string;
  skill: string;
  job_count: number;
  course_count: number;
  salary_min_avg?: number | null;
  salary_max_avg?: number | null;
  location: string;
  role_category: string;
  role_family: string;
};

export type Job = {
  external_id: string;
  source_name: string;
  source_confidence: string;
  title: string;
  company: string;
  location: string;
  role_category: string;
  role_family: string;
  remote_type: string;
  salary_min?: number | null;
  salary_max?: number | null;
  skills: string;
  url: string;
};

export type Course = {
  external_id: string;
  source_name: string;
  source_confidence: string;
  title: string;
  platform: string;
  level: string;
  rating?: number | null;
  duration_minutes?: number | null;
  skills: string;
  role_families: string;
  url: string;
};

export type Certification = {
  skill: string;
  certification_name: string;
  provider: string;
  level: string;
  free_or_paid: string;
  estimated_cost_usd: number;
  source_name?: string;
  source_confidence?: string;
  last_verified?: string;
  target_roles: string;
  role_families: string;
  url: string;
  recommendation_score: number;
  opportunity_index: number;
};

export type QualityCheck = {
  dataset: string;
  check_name: string;
  status: string;
  severity: string;
  records_checked: number;
  failed_count: number;
  message: string;
};

export type Source = {
  dataset: string;
  source_name: string;
  source_confidence: string;
  record_count: number;
};

export type SourceRun = {
  run_id: string;
  source_name: string;
  source_type: string;
  status: "success" | "empty" | "failed";
  record_count: number;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  error_type?: string | null;
  error_message?: string | null;
};

export type Run = Record<string, string | number | null>;

export type SchedulerStatus = {
  interval_minutes: number;
  run_on_start: boolean;
  latest_run_timestamp?: string | null;
  estimated_next_run?: string | null;
};

export type WeeklySkill = {
  skill: string;
  job_count: number;
  course_count: number;
  role_families: string;
  opportunity_index?: number | null;
};

export type WeeklyMovement = {
  skill: string;
  current: number;
  previous: number;
  change: number;
};

export type WeeklyReport = {
  report_id: string;
  run_id: string;
  published_at: string;
  week_start: string;
  week_end: string;
  title: string;
  summary: string;
  jobs: number;
  courses: number;
  skills: number;
  top_opportunity_skill: string;
  top_skills: WeeklySkill[];
  rising_skills: WeeklyMovement[];
  declining_skills: WeeklyMovement[];
  status: string;
  methodology_note: string;
};

export type PracticeIssue = {
  repository: string;
  issue_title: string;
  practice_label: string;
  language?: string | null;
  stars: number;
  issue_updated_at: string;
  issue_url: string;
};

export type PracticeResponse = {
  items: PracticeIssue[];
  topic: string;
  status: string;
  message: string;
  authenticated: boolean;
  rate_limit_remaining?: number | null;
  fetched_at: string;
};

export type SkillProfile = {
  skill: string;
  gap: SkillGap;
  job_count: number;
  course_count: number;
  sample_jobs: Job[];
  sample_courses: Course[];
};


