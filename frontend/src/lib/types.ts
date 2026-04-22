export type LanguageItem = {
  name: string;
  percentage: number;
};

export type TrendingRepository = {
  handle: string;
  description: string;
  stars: string;
  url: string;
};

export type ResearchData = {
  overview: {
    name: string;
    owner: string;
    description: string | null;
    stars: number;
    forks: number;
    last_updated: string;
    url: string;
    default_branch: string;
  };
  insights: {
    primary_language: string | null;
    languages: LanguageItem[];
    license_name: string | null;
    has_license: boolean;
    dependency_files: string[];
  };
  activity: {
    recent_commits_last_7_days: number;
    recent_commits_last_30_days: number;
    last_commit_date: string | null;
    total_contributors: number;
    active_contributors_last_30_days: number;
  };
  structure: {
    total_files: number;
    has_readme: boolean;
    has_license: boolean;
    top_directories: string[];
  };
  code_health?: CodeHealth | null;
};

export type ResearchResponse = {
  status: "success" | "partial";
  data: ResearchData;
  warnings: string[];
  rate_limit?: RateLimit;
};

export type DocumentationSection = {
  title: string;
  summary: string;
  content: string[];
};

export type DocumentationAiSection = "all" | "readme_summary" | "recommendations" | "risk_observations";

export type DocumentationData = ResearchData & {
  sections: DocumentationSection[];
  markdown: string;
  readme_summary: string | null;
  recommendations: string[];
  risk_observations: string[];
};

export type CodeHealthFinding = {
  id: string;
  category: "security" | "architecture" | "maintenance";
  rule_name: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  confidence: "High" | "Medium" | "Low";
  file_path: string;
  line: number;
  message: string;
  suggestion: string;
  impact_area: "Security" | "Architecture" | "Maintenance";
  evidence: string;
  why_it_matters: string;
};

export type LLMRankedFinding = {
  id: string;
  impact_priority: number;
  business_context: string;
  remediation_steps: string[];
  is_false_positive: boolean;
  automation_opportunity: string | null;
};

export type LLMInsights = {
  ranked_findings: LLMRankedFinding[];
  executive_summary: string;
  source: string;
};

export type CodeHealth = {
  grade: "A" | "B" | "C" | "D" | "F" | "N/A";
  score: number;
  summary: string;
  metrics: {
    scanned_files: number;
    source_files_detected: number;
    security_findings: number;
    architecture_findings: number;
    maintenance_findings: number;
    critical_findings: number;
    high_findings: number;
    medium_findings: number;
    low_findings: number;
    circular_dependencies: number;
    coupling_index: number;
    orphan_file_percent: number;
  };
  breakdown: Array<{
    name: string;
    score: number;
    impact: number;
    drivers: string[];
  }>;
  findings: CodeHealthFinding[];
  llm_insights?: LLMInsights | null;
  warnings?: string[];
};

export type RateLimit = {
  remaining: number;
  limit: number;
  reset_unix_timestamp: number;
  reset_in_seconds: number;
};

export type DocumentationResponse = {
  status: "success" | "partial";
  data: DocumentationData;
  warnings: string[];
  rate_limit?: RateLimit;
};
