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

  return (
    <div
      className={`rounded-lg border p-3 ${
        isAtLimit
          ? "border-red-300 bg-red-50"
          : isWarning
            ? "border-orange-300 bg-orange-50"
            : "border-blue-300 bg-blue-50"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div
            className={`text-sm font-semibold ${
              isAtLimit ? "text-red-900" : isWarning ? "text-orange-900" : "text-blue-900"
            }`}
          >
            {isAtLimit
              ? "Rate Limit Exceeded"
              : isWarning
                ? "Rate Limit Warning"
                : "API Rate Limit"}
          </div>
          <div className="mt-1 text-xs text-gray-600">
            {isAtLimit ? (
              <span>
                Your limit will reset in {timeRemaining || "loading..."}.{" "}
                {!hasGithubToken && "Add a GitHub PAT above to get 5,000 requests/hr."}
              </span>
            ) : (
              <span>
                {rateLimit.remaining} of {rateLimit.limit} requests remaining
                {timeRemaining && ` • Resets in ${timeRemaining}`}
              </span>
            )}
          </div>

          {/* Progress bar */}
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gray-300">
            <div
              className={`h-full transition-all ${
                isAtLimit
                  ? "bg-red-500"
                  : isWarning
                    ? "bg-orange-500"
                    : "bg-blue-500"
              }`}
              style={{ width: `${Math.min(percentageUsed, 100)}%` }}
            />
          </div>
        </div>

        {!hasGithubToken && !isAtLimit && (
          <a
            href="#github-pat-input"
            className="flex-shrink-0 whitespace-nowrap rounded bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-200"
          >
            Add PAT
          </a>
        )}
      </div>
    </div>
  );
}
