// components/export/ExportBar.tsx
"use client";

import { useState } from "react";
import { downloadReport } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ExportBarProps {
  jobId:    string;
  filename: string;
}

type ExportFormat = "json" | "markdown" | "sarif" | "pdf";
type ButtonState  = "idle" | "loading" | "done" | "error";

// ── Export Button Config ──────────────────────────────────────────────────────

const EXPORT_BUTTONS: {
  format:  ExportFormat;
  label:   string;
  icon:    string;
  tooltip: string;
}[] = [
  {
    format:  "json",
    label:   "JSON",
    icon:    "{ }",
    tooltip: "Full structured report with all findings and metadata",
  },
  {
    format:  "markdown",
    label:   "Markdown",
    icon:    "MD",
    tooltip: "Human-readable report for documentation or GitHub PRs",
  },
  {
    format:  "sarif",
    label:   "SARIF",
    icon:    "◈",
    tooltip: "Static Analysis Results Interchange Format for IDE integration",
  },
  {
    format:  "pdf",
    label:   "PDF",
    icon:    "⬇",
    tooltip: "Formatted PDF report suitable for sharing or printing",
  },
];

// ── Single Export Button ──────────────────────────────────────────────────────

function ExportButton({
  format,
  label,
  icon,
  tooltip,
  jobId,
}: {
  format:  ExportFormat;
  label:   string;
  icon:    string;
  tooltip: string;
  jobId:   string;
}) {
  const [state,       setState]       = useState<ButtonState>("idle");
  const [showTooltip, setShowTooltip] = useState(false);

  const handleClick = async () => {
    if (state === "loading") return;
    setState("loading");
    try {
      if (format === "pdf") {
        // ✅ PDF is a direct download — open in new tab to trigger browser download
        const url = `/api/backend/report/${jobId}/pdf`;
        const anchor = document.createElement("a");
        anchor.href     = url;
        anchor.download = `report-${jobId}.pdf`;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
      } else {
        downloadReport(jobId, format as "json" | "markdown" | "sarif");
      }
      setState("done");
      setTimeout(() => setState("idle"), 2000);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 2000);
    }
  };

  const isLoading = state === "loading";
  const isDone    = state === "done";
  const isError   = state === "error";

  const borderColor = isDone
    ? "rgba(0, 255, 135, 0.40)"
    : isError
    ? "var(--sev-critical)"
    : "var(--border-default)";

  const textColor = isDone
    ? "#00FF87"
    : isError
    ? "var(--sev-critical)"
    : "var(--text-secondary)";

  return (
    <div style={{ position: "relative" }}>
      {/* Tooltip */}
      {showTooltip && (
        <div style={{
          position:      "absolute",
          bottom:        "calc(100% + 8px)",
          left:          "50%",
          transform:     "translateX(-50%)",
          background:    "var(--bg-elevated)",
          border:        "1px solid var(--border-default)",
          borderRadius:  "6px",
          padding:       "6px 10px",
          fontFamily:    "var(--font-mono)",
          fontSize:      "10px",
          color:         "var(--text-secondary)",
          whiteSpace:    "nowrap",
          zIndex:        50,
          pointerEvents: "none",
          boxShadow:     "0 4px 16px rgba(0,0,0,0.4)",
        }}>
          {tooltip}
          <div style={{
            position:     "absolute",
            bottom:       "-5px",
            left:         "50%",
            transform:    "translateX(-50%) rotate(45deg)",
            width:        "8px",
            height:       "8px",
            background:   "var(--bg-elevated)",
            borderRight:  "1px solid var(--border-default)",
            borderBottom: "1px solid var(--border-default)",
          }} />
        </div>
      )}

      <button
        onClick={handleClick}
        disabled={isLoading}
        style={{
          display:       "flex",
          alignItems:    "center",
          gap:           "8px",
          padding:       "9px 16px",
          background:    isDone ? "rgba(0,255,135,0.08)" : "var(--bg-elevated)",
          border:        `1px solid ${borderColor}`,
          borderRadius:  "6px",
          color:         textColor,
          fontFamily:    "var(--font-mono)",
          fontSize:      "11px",
          fontWeight:    500,
          cursor:        isLoading ? "wait" : "pointer",
          transition:    "all 0.2s ease",
          letterSpacing: "0.04em",
          whiteSpace:    "nowrap",
        }}
        onMouseEnter={(e) => {
          setShowTooltip(true);
          if (!isDone && !isError) {
            (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent-border)";
            (e.currentTarget as HTMLButtonElement).style.color       = "var(--accent)";
            (e.currentTarget as HTMLButtonElement).style.background  = "var(--accent-dim)";
          }
        }}
        onMouseLeave={(e) => {
          setShowTooltip(false);
          if (!isDone && !isError) {
            (e.currentTarget as HTMLButtonElement).style.borderColor = borderColor;
            (e.currentTarget as HTMLButtonElement).style.color       = textColor;
            (e.currentTarget as HTMLButtonElement).style.background  = isDone
              ? "rgba(0,255,135,0.08)"
              : "var(--bg-elevated)";
          }
        }}
      >
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize:   "10px",
          fontWeight: 700,
          color:      "inherit",
          opacity:    0.7,
        }}>
          {isLoading ? "…" : isDone ? "✓" : isError ? "✕" : icon}
        </span>
        <span>
          {isLoading ? "Downloading" : isDone ? "Downloaded!" : isError ? "Failed" : `Export ${label}`}
        </span>
      </button>
    </div>
  );
}

