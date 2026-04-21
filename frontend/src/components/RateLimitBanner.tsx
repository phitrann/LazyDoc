"use client";

import { useEffect, useState } from "react";
import type { RateLimit } from "@/lib/types";

interface RateLimitBannerProps {
  rateLimit?: RateLimit;
  hasGithubToken?: boolean;
}

export function RateLimitBanner({ rateLimit, hasGithubToken = false }: RateLimitBannerProps) {
  const [timeRemaining, setTimeRemaining] = useState<string | null>(null);

  useEffect(() => {
    if (!rateLimit) {
      setTimeRemaining(null);
      return;
    }

    const updateCountdown = () => {
      const now = Date.now() / 1000;
      const secondsLeft = rateLimit.reset_unix_timestamp - now;

      if (secondsLeft <= 0) {
        setTimeRemaining(null);
        return;
      }

      const minutes = Math.floor(secondsLeft / 60);
      const seconds = Math.floor(secondsLeft % 60);

      if (minutes > 0) {
        setTimeRemaining(`${minutes}m ${seconds}s`);
      } else {
        setTimeRemaining(`${seconds}s`);
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [rateLimit]);

  if (!rateLimit) {
    return null;
  }

  const percentageUsed = ((rateLimit.limit - rateLimit.remaining) / rateLimit.limit) * 100;
  const isWarning = percentageUsed > 75;
  const isAtLimit = rateLimit.remaining === 0;
  const isUnauthenticatedLimit = !hasGithubToken && rateLimit.limit <= 60;
  const toneClass = isAtLimit ? "error" : isWarning ? "warning" : "info";
  const progressToneClass = isAtLimit ? "error" : isWarning ? "warning" : "info";

  return (
    <div className={`rate-limit-banner ${toneClass}`}>
      <div className="rate-limit-header-row">
        <p className="rate-limit-title">
          {isAtLimit ? "GitHub Rate Limit Exceeded" : isWarning ? "GitHub Rate Limit Warning" : "GitHub API Rate Limit"}
        </p>
        {!hasGithubToken && !isAtLimit ? (
          <a href="#github-pat-input" className="rate-limit-cta">
            Use GitHub PAT
          </a>
        ) : null}
      </div>

      <p className="rate-limit-meta">
        {isAtLimit ? (
          <>
            Your limit will reset in {timeRemaining || "loading..."}.
            {!hasGithubToken ? " Add a GitHub PAT above to get 5,000 requests/hr." : ""}
          </>
        ) : (
          <>
            {rateLimit.remaining} / {rateLimit.limit} requests remaining
            {timeRemaining ? ` • Resets in ${timeRemaining}` : ""}
            {isUnauthenticatedLimit ? " • Unauthenticated mode" : ""}
          </>
        )}
      </p>

      <div className="rate-limit-progress">
        <div
          className={`rate-limit-progress-fill ${progressToneClass}`}
          style={{ width: `${Math.min(percentageUsed, 100)}%` }}
        />
      </div>
    </div>
  );
}
