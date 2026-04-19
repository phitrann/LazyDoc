export type LanguageItem = {
  name: string;
  percentage: number;
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
};

export type ResearchResponse = {
  status: "success" | "partial";
  data: ResearchData;
  warnings: string[];
};
