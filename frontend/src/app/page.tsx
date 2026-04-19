"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type FeaturedRepo = {
  handle: string;
  description: string;
  stars: string;
  url: string;
};

const featuredRepos: FeaturedRepo[] = [
  {
    handle: "phitrann / LazyDoc",
    description: "GitHub Repository Research Tool with FastAPI backend and Next.js frontend.",
    stars: "local",
    url: "https://github.com/phitrann/LazyDoc",
  },
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
          <div className="repo-grid">
            <button type="button" className="repo-card add-repo" onClick={() => setRepositoryUrl("https://github.com/owner/repo")}>
              <span className="repo-add-icon">+</span>
              <span>Add repo</span>
            </button>

            {featuredRepos.map((repo) => (
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
