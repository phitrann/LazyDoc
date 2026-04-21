import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8992";

export async function POST(request: NextRequest) {
  const requestBody = await request.text();
  const githubToken = request.headers.get("x-github-token");

  try {
    const upstream = await fetch(`${backendBaseUrl}/api/documentation/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(githubToken ? { "X-GitHub-Token": githubToken } : {}),
      },
      body: requestBody,
      cache: "no-store",
    });

    if (!upstream.body) {
      const text = await upstream.text();
      return new NextResponse(text, {
        status: upstream.status,
        headers: {
          "Content-Type": upstream.headers.get("content-type") || "application/json",
        },
      });
    }

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch {
    return NextResponse.json(
      {
        status: "error",
        error_code: "UPSTREAM_UNAVAILABLE",
        message: "Backend service is unavailable. Ensure FastAPI is running.",
      },
      { status: 502 }
    );
  }
}
