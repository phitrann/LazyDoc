"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { GitHubPatInput } from "@/components/GitHubPatInput";
import { MetricCard } from "@/components/MetricCard";
import { RateLimitBanner } from "@/components/RateLimitBanner";
import { SectionCard } from "@/components/SectionCard";
import { StatusBanner } from "@/components/StatusBanner";
import { generateDocumentation, streamDocumentationAiSection } from "@/lib/api";
import type { DocumentationResponse } from "@/lib/types";

const defaultRepository = "https://github.com/phitrann/LazyDoc";

export function ReportClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialRepository = searchParams.get("repo") || defaultRepository;

  const [repositoryUrl, setRepositoryUrl] = useState(initialRepository);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<DocumentationResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTocId, setActiveTocId] = useState("repository-overview");
  const [aiStreaming, setAiStreaming] = useState(false);
  const [aiStreamingStatus, setAiStreamingStatus] = useState<string | null>(null);
  const [githubToken, setGithubToken] = useState<string | null>(null);

  async function loadReport(targetRepository: string, forceRegenerate = false) {
    const trimmed = targetRepository.trim();
    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);
    setCopied(false);

    try {
      const result = await generateDocumentation(trimmed, forceRegenerate, githubToken ?? undefined);
      setReport(result);
    } catch (caughtError) {
      setReport(null);
      setError(caughtError instanceof Error ? caughtError.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = repositoryUrl.trim();
    if (!trimmed) {
      return;
    }
    router.replace(`/report?repo=${encodeURIComponent(trimmed)}`);
    void loadReport(trimmed);
  }

  async function handleCopyMarkdown() {
    if (!report?.data.markdown) {
      return;
    }
    await navigator.clipboard.writeText(report.data.markdown);
    setCopied(true);
  }

  async function handleRegenerateAiContent() {
    const trimmed = repositoryUrl.trim();
    if (!trimmed) {
      return;
    }

    setAiStreaming(true);
    setAiStreamingStatus("Preparing AI section...");
    setError(null);
    setReport((previous) => {
      if (!previous) {
        return previous;
      }
      return {
        ...previous,
        data: {
          ...previous.data,
          readme_summary: "",
          recommendations: [],
          risk_observations: [],
        },
      };
    });

    try {
      await streamDocumentationAiSection(trimmed, true, {
        onStage: (_stage, message) => {
          setAiStreamingStatus(message);
        },
        onToken: (field, token) => {
          if (field !== "readme_summary") {
            return;
          }
          setReport((previous) => {
            if (!previous) {
              return previous;
            }
            return {
              ...previous,
              data: {
                ...previous.data,
                readme_summary: `${previous.data.readme_summary ?? ""}${token}`,
              },
            };
          });
        },
        onUpdate: (update) => {
          setReport((previous) => {
            if (!previous) {
              return previous;
            }
            return {
              ...previous,
              data: {
                ...previous.data,
                readme_summary: update.readme_summary ?? previous.data.readme_summary,
                recommendations: update.recommendations ?? previous.data.recommendations,
                risk_observations: update.risk_observations ?? previous.data.risk_observations,
              },
            };
          });
        },
        onComplete: (update) => {
          setReport((previous) => {
            if (!previous) {
              return previous;
            }
            return {
              ...previous,
              status: (update.warnings?.length ? "partial" : "success") as "success" | "partial",
              warnings: update.warnings ?? [],
              data: {
                ...previous.data,
                readme_summary: update.readme_summary ?? previous.data.readme_summary,
                recommendations: update.recommendations ?? previous.data.recommendations,
                risk_observations: update.risk_observations ?? previous.data.risk_observations,
                sections: update.sections ?? previous.data.sections,
                markdown: update.markdown ?? previous.data.markdown,
              },
            };
          });
        },
      }, githubToken ?? undefined);
      setAiStreamingStatus("AI section updated.");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Something went wrong.");
    } finally {
      setAiStreaming(false);
      setTimeout(() => {
        setAiStreamingStatus(null);
      }, 1500);
    }
  }

  useEffect(() => {
    const repo = searchParams.get("repo");
    if (!repo) {
      return;
    }
    setRepositoryUrl(repo);
    void loadReport(repo);
  }, [searchParams]);

  const markdownPreview = useMemo(() => report?.data.markdown.trim(), [report]);

  const overview = report?.data.overview;
  const insights = report?.data.insights;
  const activity = report?.data.activity;
  const structure = report?.data.structure;
  const hasDocumentationIntelligence = Boolean(
    aiStreaming || report?.data.readme_summary || report?.data.recommendations.length || report?.data.risk_observations.length
  );
  const hasGeneratedSections = Boolean(report?.data.sections.length);
  const readmeSummary = useMemo(() => report?.data.readme_summary?.trim(), [report]);

  const tocItems = useMemo(
    () => [
      { id: "repository-overview", label: "Repository Overview" },
      { id: "project-insights", label: "Project Insights" },
      { id: "activity-health", label: "Activity & Health" },
      { id: "structure-summary", label: "Structure Summary" },
      ...(hasDocumentationIntelligence ? [{ id: "documentation-intelligence", label: "Documentation Intelligence" }] : []),
      { id: "generated-markdown", label: "Generated Markdown" },
      ...(hasGeneratedSections ? [{ id: "report-sections", label: "Report Sections" }] : []),
    ],
    [hasDocumentationIntelligence, hasGeneratedSections]
  );

  useEffect(() => {
    const sections = tocItems
      .map((item) => document.getElementById(item.id))
      .filter((element): element is HTMLElement => Boolean(element));

    if (!sections.length) {
      return;
    }

    setActiveTocId(sections[0].id);

    const visibleRatios = new Map<string, number>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          visibleRatios.set(entry.target.id, entry.isIntersecting ? entry.intersectionRatio : 0);
        }

        const mostVisible = [...visibleRatios.entries()]
          .filter(([, ratio]) => ratio > 0)
          .sort((left, right) => right[1] - left[1])[0];

        if (mostVisible) {
          setActiveTocId(mostVisible[0]);
        }
      },
      {
        root: null,
        rootMargin: "-20% 0px -55% 0px",
        threshold: [0, 0.15, 0.35, 0.6, 1],
      }
    );

    for (const section of sections) {
      observer.observe(section);
    }

    return () => {
      observer.disconnect();
    };
  }, [tocItems, report]);

  return (
    <div className="report-shell">
      <header className="top-nav">
        <div className="top-nav-inner">
          <div className="nav-left">
            <Link href="/" className="back-link">
              ← Home
            </Link>
            <div className="brand">LazyDoc</div>
          </div>
          <div className="nav-meta">
            <p>Technical Repository Report</p>
          </div>
        </div>
      </header>

      <main className="report-content">
        <section className="hero-card light-hero">
          <p className="eyebrow">LazyDoc Report</p>
          <h1>Generated repository research output</h1>
          <p className="hero-copy">Analyze any public repository and review normalized metrics, AI summaries, and reusable markdown output.</p>

          <form className="search-form" onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="repository-url-report">
              Repository URL
            </label>
            <div className="search-row">
              <input
                id="repository-url-report"
                type="url"
                value={repositoryUrl}
                onChange={(event) => setRepositoryUrl(event.target.value)}
                placeholder="https://github.com/owner/repo"
              />
              <button type="submit" disabled={loading}>
                {loading ? "Generating..." : "Research"}
              </button>
            </div>
          </form>

          <GitHubPatInput onTokenChange={setGithubToken} disabled={loading} />

          {report?.rate_limit && <RateLimitBanner rateLimit={report.rate_limit} hasGithubToken={!!githubToken} />}

          {error ? <StatusBanner kind="error" message={error} /> : null}
          {report?.warnings?.length ? <StatusBanner kind="warning" message={report.warnings.join(" ")} /> : null}
          {copied ? <StatusBanner kind="warning" message="Markdown copied to clipboard." /> : null}
        </section>

        {overview && insights && activity && structure ? (
          <div className="report-layout">
            <aside className="report-toc" aria-label="Table of contents">
              <h2>Table of contents</h2>
              <ul>
                {tocItems.map((item) => (
                  <li key={item.id}>
                    <a
                      href={`#${item.id}`}
                      className={activeTocId === item.id ? "toc-link active" : "toc-link"}
                      onClick={() => setActiveTocId(item.id)}
                      aria-current={activeTocId === item.id ? "location" : undefined}
                    >
                      {item.label}
                    </a>
                  </li>
                ))}
              </ul>
            </aside>

            <section className="report-grid report-grid-light">
              <p className="ai-legend">Sections tagged AI-generated include model-assisted summaries, recommendations, or risk observations.</p>

            <SectionCard id="repository-overview" title="Repository Overview" description="Core metadata and ownership.">
              <div className="metric-grid">
                <MetricCard label="Name" value={overview.name} />
                <MetricCard label="Owner" value={overview.owner} />
                <MetricCard label="Stars" value={String(overview.stars)} />
                <MetricCard label="Forks" value={String(overview.forks)} />
                <MetricCard label="Updated" value={new Date(overview.last_updated).toLocaleDateString()} />
              </div>
              <p className="section-note">{overview.description || "No description provided."}</p>
            </SectionCard>

            <SectionCard id="project-insights" title="Project Insights" description="Languages and dependency hints.">
              <div className="metric-grid">
                <MetricCard label="Primary language" value={insights.primary_language || "Unknown"} />
                <MetricCard label="Has license" value={insights.has_license ? "Yes" : "No"} />
                <MetricCard
                  label="Dependency files"
                  value={insights.dependency_files.length ? insights.dependency_files.join(", ") : "None detected"}
                />
              </div>
              <div className="tag-row">
                {insights.languages.map((language) => (
                  <span key={language.name} className="tag">
                    {language.name} {language.percentage}%
                  </span>
                ))}
              </div>
            </SectionCard>

            <SectionCard id="activity-health" title="Activity & Health" description="Recent commit and contributor signals.">
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

            <SectionCard id="structure-summary" title="Structure Summary" description="Lightweight repository shape summary.">
              <div className="metric-grid">
                <MetricCard label="Files" value={String(structure.total_files)} />
                <MetricCard label="README" value={structure.has_readme ? "Present" : "Missing"} />
                <MetricCard label="License" value={structure.has_license ? "Present" : "Missing"} />
              </div>
              <p className="section-note">
                Top directories: {structure.top_directories.length ? structure.top_directories.join(", ") : "None detected"}
              </p>
            </SectionCard>

            {hasDocumentationIntelligence ? (
              <SectionCard
                id="documentation-intelligence"
                title="Documentation Intelligence"
                description="README summary, recommendations, and risk signals."
                badges={["AI-generated"]}
              >
                <div className="ai-actions">
                  <button type="button" onClick={handleRegenerateAiContent} disabled={loading || aiStreaming}>
                    {aiStreaming ? "Streaming AI update..." : loading ? "Re-generating..." : "Re-generate AI content"}
                  </button>
                </div>
                {aiStreamingStatus ? <p className="section-note">{aiStreamingStatus}</p> : null}
                {readmeSummary ? (
                  <div className="markdown-render markdown-compact">
                    <h3>README Summary</h3>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{readmeSummary}</ReactMarkdown>
                  </div>
                ) : null}
                {report.data.recommendations.length ? (
                  <div className="content-list">
                    <h3>Recommendations</h3>
                    <ul>
                      {report.data.recommendations.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {report.data.risk_observations.length ? (
                  <div className="content-list">
                    <h3>Security & Risk Observations</h3>
                    <ul>
                      {report.data.risk_observations.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </SectionCard>
            ) : null}

            <SectionCard id="generated-markdown" title="Generated Markdown" description="Copy the rendered report or reuse it in documentation workflows.">
              <div className="markdown-actions">
                <button type="button" onClick={handleCopyMarkdown} disabled={!report?.data.markdown}>
                  Copy Markdown
                </button>
              </div>
              {markdownPreview ? (
                <div className="markdown-render markdown-preview-rendered">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdownPreview}</ReactMarkdown>
                </div>
              ) : (
                <p className="section-note">No markdown generated yet.</p>
              )}
            </SectionCard>

            {hasGeneratedSections ? (
              <SectionCard id="report-sections" title="Report Sections" description="The generated report is broken into reusable sections." badges={["AI-assisted"]}>
                <div className="section-stack">
                  {report.data.sections.map((section) => (
                    <article key={section.title} className="generated-section">
                      <h3>{section.title}</h3>
                      <p>{section.summary}</p>
                      {section.content.length ? (
                        <ul>
                          {section.content.map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      ) : null}
                    </article>
                  ))}
                </div>
              </SectionCard>
            ) : null}
            </section>
          </div>
        ) : null}
      </main>
    </div>
  );
}
