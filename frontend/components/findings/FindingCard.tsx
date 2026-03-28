// components/findings/FindingCard.tsx
"use client";

import { useState } from "react";
import { Finding } from "@/lib/useAnalysisStatus";

// ── Severity Config ───────────────────────────────────────────────────────────

const SEVERITY_CONFIG = {
  Critical: { color: "var(--sev-critical)", bg: "var(--sev-critical-bg)", label: "CRITICAL" },
  High:     { color: "var(--sev-high)",     bg: "var(--sev-high-bg)",     label: "HIGH"     },
  Medium:   { color: "var(--sev-medium)",   bg: "var(--sev-medium-bg)",   label: "MEDIUM"   },
  Low:      { color: "var(--sev-low)",      bg: "var(--sev-low-bg)",      label: "LOW"      },
  Info:     { color: "var(--sev-info)",     bg: "var(--sev-info-bg)",     label: "INFO"     },
};

const ISSUE_TYPE_CONFIG = {
  bug:         { color: "#FF6B6B", label: "Bug",         icon: "🐛" },
  security:    { color: "#FF6B35", label: "Security",    icon: "🔒" },
  performance: { color: "#A78BFA", label: "Performance", icon: "⚡" },
  style:       { color: "#34D399", label: "Style",       icon: "✦"  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

function SeverityBadge({ severity }: { severity: Finding["severity"] }) {
  const cfg = SEVERITY_CONFIG[severity] ?? SEVERITY_CONFIG.Info;
  return (
    <span style={{
      display:       "inline-flex",
      alignItems:    "center",
      padding:       "2px 8px",
      borderRadius:  "4px",
      fontFamily:    "var(--font-mono)",
      fontSize:      "9px",
      fontWeight:    700,
      letterSpacing: "0.10em",
      color:         cfg.color,
      background:    cfg.bg,
      borderLeft:    `3px solid ${cfg.color}`,
      whiteSpace:    "nowrap",
    }}>
      {cfg.label}
    </span>
  );
}

function IssueTypePill({ type }: { type: Finding["issue_type"] }) {
  const cfg = ISSUE_TYPE_CONFIG[type] ?? ISSUE_TYPE_CONFIG.bug;
  return (
    <span style={{
      display:       "inline-flex",
      alignItems:    "center",
      gap:           "4px",
      padding:       "2px 8px",
      borderRadius:  "100px",
      fontSize:      "10px",
      fontFamily:    "var(--font-mono)",
      color:         cfg.color,
      background:    `${cfg.color}15`,
      border:        `1px solid ${cfg.color}30`,
      whiteSpace:    "nowrap",
    }}>
      <span>{cfg.icon}</span>
      <span>{cfg.label}</span>
    </span>
  );
}

// ── Diff View ─────────────────────────────────────────────────────────────────

function DiffView({ suggestion }: { suggestion: string }) {
  if (!suggestion.trim()) {
    return (
      <p style={{
        fontFamily: "var(--font-mono)",
        fontSize:   "11px",
        color:      "var(--text-muted)",
        fontStyle:  "italic",
      }}>
        No auto-fix available for this finding.
      </p>
    );
  }

  const lines = suggestion.split("\n");

  return (
    <div style={{
      background:   "var(--bg-code)",
      border:       "1px solid var(--border-subtle)",
      borderRadius: "6px",
      overflow:     "hidden",
      fontSize:     "11px",
      fontFamily:   "var(--font-mono)",
      lineHeight:   1.7,
    }}>
      {/* Header bar */}
      <div style={{
        display:       "flex",
        alignItems:    "center",
        gap:           "6px",
        padding:       "6px 12px",
        background:    "var(--bg-elevated)",
        borderBottom:  "1px solid var(--border-subtle)",
        fontSize:      "10px",
        color:         "var(--text-muted)",
        letterSpacing: "0.06em",
      }}>
        <span style={{ color: "#FF6B6B" }}>−</span> before
        <span style={{ marginLeft: "12px", color: "#34D399" }}>+</span> after
      </div>

      {/* Lines */}
      <div style={{ padding: "8px 0", overflowX: "auto" }}>
        {lines.map((line, i) => {
          const isAdded   = line.startsWith("+") && !line.startsWith("+++");
          const isRemoved = line.startsWith("-") && !line.startsWith("---");
          const isHunk    = line.startsWith("@@");

          return (
            <div
              key={i}
              style={{
                display:    "flex",
                padding:    "1px 12px",
                background: isAdded
                  ? "rgba(52, 211, 153, 0.08)"
                  : isRemoved
                  ? "rgba(255, 107, 107, 0.08)"
                  : isHunk
                  ? "rgba(0, 212, 255, 0.05)"
                  : "transparent",
                color: isAdded
                  ? "#34D399"
                  : isRemoved
                  ? "#FF6B6B"
                  : isHunk
                  ? "var(--accent)"
                  : "var(--text-secondary)",
                whiteSpace: "pre",
              }}
            >
              {line || " "}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main Finding Card ─────────────────────────────────────────────────────────

interface FindingCardProps {
  finding: Finding;
  index:   number;
}

export default function FindingCard({ finding, index }: FindingCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [visible,  setVisible]  = useState(false);

  // Stagger mount
  useState(() => {
    const t = setTimeout(() => setVisible(true), index * 60);
    return () => clearTimeout(t);
  });

  const severityCfg = SEVERITY_CONFIG[finding.severity] ?? SEVERITY_CONFIG.Info;

  return (
    <div
      style={{
        background:   "var(--bg-surface)",
        border:       "1px solid var(--border-subtle)",
        borderLeft:   `3px solid ${severityCfg.color}`,
        borderRadius: "8px",
        overflow:     "hidden",
        opacity:      visible ? 1 : 0,
        transform:    visible ? "translateY(0)" : "translateY(10px)",
        transition:   `opacity 0.35s ease ${index * 40}ms, transform 0.35s ease ${index * 40}ms, border-color 0.2s ease, box-shadow 0.2s ease`,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor      = `${severityCfg.color}`;
        (e.currentTarget as HTMLDivElement).style.boxShadow        = `0 0 16px ${severityCfg.color}22`;
        (e.currentTarget as HTMLDivElement).style.borderLeftColor  = severityCfg.color;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor     = "var(--border-subtle)";
        (e.currentTarget as HTMLDivElement).style.boxShadow       = "none";
        (e.currentTarget as HTMLDivElement).style.borderLeftColor = severityCfg.color;
      }}
    >
      {/* ── Main row ────────────────────────────────────────────────────────── */}
      <div
        style={{
          padding:  "14px 16px",
          cursor:   "pointer",
          display:  "flex",
          flexDirection: "column",
          gap:      "10px",
        }}
        onClick={() => setExpanded(!expanded)}
      >
        {/* Top row: badges + line info */}
        <div style={{
          display:    "flex",
          alignItems: "center",
          gap:        "8px",
          flexWrap:   "wrap",
        }}>
          <SeverityBadge severity={finding.severity} />
          <IssueTypePill type={finding.issue_type} />

          {/* File + line */}
          <span style={{
            fontFamily:   "var(--font-mono)",
            fontSize:     "10px",
            color:        "var(--text-muted)",
            marginLeft:   "auto",
            whiteSpace:   "nowrap",
          }}>
            {fileName(finding.file_path)}
            <span style={{ color: "var(--accent)", marginLeft: "4px" }}>
              :{finding.start_line}
              {finding.end_line !== finding.start_line && `–${finding.end_line}`}
            </span>
          </span>
        </div>

        {/* Description */}
        <p style={{
          fontSize:   "13px",
          color:      "var(--text-primary)",
          lineHeight: 1.5,
          margin:     0,
        }}>
          {finding.description}
        </p>

        {/* Bottom row: tags + expand toggle */}
        <div style={{
          display:    "flex",
          alignItems: "center",
          gap:        "6px",
          flexWrap:   "wrap",
        }}>
          {/* Confidence */}
          <span style={{
            fontFamily:    "var(--font-mono)",
            fontSize:      "9px",
            color:         "var(--text-muted)",
            border:        "1px solid var(--border-subtle)",
            borderRadius:  "4px",
            padding:       "1px 6px",
          }}>
            {Math.round(finding.confidence * 100)}% conf
          </span>

          {/* Tags */}
          {finding.tags.slice(0, 3).map((tag) => (
            <span key={tag} style={{
              fontFamily:   "var(--font-mono)",
              fontSize:     "9px",
              color:        "var(--text-muted)",
              background:   "var(--bg-elevated)",
              border:       "1px solid var(--border-subtle)",
              borderRadius: "4px",
              padding:      "1px 6px",
            }}>
              {tag}
            </span>
          ))}

          {/* Expand toggle */}
          {(finding.remediation || finding.code_suggestion) && (
            <span style={{
              marginLeft:    "auto",
              fontFamily:    "var(--font-mono)",
              fontSize:      "10px",
              color:         "var(--accent)",
              display:       "flex",
              alignItems:    "center",
              gap:           "4px",
              userSelect:    "none",
            }}>
              {expanded ? "▲ Hide Fix" : "▼ View Fix"}
            </span>
          )}
        </div>
      </div>

      {/* ── Expanded section ─────────────────────────────────────────────────── */}
      <div style={{
        maxHeight:  expanded ? "600px" : "0",
        overflow:   "hidden",
        transition: "max-height 0.35s ease",
      }}>
        <div style={{
          padding:    "0 16px 16px",
          borderTop:  "1px solid var(--border-subtle)",
          paddingTop: "14px",
          display:    "flex",
          flexDirection: "column",
          gap:        "14px",
        }}>

          {/* Remediation */}
          {finding.remediation && (
            <div>
              <div style={{
                fontFamily:    "var(--font-mono)",
                fontSize:      "10px",
                color:         "var(--text-muted)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                marginBottom:  "6px",
              }}>
                Remediation
              </div>
              <p style={{
                fontSize:   "12px",
                color:      "var(--text-secondary)",
                lineHeight: 1.6,
                margin:     0,
              }}>
                {finding.remediation}
              </p>
            </div>
          )}

          {/* Code suggestion diff */}
          {(finding.code_suggestion !== undefined) && (
            <div>
              <div style={{
                fontFamily:    "var(--font-mono)",
                fontSize:      "10px",
                color:         "var(--text-muted)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                marginBottom:  "6px",
              }}>
                Suggested Fix
              </div>
              <DiffView suggestion={finding.code_suggestion} />
            </div>
          )}

          {/* References */}
          {finding.references && finding.references.length > 0 && (
            <div style={{
              display:    "flex",
              gap:        "6px",
              flexWrap:   "wrap",
              alignItems: "center",
            }}>
              <span style={{
                fontFamily:    "var(--font-mono)",
                fontSize:      "9px",
                color:         "var(--text-muted)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}>
                Refs:
              </span>
              {finding.references.map((ref) => (
                <span key={ref} style={{
                  fontFamily:   "var(--font-mono)",
                  fontSize:     "9px",
                  color:        "var(--accent)",
                  background:   "var(--accent-dim)",
                  border:       "1px solid var(--accent-border)",
                  borderRadius: "4px",
                  padding:      "1px 6px",
                }}>
                  {ref}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
