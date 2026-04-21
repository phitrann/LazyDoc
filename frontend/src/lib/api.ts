import type { DocumentationAiSection, DocumentationResponse, ResearchResponse, TrendingRepository } from "@/lib/types";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "";
type StreamPayload = {
  stage?: string;
  message?: string;
  field?: string;
  token?: string;
  data?: DocumentationAiStreamUpdate;
  cached?: boolean;
  error_code?: string;
  retry_after_seconds?: number;
};

async function readErrorPayload(response: Response): Promise<{ message?: string; error_code?: string; retry_after_seconds?: number }> {
  const text = await response.text();
  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text) as { message?: string; error_code?: string; retry_after_seconds?: number };
  } catch {
    return { message: text };
  }
}

function getHeaders(githubToken?: string): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (githubToken) {
    headers["X-GitHub-Token"] = githubToken;
  }
  return headers;
}

export async function analyzeRepository(repositoryUrl: string, githubToken?: string): Promise<ResearchResponse> {
  const response = await fetch(`${apiBaseUrl}/api/research`, {
    method: "POST",
    headers: getHeaders(githubToken),
    body: JSON.stringify({ repository_url: repositoryUrl }),
  });

  if (!response.ok) {
    const payload = await readErrorPayload(response);
    const error = new Error(payload.message || "Request failed.") as Error & { code?: string; retryAfterSeconds?: number };
    error.code = payload.error_code;
    error.retryAfterSeconds = payload.retry_after_seconds;
    throw error;
  }

  const payload = await response.json();

  return payload as ResearchResponse;
}

export async function generateDocumentation(repositoryUrl: string, forceRegenerate = false, githubToken?: string): Promise<DocumentationResponse> {
  const response = await fetch(`${apiBaseUrl}/api/documentation`, {
    method: "POST",
    headers: getHeaders(githubToken),
    body: JSON.stringify({ repository_url: repositoryUrl, force_regenerate: forceRegenerate }),
  });

  if (!response.ok) {
    const payload = await readErrorPayload(response);
    const error = new Error(payload.message || "Request failed.") as Error & { code?: string; retryAfterSeconds?: number };
    error.code = payload.error_code;
    error.retryAfterSeconds = payload.retry_after_seconds;
    throw error;
  }

  const payload = await response.json();

  return payload as DocumentationResponse;
}

export async function fetchTrendingRepositories(): Promise<TrendingRepository[]> {
  const response = await fetch(`${apiBaseUrl}/api/trending`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await readErrorPayload(response);
    throw new Error(payload.message || "Failed to load trending repositories.");
  }

  const payload = (await response.json()) as { data?: TrendingRepository[] };
  return payload.data || [];
}

export type DocumentationAiStreamUpdate = {
  readme_summary?: string | null;
  recommendations?: string[];
  risk_observations?: string[];
  sections?: DocumentationResponse["data"]["sections"];
  markdown?: string;
  warnings?: string[];
};

type DocumentationAiStreamHandlers = {
  onStage?: (stage: string, message: string) => void;
  onToken?: (field: string, token: string) => void;
  onUpdate?: (update: DocumentationAiStreamUpdate) => void;
  onComplete?: (update: DocumentationAiStreamUpdate, cached: boolean) => void;
};

function parseSseChunk(chunk: string): Array<{ event: string; data: string }> {
  return chunk
    .split("\n\n")
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) => {
      const lines = block.split("\n");
      const eventLine = lines.find((line) => line.startsWith("event:"));
      const dataLines = lines.filter((line) => line.startsWith("data:"));
      return {
        event: eventLine ? eventLine.replace("event:", "").trim() : "message",
        data: dataLines.map((line) => line.replace("data:", "").trim()).join("\n"),
      };
    });
}

export async function streamDocumentationAiSection(
  repositoryUrl: string,
  forceRegenerate = false,
  aiSection: DocumentationAiSection = "all",
  handlers: DocumentationAiStreamHandlers = {},
  githubToken?: string
): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/documentation/stream`, {
    method: "POST",
    headers: getHeaders(githubToken),
    body: JSON.stringify({ repository_url: repositoryUrl, force_regenerate: forceRegenerate, ai_section: aiSection }),
  });

  if (!response.ok) {
    const payload = await readErrorPayload(response);
    const error = new Error(payload.message || "Request failed.") as Error & { code?: string; retryAfterSeconds?: number };
    error.code = payload.error_code;
    error.retryAfterSeconds = payload.retry_after_seconds;
    throw error;
  }

  if (!response.body) {
    throw new Error("Streaming is not available in this environment.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";

    for (const rawChunk of chunks) {
      for (const event of parseSseChunk(rawChunk)) {
        if (!event.data) {
          continue;
        }
        let payload: StreamPayload;
        try {
          payload = JSON.parse(event.data) as StreamPayload;
        } catch {
          throw new Error(event.data || "Streaming request failed.");
        }

        if (event.event === "stage" && payload.stage && payload.message) {
          handlers.onStage?.(payload.stage, payload.message);
          continue;
        }
        if (event.event === "ai_update" && payload.data) {
          handlers.onUpdate?.(payload.data);
          continue;
        }
        if (event.event === "token" && payload.field && typeof payload.token === "string") {
          handlers.onToken?.(payload.field, payload.token);
          continue;
        }
        if (event.event === "complete" && payload.data) {
          handlers.onComplete?.(payload.data, Boolean(payload.cached));
          continue;
        }
        if (event.event === "error") {
          const error = new Error(payload.message || "Streaming request failed.") as Error & { code?: string; retryAfterSeconds?: number };
          error.code = payload.error_code;
          error.retryAfterSeconds = payload.retry_after_seconds;
          throw error;
        }
      }
    }

    if (done) {
      break;
    }
  }
}
