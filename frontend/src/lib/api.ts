import type { ResearchResponse } from "@/lib/types";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "";

export async function analyzeRepository(repositoryUrl: string): Promise<ResearchResponse> {
  const response = await fetch(`${apiBaseUrl}/api/research`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ repository_url: repositoryUrl }),
  });

  const payload = await response.json();

  if (!response.ok) {
    const error = new Error(payload.message || "Request failed.") as Error & { code?: string; retryAfterSeconds?: number };
    error.code = payload.error_code;
    error.retryAfterSeconds = payload.retry_after_seconds;
    throw error;
  }

  return payload as ResearchResponse;
}
