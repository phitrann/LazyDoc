"use client";
import { useEffect, useState } from "react";

interface GitHubPatInputProps {
  onTokenChange: (token: string | null) => void;
  disabled?: boolean;
}

const STORAGE_KEY = "github_pat_token";

const EyeIcon = ({ open }: { open: boolean }) =>
  open ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19M1 1l22 22" />
    </svg>
  );

const XIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <path d="M18 6L6 18M6 6l12 12" />
  </svg>
);

const KeyIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="7.5" cy="15.5" r="5.5" />
    <path d="M21 2l-9.6 9.6M15.5 7.5l3 3L21 8l-3-3" />
  </svg>
);

export function GitHubPatInput({ onTokenChange, disabled = false }: GitHubPatInputProps) {
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const hasToken = token.trim().length > 0;

  useEffect(() => {
    try {
      const cached = localStorage.getItem(STORAGE_KEY);
      if (cached) {
        setToken(cached);
        onTokenChange(cached);
      }
    } catch {}
    setIsInitialized(true);
  }, [onTokenChange]);

  function handleTokenChange(value: string) {
    setToken(value);
    const trimmed = value.trim() || null;
    onTokenChange(trimmed);
    if (trimmed) {
      try { localStorage.setItem(STORAGE_KEY, trimmed); } catch {}
    }
  }

  function handleClear() {
    setToken("");
    onTokenChange(null);
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }

  if (!isInitialized) return null;

  return (
    <div className="pat-card">
      <div className="pat-label">
        <KeyIcon />
        GitHub personal access token
      </div>

      <div className="pat-input-wrap">
        <div className="pat-input-row">
          <input
            id="github-pat-token"
            type={showToken ? "text" : "password"}
            value={token}
            onChange={(e) => handleTokenChange(e.target.value)}
            placeholder="ghp_••••••••••••••••••••"
            disabled={disabled}
            className="pat-input"
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <div className="pat-btn-group">
          <button
            type="button"
            onClick={() => setShowToken((v) => !v)}
            className="pat-icon-button"
            disabled={disabled || !hasToken}
            title={showToken ? "Hide token" : "Reveal token"}
          >
            <EyeIcon open={showToken} />
          </button>

          {hasToken && (
            <>
              <div className="pat-separator" />
              <button
                type="button"
                onClick={handleClear}
                disabled={disabled}
                className="pat-icon-button danger"
                title="Clear token"
              >
                <XIcon />
              </button>
            </>
          )}
        </div>
      </div>

      <div className="pat-footer">
        <p className="pat-note">
          Cached in local storage — never sent to any server.
        </p>
        <a
          href="https://github.com/settings/tokens?type=pat"
          target="_blank"
          rel="noopener noreferrer"
          className="pat-link"
        >
          Generate token ↗
        </a>
      </div>
    </div>
  );
}