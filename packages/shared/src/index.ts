export type Severity = "info" | "low" | "medium" | "high" | "critical";

export type RiskLevel = "low" | "moderate" | "high";

export type RiskCategory =
  | "authentication"
  | "authorization"
  | "database"
  | "api"
  | "dependencies"
  | "configuration"
  | "infrastructure"
  | "security"
  | "payments"
  | "data_handling"
  | "ci_cd"
  | "environment"
  | "complexity"
  | "testing"
  | "change"
  | "impact"
  | "other";

export type FileStatus =
  | "added"
  | "modified"
  | "removed"
  | "renamed"
  | "copied"
  | "changed"
  | "unchanged";

export type FileArea =
  | "ui"
  | "api"
  | "service"
  | "data_model"
  | "database"
  | "auth"
  | "config"
  | "infra"
  | "ci"
  | "test"
  | "docs"
  | "styles"
  | "dependency"
  | "constants"
  | "hooks_state"
  | "other";

export interface ChangedFile {
  filename: string;
  status: FileStatus;
  additions: number;
  deletions: number;
  changes: number;
  patch: string | null;
  previous_filename: string | null;
  language: string | null;
  is_test_file: boolean;
  is_generated_file: boolean;
  is_binary: boolean;
  role: string;
  area: FileArea;
}

export interface PullRequest {
  id: number;
  number: number;
  title: string;
  description: string | null;
  author: string;
  repository: string;
  owner: string;
  base_branch: string;
  head_branch: string;
  head_sha: string;
  created_at: string | null;
  updated_at: string | null;
  state: string;
  additions: number;
  deletions: number;
  changed_files_count: number;
  commits: Array<{
    sha: string;
    message: string;
    author: string | null;
    committed_at: string | null;
  }>;
  changed_files: ChangedFile[];
  html_url: string;
  is_private: boolean;
}

export interface Viewer {
  oauth_enabled: boolean;
  authenticated: boolean;
  login: string | null;
  avatar_url: string | null;
}

export type PullRequestFilter = "authored" | "review_requested" | "assigned";

export interface OpenPullRequest {
  owner: string;
  repo: string;
  number: number;
  title: string;
  html_url: string;
  author_login: string | null;
  author_avatar_url: string | null;
  draft: boolean;
  comments: number;
  labels: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface OpenPullRequestsResponse {
  filter: PullRequestFilter;
  total_count: number;
  items: OpenPullRequest[];
}

export interface RiskFinding {
  id: string;
  severity: Severity;
  category: RiskCategory;
  title: string;
  description: string;
  file: string | null;
  line_start: number | null;
  line_end: number | null;
  evidence: string;
  confidence: number;
  source: string;
  recommendation: string | null;
  files: string[];
}

export interface ChangeStatistics {
  total_files: number;
  additions: number;
  deletions: number;
  net_change: number;
  files_added: number;
  files_modified: number;
  files_deleted: number;
  files_renamed: number;
  binary_files: number;
  file_type_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  role_distribution: Record<string, number>;
  area_distribution: Record<string, number>;
  area_churn: Record<string, { additions: number; deletions: number }>;
}

export interface ComplexityObservation {
  file: string;
  language: string;
  function_count: number;
  class_count: number;
  max_nesting_depth: number;
  max_cyclomatic_complexity: number | null;
  large_functions: string[];
  complex_functions: Array<Record<string, unknown>>;
  notes: string[];
}

export interface TestingAnalysis {
  test_files_added: number;
  test_files_modified: number;
  test_files_deleted: number;
  production_files_changed: number;
  test_to_source_ratio: number | null;
  test_directory_present: boolean;
  frameworks_detected: string[];
  findings: RiskFinding[];
}

export interface DependencyChange {
  name: string;
  change_type: string;
  ecosystem: string;
  old_version: string | null;
  new_version: string | null;
  file: string;
}

export interface DependencyEdge {
  source: string;
  target: string;
  relationship: string;
  confidence: number;
}

export interface ActionItem {
  priority: number;
  title: string;
  detail: string;
  files: string[];
}

export interface ReviewSummary {
  risk_level: RiskLevel;
  headline: string;
  overview: string;
  highlights: string[];
  action_items: ActionItem[];
}

export interface AIAnalysis {
  summary: string | null;
  key_changes: string[];
  risk_observations: string[];
  testing_observations: string[];
  review_questions: string[];
  additional_findings: RiskFinding[];
  provider: string;
  model: string | null;
  generated_at: string;
}

export interface AnalysisReport {
  pr: PullRequest;
  summary: string;
  statistics: ChangeStatistics;
  complexity: ComplexityObservation[];
  risks: RiskFinding[];
  testing: TestingAnalysis;
  dependencies: DependencyChange[];
  dependency_edges: DependencyEdge[];
  review_questions: string[];
  analyzed_at: string;
  analyzer_version: string;
  partial: boolean;
  partial_message: string | null;
  files_analyzed: number;
  files_total: number;
  ai_analysis: AIAnalysis | null;
  review: ReviewSummary | null;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
