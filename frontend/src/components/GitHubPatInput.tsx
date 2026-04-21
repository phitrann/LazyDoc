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
  const hasToken = token.trim().length > 0;

  function handleTokenChange(value: string) {
    setToken(value);
    onTokenChange(value.trim() || null);
  }

  function handleClear() {
    setToken("");
    onTokenChange(null);
  }

  return (
    <div id="github-pat-input" className="pat-card">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="pat-toggle"
        aria-expanded={isExpanded}
      >
        <span className="pat-toggle-label">
          <span className={hasToken ? "pat-dot active" : "pat-dot"} />
          GitHub Personal Access Token (PAT)
        </span>
        <span className="pat-toggle-icon">{isExpanded ? "-" : "+"}</span>
      </button>

      {isExpanded && (
        <div className="pat-panel">
          <p className="pat-copy">
            Provide a GitHub PAT to increase your rate limit from 60 req/hr (unauthenticated) to 5,000 req/hr (authenticated).
          </p>

          <label className="field-label pat-field-label" htmlFor="github-pat-token">
            GitHub PAT
          </label>

          <div className="pat-input-row">
            <input
              id="github-pat-token"
              type={showToken ? "text" : "password"}
              value={token}
              onChange={(e) => handleTokenChange(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              disabled={disabled}
              className="pat-input"
            />
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="pat-secondary-button"
              disabled={disabled || !hasToken}
            >
              {showToken ? "Hide" : "Show"}
            </button>
            {hasToken ? (
              <button type="button" onClick={handleClear} disabled={disabled} className="pat-secondary-button danger">
                Clear
              </button>
            ) : null}
          </div>

          <div className="pat-actions">
            <a href="https://github.com/settings/tokens?type=pat" target="_blank" rel="noopener noreferrer" className="pat-link">
              Generate token on GitHub
            </a>
          </div>

          <div className="pat-note">
            Token is used only for this browser session and is not stored on disk.
          </div>
        </div>
      )}
    </div>
  );
}
