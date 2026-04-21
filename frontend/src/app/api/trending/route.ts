import { NextResponse } from "next/server";

import type { TrendingRepository } from "@/lib/types";

const lazyDocRepository: TrendingRepository = {
  handle: "phitrann / LazyDoc",
  description: "GitHub Repository Research Tool with FastAPI backend and Next.js frontend.",
  stars: "local",
  url: "https://github.com/phitrann/LazyDoc",
};

const fallbackTrendingRepositories: TrendingRepository[] = [
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

function formatStars(stars: number): string {
  if (stars >= 1_000_000) {
    return `${(stars / 1_000_000).toFixed(1)}m`;
  }
  if (stars >= 1_000) {
    return `${(stars / 1_000).toFixed(1)}k`;
  }
  return `${stars}`;
}

function normalizeTrending(items: Array<{ full_name: string; description: string | null; stargazers_count: number; html_url: string }>): TrendingRepository[] {
  return items.map((item) => ({
    handle: item.full_name.replace("/", " / "),
    description: item.description || "No description provided.",
    stars: formatStars(item.stargazers_count),
    url: item.html_url,
  }));
}

export async function GET() {
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  const since = sevenDaysAgo.toISOString().slice(0, 10);

  const searchQuery = `https://api.github.com/search/repositories?q=created:>${since}&sort=stars&order=desc&per_page=12`;
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "User-Agent": "LazyDoc-Trending-Route",
  };

  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(searchQuery, {
      headers,
      next: { revalidate: 1800 },
    });

    if (!response.ok) {
      throw new Error(`GitHub trending fetch failed with status ${response.status}`);
    }

    const payload = (await response.json()) as {
      items?: Array<{ full_name: string; description: string | null; stargazers_count: number; html_url: string }>;
    };

    const normalized = normalizeTrending(payload.items || []);
    const filtered = normalized.filter((repo) => repo.url.toLowerCase() !== lazyDocRepository.url.toLowerCase());

    return NextResponse.json({
      status: "success",
      data: [lazyDocRepository, ...filtered],
    });
  } catch {
    return NextResponse.json({
      status: "partial",
      data: [lazyDocRepository, ...fallbackTrendingRepositories],
      warnings: ["Trending repositories fallback is in use."],
    });
  }
}
