"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { GitHubPatInput } from "@/components/GitHubPatInput";
import { MetricCard } from "@/components/MetricCard";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { RateLimitBanner } from "@/components/RateLimitBanner";
import { SectionCard } from "@/components/SectionCard";
import { StatusBanner } from "@/components/StatusBanner";
import { generateDocumentation, streamDocumentationAiSection } from "@/lib/api";
import type { DocumentationAiSection, DocumentationData, DocumentationResponse } from "@/lib/types";

const defaultRepository = "https://github.com/phitrann/LazyDoc";
const codeHealthCategoryConfig = [
  ["security", "Security"],
  ["architecture", "Architecture"],
  ["maintenance", "Maintenance"],
] as const;

type AiDraftState = {
  readme_summary: string;
  recommendations: string[];
  risk_observations: string[];
  sections: DocumentationData["sections"];
  markdown: string;
};

type AiSnapshot = {
  readme_summary: string;
  recommendations: string[];
  risk_observations: string[];
};

const aiSectionLabels: Record<Exclude<DocumentationAiSection, "all">, string> = {
  readme_summary: "README summary",
  recommendations: "recommendations",
  risk_observations: "security and risk observations",
};

export function ReportClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialRepository = searchParams.get("repo") || defaultRepository;

  const [repositoryUrl, setRepositoryUrl] = useState(initialRepository);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<DocumentationResponse | null>(null);
  const [copyStatus, setCopyStatus] = useState<string | null>(null);
  const [activeTocId, setActiveTocId] = useState("repository-overview");
  const [aiStreaming, setAiStreaming] = useState(false);
  const [aiStreamingStatus, setAiStreamingStatus] = useState<string | null>(null);
  const [githubToken, setGithubToken] = useState<string | null>(null);
  const [previousAiSnapshot, setPreviousAiSnapshot] = useState<AiSnapshot | null>(null);
  const [showAiDiff, setShowAiDiff] = useState(false);
  const [activeCodeHealthGroup, setActiveCodeHealthGroup] = useState<(typeof codeHealthCategoryConfig)[number][0]>("security");
  const emptyAiDraft = useMemo(
    () => ({
      readme_summary: "" as string,
      recommendations: [] as string[],
      risk_observations: [] as string[],
      sections: [] as DocumentationData["sections"],
      markdown: "" as string,
    }),
    []
  );
  const [aiDraft, setAiDraft] = useState<AiDraftState | null>(null);
  const activeTocRef = useRef(activeTocId);

  async function loadReport(targetRepository: string, forceRegenerate = false) {
    const trimmed = targetRepository.trim();
    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);
    setCopyStatus(null);
    setAiDraft(null);
    setPreviousAiSnapshot(null);
    setShowAiDiff(false);

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

  function announceCopied(message: string) {
    setCopyStatus(message);
    setTimeout(() => {
      setCopyStatus(null);
    }, 1400);
  }

  async function handleCopyText(content: string, label: string) {
    const trimmed = content.trim();
    if (!trimmed) {
      return;
    }
    await navigator.clipboard.writeText(trimmed);
    announceCopied(`${label} copied to clipboard.`);
  }

  async function handleCopyMarkdown() {
    if (!report?.data.markdown) {
      return;
    }
    await handleCopyText(report.data.markdown, "Markdown");
  }

  async function handleRegenerateAiSection(aiSection: Exclude<DocumentationAiSection, "all">) {
    const trimmed = repositoryUrl.trim();
    if (!trimmed) {
      return;
    }

    setPreviousAiSnapshot(
      report?.data
        ? {
            readme_summary: report.data.readme_summary ?? "",
            recommendations: [...report.data.recommendations],
            risk_observations: [...report.data.risk_observations],
          }
        : null
    );
    setShowAiDiff(false);
    setAiStreaming(true);
    setAiStreamingStatus(`Refreshing ${aiSectionLabels[aiSection]}...`);
    setError(null);
    setCopyStatus(null);
    setAiDraft((previous) => ({
      ...(previous ?? emptyAiDraft),
      ...(aiSection === "readme_summary"
        ? { readme_summary: "" }
        : aiSection === "recommendations"
          ? { recommendations: [] }
          : { risk_observations: [] }),
    }));

    try {
      await streamDocumentationAiSection(trimmed, true, aiSection, {
        onStage: (_stage, message) => {
          setAiStreamingStatus(message);
        },
        onToken: (field, token) => {
          if (aiSection !== "readme_summary" || field !== "readme_summary") {
            return;
          }
          setAiDraft((previous) => ({
            ...(previous ?? emptyAiDraft),
            readme_summary: `${(previous ?? emptyAiDraft).readme_summary}${token}`,
          }));
        },
        onUpdate: (update) => {
          setAiDraft((previous) => ({
            ...(previous ?? emptyAiDraft),
            readme_summary: update.readme_summary ?? (previous ?? emptyAiDraft).readme_summary,
            recommendations: update.recommendations ?? (previous ?? emptyAiDraft).recommendations,
            risk_observations: update.risk_observations ?? (previous ?? emptyAiDraft).risk_observations,
            sections: update.sections ?? (previous ?? emptyAiDraft).sections,
            markdown: update.markdown ?? (previous ?? emptyAiDraft).markdown,
          }));
        },
        onComplete: (update) => {
          setAiDraft((previous) => ({
            ...(previous ?? emptyAiDraft),
            readme_summary: update.readme_summary ?? (previous ?? emptyAiDraft).readme_summary,
            recommendations: update.recommendations ?? (previous ?? emptyAiDraft).recommendations,
            risk_observations: update.risk_observations ?? (previous ?? emptyAiDraft).risk_observations,
            sections: update.sections ?? (previous ?? emptyAiDraft).sections,
            markdown: update.markdown ?? (previous ?? emptyAiDraft).markdown,
          }));
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
      setAiDraft(null);
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

  const overview = report?.data.overview;
  const insights = report?.data.insights;
  const activity = report?.data.activity;
  const structure = report?.data.structure;
  const codeHealth = report?.data.code_health;
  const readmeSummary = useMemo(() => {
    if (aiStreaming) {
      return aiDraft?.readme_summary.trim() || "";
    }
    return aiDraft?.readme_summary.trim() || report?.data.readme_summary?.trim() || "";
  }, [aiDraft, aiStreaming, report]);
  const recommendations = aiStreaming ? aiDraft?.recommendations ?? [] : aiDraft?.recommendations ?? report?.data.recommendations ?? [];
  const riskObservations = aiStreaming ? aiDraft?.risk_observations ?? [] : aiDraft?.risk_observations ?? report?.data.risk_observations ?? [];
  const markdownPreview = useMemo(() => {
    if (aiStreaming) {
      return aiDraft?.markdown ?? "";
    }
    return aiDraft?.markdown ?? report?.data.markdown ?? "";
  }, [aiDraft, aiStreaming, report]);
  const hasDocumentationIntelligence = Boolean(aiStreaming || readmeSummary || recommendations.length || riskObservations.length);
  const hasCodeHealth = Boolean(codeHealth);
  const codeHealthFindings = codeHealth?.findings ?? [];
  const codeHealthGroups = useMemo(() => {
    const groups = {
      security: [] as typeof codeHealthFindings,
      architecture: [] as typeof codeHealthFindings,
      maintenance: [] as typeof codeHealthFindings,
    };
    for (const finding of codeHealthFindings) {
      groups[finding.category].push(finding);
    }
    return groups;
  }, [codeHealthFindings]);
  const aiDiff = useMemo(() => {
    if (!previousAiSnapshot) {
      return null;
    }
    const normalize = (value: string) => value.trim().replace(/\s+/g, " ");
    const previousRecommendations = previousAiSnapshot.recommendations;
    const previousRisks = previousAiSnapshot.risk_observations;
    const currentRecommendations = recommendations;
    const currentRisks = riskObservations;
    return {
      readmeChanged: normalize(previousAiSnapshot.readme_summary) !== normalize(readmeSummary),
      addedRecommendations: currentRecommendations.filter((item) => !previousRecommendations.includes(item)),
      removedRecommendations: previousRecommendations.filter((item) => !currentRecommendations.includes(item)),
      addedRisks: currentRisks.filter((item) => !previousRisks.includes(item)),
      removedRisks: previousRisks.filter((item) => !currentRisks.includes(item)),
    };
  }, [previousAiSnapshot, readmeSummary, recommendations, riskObservations]);

  function jumpToCodeHealthGroup(group: (typeof codeHealthCategoryConfig)[number][0]) {
    setActiveCodeHealthGroup(group);
    const target = document.getElementById(`code-health-group-${group}`);
    if (target instanceof HTMLDetailsElement) {
      target.open = true;
    }
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const tocItems = useMemo(
    () => [
      { id: "repository-overview", label: "Repository Overview" },
      { id: "project-insights", label: "Project Insights" },
      { id: "activity-health", label: "Activity & Health" },
      { id: "structure-summary", label: "Structure Summary" },
      ...(hasCodeHealth ? [{ id: "code-health", label: "Code Health" }] : []),
      ...(hasDocumentationIntelligence ? [{ id: "documentation-intelligence", label: "Documentation Intelligence" }] : []),
      { id: "generated-markdown", label: "Generated Markdown" },
    ],
    [hasCodeHealth, hasDocumentationIntelligence]
  );

  useEffect(() => {
    activeTocRef.current = activeTocId;
  }, [activeTocId]);

  useEffect(() => {
    const sections = tocItems
      .map((item) => document.getElementById(item.id))
      .filter((element): element is HTMLElement => Boolean(element));

    if (!sections.length) {
      return;
    }

    if (!sections.some((section) => section.id === activeTocRef.current)) {
      activeTocRef.current = sections[0].id;
      setActiveTocId(sections[0].id);
    }

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
          activeTocRef.current = mostVisible[0];
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
  }, [tocItems]);

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
          {copyStatus ? <StatusBanner kind="warning" message={copyStatus} /> : null}
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

              <div className="report-highlights" role="list" aria-label="Key repository highlights">
                <article className="report-highlight-card" role="listitem">
                  <span className="report-highlight-label">Stars</span>
                  <strong>{overview.stars.toLocaleString()}</strong>
                </article>
                <article className="report-highlight-card" role="listitem">
                  <span className="report-highlight-label">Commits (30d)</span>
                  <strong>{activity.recent_commits_last_30_days.toLocaleString()}</strong>
                </article>
                <article className="report-highlight-card" role="listitem">
                  <span className="report-highlight-label">Active contributors</span>
                  <strong>{activity.active_contributors_last_30_days.toLocaleString()}</strong>
                </article>
                <article className="report-highlight-card" role="listitem">
                  <span className="report-highlight-label">Primary language</span>
                  <strong>{insights.primary_language || "Unknown"}</strong>
                </article>
                <article className="report-highlight-card" role="listitem">
                  <span className="report-highlight-label">Tracked files</span>
                  <strong>{structure.total_files.toLocaleString()}</strong>
                </article>
                {codeHealth ? (
                  <article className="report-highlight-card report-highlight-card-health" role="listitem">
                    <span className="report-highlight-label">Code health grade</span>
                    <strong>{codeHealth.grade}</strong>
                  </article>
                ) : null}
              </div>

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

            {codeHealth ? (
              <SectionCard
                id="code-health"
                title="Code Health"
                description="A quick health signal with grouped findings, evidence snippets, and score drivers."
                badges={[`Grade ${codeHealth.grade}`]}
              >
                <div className="metric-grid">
                  <MetricCard label="Score" value={`${codeHealth.score}/100`} />
                  <MetricCard label="Scanned files" value={String(codeHealth.metrics.scanned_files)} />
                  <MetricCard label="Security findings" value={String(codeHealth.metrics.security_findings)} />
                  <MetricCard label="Architecture findings" value={String(codeHealth.metrics.architecture_findings)} />
                  <MetricCard label="Maintenance findings" value={String(codeHealth.metrics.maintenance_findings)} />
                  <MetricCard label="Circular dependencies" value={String(codeHealth.metrics.circular_dependencies)} />
                  <MetricCard label="Coupling index" value={String(codeHealth.metrics.coupling_index)} />
                </div>
                <div className="code-health-summary">
                  <p className="section-note">{codeHealth.summary}</p>
                  <div className="code-health-breakdown">
                    {codeHealth.breakdown.map((item) => (
                      <article key={item.name} className="code-health-breakdown-card">
                        <span>{item.name}</span>
                        <strong>{item.score}/100</strong>
                        <p>{item.impact < 0 ? `${item.impact} penalty` : "No penalty"}</p>
                        {item.drivers.length ? (
                          <ul className="code-health-driver-list">
                            {item.drivers.map((driver) => (
                              <li key={driver}>{driver}</li>
                            ))}
                          </ul>
                        ) : null}
                      </article>
                    ))}
                  </div>
                </div>
                {codeHealthFindings.length ? (
                  <div className="code-health-findings">
                    <div className="code-health-tabs" role="tablist" aria-label="Code health categories">
                      {codeHealthCategoryConfig.map(([key, title]) => (
                        <button
                          key={key}
                          type="button"
                          className={activeCodeHealthGroup === key ? "code-health-tab active" : "code-health-tab"}
                          onClick={() => jumpToCodeHealthGroup(key)}
                        >
                          {title} ({codeHealthGroups[key].length})
                        </button>
                      ))}
                    </div>
                    {codeHealthCategoryConfig.map(([key, title]) => {
                      const findings = codeHealthGroups[key];
                      return (
                        <details key={key} id={`code-health-group-${key}`} className="code-health-dropdown">
                          <summary className="code-health-dropdown-summary">
                            <span className="code-health-dropdown-title">{title}</span>
                            <span className="code-health-group-count">
                              {findings.length} finding{findings.length === 1 ? "" : "s"}
                            </span>
                          </summary>
                          {findings.length ? (
                            <div className="code-health-finding-list">
                              {findings.map((finding) => (
                                <section key={finding.id} className="code-health-finding-card">
                                  <div className="code-health-finding-topline">
                                    <span className={`code-health-pill ${finding.category}`}>{finding.impact_area}</span>
                                    <span className={`code-health-severity severity-${finding.severity.toLowerCase()}`}>{finding.severity}</span>
                                    <span className="code-health-confidence">Confidence: {finding.confidence}</span>
                                  </div>
                                  <h4>{finding.rule_name}</h4>
                                  <p className="code-health-finding-message">{finding.message}</p>
                                  <p className="code-health-finding-why">{finding.why_it_matters}</p>
                                  <p className="code-health-finding-evidence">
                                    <strong>Citation:</strong> {finding.file_path}
                                    {finding.line > 0 ? `:${finding.line}` : ""} — <code>{finding.evidence}</code>
                                  </p>
                                  <p className="code-health-finding-suggestion">{finding.suggestion}</p>
                                </section>
                              ))}
                            </div>
                          ) : (
                            <p className="section-note">No {title.toLowerCase()} findings were detected.</p>
                          )}
                        </details>
                      );
                    })}
                  </div>
                ) : (
                  <p className="section-note">No code health risks were found in the scanned source files.</p>
                )}
                
                {codeHealth?.llm_insights?.ranked_findings && codeHealth.llm_insights.ranked_findings.length > 0 ? (
                  <div className="llm-insights-section">
                    <h3>AI-Powered Code Health Analysis</h3>
                    {codeHealth.llm_insights.executive_summary ? (
                      <p className="llm-executive-summary">{codeHealth.llm_insights.executive_summary}</p>
                    ) : null}
                    <div className="llm-ranked-findings">
                      {codeHealth.llm_insights.ranked_findings.map((rankedFinding) => (
                        <details key={rankedFinding.id} className="llm-finding-card">
                          <summary className="llm-finding-summary">
                            <span className="llm-priority-badge">{rankedFinding.impact_priority}</span>
                            <span className="llm-finding-id">{rankedFinding.id}</span>
                            {rankedFinding.is_false_positive ? <span className="llm-badge fp">False Positive</span> : null}
                          </summary>
                          <div className="llm-finding-details">
                            <div className="llm-finding-context">
                              <h4>Business Context</h4>
                              <p>{rankedFinding.business_context}</p>
                            </div>
                            {rankedFinding.remediation_steps?.length ? (
                              <div className="llm-finding-remediation">
                                <h4>Remediation Steps</h4>
                                <ol>
                                  {rankedFinding.remediation_steps.map((step, idx) => (
                                    <li key={idx}>{step}</li>
                                  ))}
                                </ol>
                              </div>
                            ) : null}
                            {rankedFinding.automation_opportunity ? (
                              <div className="llm-finding-automation">
                                <h4>Automation Opportunity</h4>
                                <p>{rankedFinding.automation_opportunity}</p>
                              </div>
                            ) : null}
                          </div>
                        </details>
                      ))}
                    </div>
                  </div>
                ) : null}
              </SectionCard>
            ) : null}

            {hasDocumentationIntelligence ? (
              <SectionCard
                id="documentation-intelligence"
                title="Documentation Intelligence"
                description="README summary, recommendations, and risk signals."
                badges={["AI-generated"]}
              >
                {previousAiSnapshot && !aiStreaming ? (
                  <div className="ai-actions">
                    <label className="ai-diff-toggle">
                      <input type="checkbox" checked={showAiDiff} onChange={(event) => setShowAiDiff(event.target.checked)} />
                      Show diff from previous generation
                    </label>
                  </div>
                ) : null}
                {aiStreamingStatus ? <p className="section-note">{aiStreamingStatus}</p> : null}
                <div className="markdown-section markdown-compact">
                  <div className="ai-section-header">
                    <h3>README Summary</h3>
                    <button
                      type="button"
                      className="section-icon-button"
                      onClick={() => void handleRegenerateAiSection("readme_summary")}
                      disabled={loading || aiStreaming}
                      aria-label="Regenerate README summary"
                      title="Regenerate README summary"
                    >
                      ↻
                    </button>
                  </div>
                  {aiStreaming && !readmeSummary ? (
                    <div className="ai-skeleton-block" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                    </div>
                  ) : readmeSummary ? (
                    <MarkdownRenderer content={readmeSummary} />
                  ) : (
                    <p className="section-note">No README summary available.</p>
                  )}
                  {showAiDiff && aiDiff?.readmeChanged ? (
                    <div className="ai-diff-panel">
                      <p>README summary changed from the previous generation.</p>
                      {previousAiSnapshot?.readme_summary ? (
                        <details>
                          <summary>View previous README summary</summary>
                          <MarkdownRenderer content={previousAiSnapshot.readme_summary} className="markdown-preview-rendered" />
                        </details>
                      ) : null}
                    </div>
                  ) : null}
                </div>
                <div className="content-list">
                  <div className="ai-section-header">
                    <h3>Recommendations</h3>
                    <button
                      type="button"
                      className="section-icon-button"
                      onClick={() => void handleRegenerateAiSection("recommendations")}
                      disabled={loading || aiStreaming}
                      aria-label="Regenerate recommendations"
                      title="Regenerate recommendations"
                    >
                      ↻
                    </button>
                  </div>
                  {aiStreaming && !recommendations.length ? (
                    <div className="ai-skeleton-list" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                    </div>
                  ) : recommendations.length ? (
                    <ul>
                      {recommendations.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="section-note">No recommendations generated.</p>
                  )}
                  {showAiDiff && aiDiff && (aiDiff.addedRecommendations.length || aiDiff.removedRecommendations.length) ? (
                    <div className="ai-diff-panel">
                      {aiDiff.addedRecommendations.length ? (
                        <p>
                          <strong>Added:</strong> {aiDiff.addedRecommendations.join(" | ")}
                        </p>
                      ) : null}
                      {aiDiff.removedRecommendations.length ? (
                        <p>
                          <strong>Removed:</strong> {aiDiff.removedRecommendations.join(" | ")}
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                </div>
                <div className="content-list">
                  <div className="ai-section-header">
                    <h3>Security & Risk Observations</h3>
                    <button
                      type="button"
                      className="section-icon-button"
                      onClick={() => void handleRegenerateAiSection("risk_observations")}
                      disabled={loading || aiStreaming}
                      aria-label="Regenerate security and risk observations"
                      title="Regenerate security and risk observations"
                    >
                      ↻
                    </button>
                  </div>
                  {aiStreaming && !riskObservations.length ? (
                    <div className="ai-skeleton-list" aria-hidden="true">
                      <span />
                      <span />
                    </div>
                  ) : riskObservations.length ? (
                    <ul>
                      {riskObservations.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="section-note">No risk observations generated.</p>
                  )}
                  {showAiDiff && aiDiff && (aiDiff.addedRisks.length || aiDiff.removedRisks.length) ? (
                    <div className="ai-diff-panel">
                      {aiDiff.addedRisks.length ? (
                        <p>
                          <strong>Added:</strong> {aiDiff.addedRisks.join(" | ")}
                        </p>
                      ) : null}
                      {aiDiff.removedRisks.length ? (
                        <p>
                          <strong>Removed:</strong> {aiDiff.removedRisks.join(" | ")}
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </SectionCard>
            ) : null}

            <SectionCard
              id="generated-markdown"
              title="Generated Markdown"
              description="Copy the rendered report or reuse it in documentation workflows."
              action={
                <button type="button" className="section-action-button" onClick={handleCopyMarkdown} disabled={!report?.data.markdown}>
                  Copy Markdown
                </button>
              }
            >
              {markdownPreview ? (
                <MarkdownRenderer content={markdownPreview} className="markdown-preview-rendered" />
              ) : (
                <p className="section-note">No markdown generated yet.</p>
              )}
            </SectionCard>

          </section>
          </div>
        ) : null}
      </main>
    </div>
  );
}
