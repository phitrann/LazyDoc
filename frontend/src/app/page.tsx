"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { fetchTrendingRepositories } from "@/lib/api";
import type { TrendingRepository } from "@/lib/types";

const lazyDocRepo: TrendingRepository = {
  handle: "phitrann / LazyDoc",
  description: "GitHub Repository Research Tool with FastAPI backend and Next.js frontend.",
  stars: "local",
  url: "https://github.com/phitrann/LazyDoc",
};

const fallbackTrendingRepos: TrendingRepository[] = [
  {
    handle: "microsoft / vscode",
    description: "Visual Studio Code",
    stars: "159.4k",
    url: "https://github.com/microsoft/vscode",
  },
  {
    handle: "huggingface / transformers",
    description: "State-of-the-art machine learning for PyTorch, TensorFlow, and JAX.",
    stars: "152.4k",
    url: "https://github.com/huggingface/transformers",
  },
  {
    handle: "microsoft / playwright",
    description: "Framework for web testing and automation across Chromium, Firefox, and WebKit.",
    stars: "66.5k",
    url: "https://github.com/microsoft/playwright",
  },
  {
    handle: "karpathy / nanoGPT",
    description: "A simple and fast repository for training and finetuning medium-sized GPTs.",
    stars: "50.1k",
    url: "https://github.com/karpathy/nanoGPT",
  },
  {
    handle: "langchain-ai / langchain",
    description: "Building applications with LLMs through composability.",
    stars: "33.6k",
    url: "https://github.com/langchain-ai/langchain",
  },
  {
    handle: "openai / openai-python",
    description: "Official Python library for the OpenAI API.",
    stars: "32.5k",
    url: "https://github.com/openai/openai-python",
  },
];

export default function HomePage() {
  const router = useRouter();
  const [repositoryUrl, setRepositoryUrl] = useState("https://github.com/phitrann/LazyDoc");
  const [trendingRepos, setTrendingRepos] = useState<TrendingRepository[]>(fallbackTrendingRepos);
  const [isTrendingLoading, setIsTrendingLoading] = useState(true);
  const [trendingError, setTrendingError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadTrending() {
      try {
        setIsTrendingLoading(true);
        setTrendingError(null);
        const repositories = await fetchTrendingRepositories();
        if (!isMounted || !repositories.length) {
          return;
        }

        const withoutLazyDoc = repositories.filter((repo) => repo.url.toLowerCase() !== lazyDocRepo.url.toLowerCase());
        setTrendingRepos(withoutLazyDoc.length ? withoutLazyDoc : fallbackTrendingRepos);
      } catch {
        if (isMounted) {
          setTrendingError("Unable to load live trending data. Showing fallback list.");
          setTrendingRepos(fallbackTrendingRepos);
        }
      } finally {
        if (isMounted) {
          setIsTrendingLoading(false);
        }
      }
    }

    void loadTrending();

    return () => {
      isMounted = false;
    };
  }, []);

  const trendingCountLabel = useMemo(() => {
    if (isTrendingLoading) {
      return "Refreshing trending repositories...";
    }
    return `Showing ${trendingRepos.length} trending repositories from GitHub search.`;
  }, [isTrendingLoading, trendingRepos.length]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = repositoryUrl.trim();
    if (!trimmed) {
      return;
    }
    router.push(`/report?repo=${encodeURIComponent(trimmed)}`);
  }

  return (
    <div className="landing-shell">
      <header className="top-nav">
        <div className="top-nav-inner">
          <div className="brand">LazyDoc</div>
          <div className="nav-meta">
            <p>Repository research for technical due diligence</p>
            <button type="submit" form="landing-search-form">
              Research
            </button>
          </div>
        </div>
      </header>

      <main className="landing-content">
        <section className="hero-search">
          <h1>Which GitHub repository should LazyDoc research?</h1>
          <form id="landing-search-form" className="hero-search-form" onSubmit={handleSubmit}>
            <input
              type="url"
              value={repositoryUrl}
              onChange={(event) => setRepositoryUrl(event.target.value)}
              placeholder="Paste a public repository URL"
            />
          </form>
        </section>

        <section className="repo-grid-section">
          <div className="repo-section-header">
            <div>
              <p className="eyebrow">Featured</p>
              <h2>LazyDoc</h2>
            </div>
            <p>Use the repository that powers this submission, then browse current trending examples.</p>
          </div>

          <button type="button" className="repo-card repo-card-featured" onClick={() => router.push(`/report?repo=${encodeURIComponent(lazyDocRepo.url)}`)}>
            <div>
              <h3>{lazyDocRepo.handle}</h3>
              <p>{lazyDocRepo.description}</p>
            </div>
            <div className="repo-card-footer">
              <span>{lazyDocRepo.stars}</span>
              <span aria-hidden="true">→</span>
            </div>
          </button>

          <div className="repo-section-header repo-section-header-trending">
            <div>
              <p className="eyebrow">Trending repositories</p>
              <h2>Popular public projects</h2>
            </div>
            <p>{trendingCountLabel}</p>
          </div>

          {trendingError ? <p className="repo-grid-warning">{trendingError}</p> : null}

          <div className="repo-grid">
            {trendingRepos.map((repo) => (
              <button
                key={repo.handle}
                type="button"
                className="repo-card"
                onClick={() => router.push(`/report?repo=${encodeURIComponent(repo.url)}`)}
              >
                <div>
                  <h3>{repo.handle}</h3>
                  <p>{repo.description}</p>
                </div>
                <div className="repo-card-footer">
                  <span>{repo.stars}</span>
                  <span aria-hidden="true">→</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        <footer className="landing-footer">
          <h2>What is LazyDoc?</h2>
          <p>
            LazyDoc turns public repositories into structured reports with overview metrics, project insights,
            activity health signals, and AI-assisted recommendations.
          </p>
        </footer>
      </main>
    </div>
  );
}
