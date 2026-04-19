"use client";

import { FormEvent, useState } from "react";

import { analyzeRepository } from "@/lib/api";
import type { ResearchResponse } from "@/lib/types";
import { MetricCard } from "@/components/MetricCard";
import { SectionCard } from "@/components/SectionCard";
import { StatusBanner } from "@/components/StatusBanner";

export default function HomePage() {
  const [repositoryUrl, setRepositoryUrl] = useState("https://github.com/vercel/next.js");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ResearchResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const result = await analyzeRepository(repositoryUrl);
      setReport(result);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const overview = report?.data.overview;
  const insights = report?.data.insights;
  const activity = report?.data.activity;
  const structure = report?.data.structure;

  return (
    <main className="page-shell">
      <section className="hero-card">
        <p className="eyebrow">GitHub Repository Research Tool</p>
        <h1>Start simple, then add depth only when it helps the report.</h1>
        <p className="hero-copy">
          Enter a public GitHub repository URL, press Research, and get a concise report with overview, insights,
          activity, and structure signals.
        </p>

        <form className="search-form" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="repository-url">
            Repository URL
          </label>
          <div className="search-row">
            <input
              id="repository-url"
              type="url"
              value={repositoryUrl}
              onChange={(event) => setRepositoryUrl(event.target.value)}
              placeholder="https://github.com/owner/repo"
            />
            <button type="submit" disabled={loading}>
              {loading ? "Researching..." : "Research"}
            </button>
          </div>
        </form>

        {error ? <StatusBanner kind="error" message={error} /> : null}
        {report?.warnings?.length ? <StatusBanner kind="warning" message={report.warnings.join(" ")} /> : null}
      </section>

      {overview && insights && activity && structure ? (
        <section className="report-grid">
          <SectionCard title="Repository Overview" description="Core metadata and ownership.">
            <div className="metric-grid">
              <MetricCard label="Name" value={overview.name} />
              <MetricCard label="Owner" value={overview.owner} />
              <MetricCard label="Stars" value={String(overview.stars)} />
              <MetricCard label="Forks" value={String(overview.forks)} />
              <MetricCard label="Updated" value={new Date(overview.last_updated).toLocaleDateString()} />
            </div>
            <p className="section-note">{overview.description || "No description provided."}</p>
          </SectionCard>

          <SectionCard title="Project Insights" description="Languages and dependency hints.">
            <div className="metric-grid">
              <MetricCard label="Primary language" value={insights.primary_language || "Unknown"} />
              <MetricCard label="Has license" value={insights.has_license ? "Yes" : "No"} />
              <MetricCard label="Dependency files" value={insights.dependency_files.length ? insights.dependency_files.join(", ") : "None detected"} />
            </div>
            <div className="tag-row">
              {insights.languages.map((language) => (
                <span key={language.name} className="tag">
                  {language.name} {language.percentage}%
                </span>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Activity & Health" description="Recent commit and contributor signals.">
            <div className="metric-grid">
              <MetricCard label="Commits last 7 days" value={String(activity.recent_commits_last_7_days)} />
              <MetricCard label="Commits last 30 days" value={String(activity.recent_commits_last_30_days)} />
              <MetricCard label="Contributors" value={String(activity.total_contributors)} />
              <MetricCard label="Active contributors" value={String(activity.active_contributors_last_30_days)} />
            </div>
            <p className="section-note">
              {activity.last_commit_date ? `Last commit: ${new Date(activity.last_commit_date).toLocaleString()}` : "No commit data detected."}
            </p>
          </SectionCard>

          <SectionCard title="Structure Summary" description="Lightweight repository shape summary.">
            <div className="metric-grid">
              <MetricCard label="Files" value={String(structure.total_files)} />
              <MetricCard label="README" value={structure.has_readme ? "Present" : "Missing"} />
              <MetricCard label="License" value={structure.has_license ? "Present" : "Missing"} />
            </div>
            <p className="section-note">
              Top directories: {structure.top_directories.length ? structure.top_directories.join(", ") : "None detected"}
            </p>
          </SectionCard>
        </section>
      ) : null}
    </main>
  );
}
