// components/heatmap/FileHeatmap.tsx
"use client";

import { useMemo, useState } from "react";
import { Finding } from "@/lib/useAnalysisStatus";

// ── Types ─────────────────────────────────────────────────────────────────────

interface FileHeatmapProps {
  findings:      Finding[];
  activeFile:    string | null;
  onFileSelect:  (file: string | null) => void;
}

interface FileRisk {
  path:       string;
  name:       string;
  score:      number;   // 0–100 risk (higher = worse)
  critical:   number;
  high:       number;
  medium:     number;
  low:        number;
  info:       number;
  total:      number;
}

// ── Risk Score Calculator ─────────────────────────────────────────────────────

const SEVERITY_WEIGHTS: Record<string, number> = {
  Critical: 40,
  High:     20,
  Medium:   8,
  Low:      2,
  Info:     0.5,
};

function calcRiskScore(findings: Finding[]): number {
  const raw = findings.reduce((sum, f) => sum + (SEVERITY_WEIGHTS[f.severity] ?? 0), 0);
  return Math.min(100, raw);
}

// ── Risk → color ──────────────────────────────────────────────────────────────

function riskColor(score: number): string {
  if (score >= 80) return "#FF3B3B";
  if (score >= 60) return "#FF6B35";
  if (score >= 40) return "#FFB347";
  if (score >= 20) return "#4A9EFF";
  return "#34D399";
}

function riskLabel(score: number): string {
  if (score >= 80) return "Critical";
  if (score >= 60) return "High";
  if (score >= 40) return "Medium";
  if (score >= 20) return "Low";
  return "Clean";
}

// ── File Icon ─────────────────────────────────────────────────────────────────

function fileIcon(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "py")                        return "🐍";
  if (ext === "java")                      return "☕";
  if (ext === "js" || ext === "jsx")       return "⚡";
  if (ext === "ts" || ext === "tsx")       return "⚡";
  if (ext === "zip")                       return "📦";
  return "📄";
}

// ── Risk Bar ──────────────────────────────────────────────────────────────────

function RiskBar({ score, color }: { score: number; color: string }) {
  return (
    <div style={{
      width:        "100%",
      height:       "3px",
      background:   "var(--border-subtle)",
      borderRadius: "2px",
      overflow:     "hidden",
      marginTop:    "6px",
    }}>
      <div style={{
        height:     "100%",
        width:      `${score}%`,
        background: color,
        borderRadius: "2px",
        boxShadow:  `0 0 6px ${color}66`,
        transition: "width 0.8s ease",
      }} />
    </div>
  );
}

// ── Severity Dot Row ──────────────────────────────────────────────────────────

function SeverityDots({ file }: { file: FileRisk }) {
  const items = [
    { count: file.critical, color: "var(--sev-critical)", label: "C" },
    { count: file.high,     color: "var(--sev-high)",     label: "H" },
    { count: file.medium,   color: "var(--sev-medium)",   label: "M" },
    { count: file.low,      color: "var(--sev-low)",      label: "L" },
  ].filter(i => i.count > 0);

  return (
    <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
      {items.map(({ count, color, label }) => (
        <span
          key={label}
          style={{
            fontFamily:   "var(--font-mono)",
            fontSize:     "9px",
            color,
            background:   `${color}18`,
            border:       `1px solid ${color}30`,
            borderRadius: "4px",
            padding:      "1px 5px",
          }}
        >
          {count}{label}
        </span>
      ))}
    </div>
  );
}

// ── File Row ──────────────────────────────────────────────────────────────────

