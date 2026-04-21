"use client";

import { useState } from "react";

interface GitHubPatInputProps {
  onTokenChange: (token: string | null) => void;
  disabled?: boolean;
}

export function GitHubPatInput({ onTokenChange, disabled = false }: GitHubPatInputProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);

  function handleTokenChange(value: string) {
    setToken(value);
    onTokenChange(value || null);
  }

  function handleClear() {
    setToken("");
    onTokenChange(null);
  }

  return (
    <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-left font-medium text-gray-700 hover:text-gray-900"
      >
        <span className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-green-500" />
          GitHub Personal Access Token (PAT)
        </span>
        <span className="text-gray-400">
          {isExpanded ? "▼" : "▶"}
        </span>
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          <p className="text-sm text-gray-600">
            Provide a GitHub PAT to increase your rate limit from 60 req/hr (unauthenticated) to 5,000 req/hr (authenticated).
          </p>

          <div className="space-y-2">
            <div className="relative">
              <input
                type={showToken ? "text" : "password"}
                value={token}
                onChange={(e) => handleTokenChange(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                disabled={disabled}
                className="w-full rounded border border-gray-300 px-3 py-2 font-mono text-sm placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-3 top-2 text-gray-500 hover:text-gray-700 disabled:text-gray-300"
                disabled={disabled || !token}
              >
                {showToken ? "Hide" : "Show"}
              </button>
            </div>

            <div className="flex gap-2">
              {token && (
                <button
                  type="button"
                  onClick={handleClear}
                  disabled={disabled}
                  className="rounded bg-red-50 px-3 py-1 text-sm font-medium text-red-600 hover:bg-red-100 disabled:bg-gray-100 disabled:text-gray-500"
                >
                  Clear
                </button>
              )}
              <a
                href="https://github.com/settings/tokens?type=pat"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded bg-blue-50 px-3 py-1 text-sm font-medium text-blue-600 hover:bg-blue-100"
              >
                Generate Token →
              </a>
            </div>
          </div>

          <div className="rounded bg-gray-50 p-3 text-xs text-gray-600">
            <p className="font-semibold text-gray-700">Token is not stored:</p>
            <p className="mt-1">Your PAT is sent directly to analyze repositories and is not saved locally or on our servers.</p>
          </div>
        </div>
      )}
    </div>
  );
}