// ── GitHub PR Button ──────────────────────────────────────────────────────────

function GitHubButton({ jobId }: { jobId: string; filename: string }) {
  const [state, setState] = useState<ButtonState>("idle");

  const handleClick = async () => {
    if (state === "loading") return;
    setState("loading");
    try {
      const res = await fetch(`/api/backend/github/post-pr/${jobId}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("GitHub post failed");
      setState("done");
      setTimeout(() => setState("idle"), 3000);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  };

  const isDone    = state === "done";
  const isLoading = state === "loading";
  const isError   = state === "error";

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      style={{
        display:       "flex",
        alignItems:    "center",
        gap:           "8px",
        padding:       "9px 20px",
        background:    isDone
          ? "rgba(0,255,135,0.10)"
          : isError
          ? "var(--sev-critical-bg)"
          : "var(--accent-dim)",
        border: `1px solid ${
          isDone  ? "rgba(0,255,135,0.40)" :
          isError ? "var(--sev-critical)"  :
          "var(--accent-border)"
        }`,
        borderRadius:  "6px",
        color:         isDone  ? "#00FF87"             :
                       isError ? "var(--sev-critical)" :
                       "var(--accent)",
        fontFamily:    "var(--font-mono)",
        fontSize:      "11px",
        fontWeight:    600,
        cursor:        isLoading ? "wait" : "pointer",
        transition:    "all 0.2s ease",
        letterSpacing: "0.04em",
        whiteSpace:    "nowrap",
        boxShadow:     !isDone && !isError
          ? "0 0 12px rgba(0,212,255,0.15)"
          : "none",
      }}
      onMouseEnter={(e) => {
        if (!isDone && !isError && !isLoading) {
          (e.currentTarget as HTMLButtonElement).style.boxShadow =
            "0 0 20px rgba(0,212,255,0.30)";
        }
      }}
      onMouseLeave={(e) => {
        if (!isDone && !isError) {
          (e.currentTarget as HTMLButtonElement).style.boxShadow =
            "0 0 12px rgba(0,212,255,0.15)";
        }
      }}
    >
      <svg
        width="14" height="14" viewBox="0 0 24 24"
        fill="currentColor"
        style={{ flexShrink: 0 }}
      >
        <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
      </svg>
      {isLoading ? "Posting…"       :
       isDone    ? "✓ Posted!"      :
       isError   ? "Not configured" :
       "Post to GitHub PR"}
    </button>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function ExportBar({ jobId, filename }: ExportBarProps) {
  return (
    <div style={{
      background:   "var(--bg-surface)",
      border:       "1px solid var(--border-subtle)",
      borderRadius: "12px",
      padding:      "16px 20px",
    }}>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div style={{
        display:      "flex",
        alignItems:   "center",
        gap:          "10px",
        marginBottom: "14px",
      }}>
        <span style={{
          fontFamily:    "var(--font-mono)",
          fontSize:      "11px",
          fontWeight:    600,
          color:         "var(--text-secondary)",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}>
          Export Report
        </span>
        <div style={{ flex: 1, height: "1px", background: "var(--border-subtle)" }} />
        <span style={{
          fontFamily:   "var(--font-mono)",
          fontSize:     "10px",
          color:        "var(--text-muted)",
          overflow:     "hidden",
          textOverflow: "ellipsis",
          whiteSpace:   "nowrap",
          maxWidth:     "160px",
        }}>
          {filename}
        </span>
      </div>

      {/* ── Buttons row ─────────────────────────────────────────────────────── */}
      <div style={{
        display:    "flex",
        gap:        "8px",
        flexWrap:   "wrap",
        alignItems: "center",
      }}>
        {EXPORT_BUTTONS.map(btn => (
          <ExportButton key={btn.format} {...btn} jobId={jobId} />
        ))}

        <div style={{
          width:      "1px",
          height:     "28px",
          background: "var(--border-subtle)",
          margin:     "0 4px",
          flexShrink: 0,
        }} />

        <GitHubButton jobId={jobId} filename={filename} />
      </div>

      {/* ── Job ID ──────────────────────────────────────────────────────────── */}
      <div style={{
        marginTop:  "12px",
        fontFamily: "var(--font-mono)",
        fontSize:   "10px",
        color:      "var(--text-muted)",
        display:    "flex",
        alignItems: "center",
        gap:        "6px",
      }}>
        <span style={{ opacity: 0.5 }}>job_id:</span>
        <span style={{
          color:         "var(--accent)",
          opacity:       0.6,
          letterSpacing: "0.04em",
        }}>
          {jobId}
        </span>
      </div>
    </div>
  );
}