function FileRow({
  file,
  isActive,
  maxScore,
  onClick,
}: {
  file:     FileRisk;
  isActive: boolean;
  maxScore: number;
  onClick:  () => void;
}) {
  const color      = riskColor(file.score);
  const normalized = maxScore > 0 ? (file.score / maxScore) * 100 : 0;

  return (
    <div
      onClick={onClick}
      style={{
        padding:      "10px 12px",
        borderRadius: "6px",
        border:       `1px solid ${isActive ? color + "60" : "var(--border-subtle)"}`,
        background:   isActive ? `${color}0D` : "var(--bg-surface)",
        cursor:       "pointer",
        transition:   "all 0.2s ease",
        position:     "relative",
        overflow:     "hidden",
      }}
      onMouseEnter={e => {
        if (!isActive) {
          (e.currentTarget as HTMLDivElement).style.borderColor  = `${color}40`;
          (e.currentTarget as HTMLDivElement).style.background   = `${color}08`;
        }
      }}
      onMouseLeave={e => {
        if (!isActive) {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-subtle)";
          (e.currentTarget as HTMLDivElement).style.background  = "var(--bg-surface)";
        }
      }}
    >
      {/* Active indicator stripe */}
      {isActive && (
        <div style={{
          position:   "absolute",
          left:       0,
          top:        0,
          bottom:     0,
          width:      "3px",
          background: color,
          boxShadow:  `0 0 8px ${color}`,
        }} />
      )}

      {/* Top row */}
      <div style={{
        display:        "flex",
        alignItems:     "center",
        justifyContent: "space-between",
        gap:            "8px",
        paddingLeft:    isActive ? "8px" : "0",
      }}>
        {/* File name + icon */}
        <div style={{
          display:    "flex",
          alignItems: "center",
          gap:        "7px",
          minWidth:   0,
        }}>
          <span style={{ fontSize: "13px", flexShrink: 0 }}>
            {fileIcon(file.name)}
          </span>
          <span style={{
            fontFamily:   "var(--font-mono)",
            fontSize:     "11px",
            color:        isActive ? "var(--text-primary)" : "var(--text-secondary)",
            overflow:     "hidden",
            textOverflow: "ellipsis",
            whiteSpace:   "nowrap",
            fontWeight:   isActive ? 600 : 400,
          }}>
            {file.name}
          </span>
        </div>

        {/* Risk badge */}
        <div style={{
          display:      "flex",
          alignItems:   "center",
          gap:          "6px",
          flexShrink:   0,
        }}>
          <span style={{
            fontFamily:    "var(--font-mono)",
            fontSize:      "9px",
            color,
            background:    `${color}18`,
            border:        `1px solid ${color}30`,
            borderRadius:  "4px",
            padding:       "1px 6px",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
          }}>
            {riskLabel(file.score)}
          </span>
          <span style={{
            fontFamily: "var(--font-mono)",
            fontSize:   "10px",
            color:      "var(--text-muted)",
          }}>
            {file.total}
          </span>
        </div>
      </div>

      {/* Severity dots */}
      <div style={{
        marginTop:   "6px",
        paddingLeft: isActive ? "8px" : "0",
      }}>
        <SeverityDots file={file} />
      </div>

      {/* Risk bar */}
      <div style={{ paddingLeft: isActive ? "8px" : "0" }}>
        <RiskBar score={normalized} color={color} />
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function FileHeatmap({
  findings,
  activeFile,
  onFileSelect,
}: FileHeatmapProps) {

  // ── Build per-file risk data ─────────────────────────────────────────────
  const fileRisks = useMemo<FileRisk[]>(() => {
    const map = new Map<string, Finding[]>();
    findings.forEach(f => {
      const list = map.get(f.file_path) ?? [];
      list.push(f);
      map.set(f.file_path, list);
    });

    const risks: FileRisk[] = [];
    map.forEach((fList, path) => {
      const counts = { Critical: 0, High: 0, Medium: 0, Low: 0, Info: 0 };
      fList.forEach(f => { counts[f.severity] = (counts[f.severity] ?? 0) + 1; });
      risks.push({
        path,
        name:     path.split(/[\\/]/).pop() ?? path,
        score:    calcRiskScore(fList),
        critical: counts.Critical,
        high:     counts.High,
        medium:   counts.Medium,
        low:      counts.Low,
        info:     counts.Info,
        total:    fList.length,
      });
    });

    return risks.sort((a, b) => b.score - a.score);
  }, [findings]);

  const maxScore = useMemo(
    () => Math.max(...fileRisks.map(f => f.score), 1),
    [fileRisks]
  );

  const handleClick = (path: string) => {
    onFileSelect(activeFile === path ? null : path);
  };

  return (
    <div style={{
      background:   "var(--bg-surface)",
      border:       "1px solid var(--border-subtle)",
      borderRadius: "12px",
      padding:      "20px",
    }}>

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div style={{
        display:        "flex",
        alignItems:     "center",
        justifyContent: "space-between",
        marginBottom:   "16px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{
            fontFamily:    "var(--font-mono)",
            fontSize:      "11px",
            fontWeight:    600,
            color:         "var(--text-secondary)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}>
            File Risk Map
          </span>
          <div style={{ width: "40px", height: "1px", background: "var(--border-subtle)" }} />
        </div>

        {activeFile && (
          <button
            onClick={() => onFileSelect(null)}
            style={{
              fontFamily:  "var(--font-mono)",
              fontSize:    "10px",
              color:       "var(--text-muted)",
              background:  "none",
              border:      "none",
              cursor:      "pointer",
              padding:     "2px 6px",
            }}
          >
            Clear filter ✕
          </button>
        )}
      </div>

      {/* ── Risk legend ───────────────────────────────────────────────────── */}
      <div style={{
        display:       "flex",
        gap:           "10px",
        marginBottom:  "14px",
        flexWrap:      "wrap",
      }}>
        {[
          { label: "Critical", color: "#FF3B3B", min: 80  },
          { label: "High",     color: "#FF6B35", min: 60  },
          { label: "Medium",   color: "#FFB347", min: 40  },
          { label: "Low",      color: "#4A9EFF", min: 20  },
          { label: "Clean",    color: "#34D399", min: 0   },
        ].map(({ label, color }) => (
          <div key={label} style={{
            display:    "flex",
            alignItems: "center",
            gap:        "5px",
          }}>
            <div style={{
              width:        "8px",
              height:       "8px",
              borderRadius: "50%",
              background:   color,
              boxShadow:    `0 0 4px ${color}`,
            }} />
            <span style={{
              fontFamily: "var(--font-mono)",
              fontSize:   "9px",
              color:      "var(--text-muted)",
            }}>
              {label}
            </span>
          </div>
        ))}
      </div>

      {/* ── Divider ───────────────────────────────────────────────────────── */}
      <div style={{ height: "1px", background: "var(--border-subtle)", marginBottom: "12px" }} />

      {/* ── File list ─────────────────────────────────────────────────────── */}
      {fileRisks.length === 0 ? (
        <div style={{
          padding:    "32px",
          textAlign:  "center",
          fontFamily: "var(--font-mono)",
          fontSize:   "12px",
          color:      "var(--text-muted)",
        }}>
          No files analyzed yet
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {fileRisks.map(file => (
            <FileRow
              key={file.path}
              file={file}
              isActive={activeFile === file.path}
              maxScore={maxScore}
              onClick={() => handleClick(file.path)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
