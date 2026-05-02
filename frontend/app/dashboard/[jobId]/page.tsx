// app/dashboard/[jobId]/page.tsx
"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAnalysisStatus } from "@/lib/useAnalysisStatus";
import PipelineTracker  from "@/components/pipeline/PipelineTracker";
import ScoreGauge       from "@/components/score/ScoreGauge";
import SubScoreRings    from "@/components/score/SubScoreRings";
import FindingsPanel    from "@/components/findings/FindingsPanel";
import FileHeatmap      from "@/components/heatmap/FileHeatmap";
import ExportBar        from "@/components/export/ExportBar";

// ── Skeleton block ────────────────────────────────────────────────────────────

function Skeleton({ w, h }: { w: string; h: string }) {
  return (
    <div
      className="skeleton"
      style={{ width: w, height: h, borderRadius: "6px" }}
    />
  );
}

// ── Nav bar ───────────────────────────────────────────────────────────────────

function NavBar({ onBack }: { onBack: () => void }) {
  return (
    <nav style={{
      position:       "sticky",
      top:            0,
      zIndex:         40,
      display:        "flex",
      alignItems:     "center",
      justifyContent: "space-between",
      padding:        "12px 32px",
      background:     "rgba(9, 12, 16, 0.85)",
      backdropFilter: "blur(12px)",
      borderBottom:   "1px solid var(--border-subtle)",
    }}>
      <button
        onClick={onBack}
        style={{
          display:    "flex",
          alignItems: "center",
          gap:        "10px",
          background: "none",
          border:     "none",
          cursor:     "pointer",
          padding:    0,
        }}
      >
        <span style={{
          fontSize:      "16px",
          color:         "var(--accent)",
          fontFamily:    "var(--font-mono)",
          letterSpacing: "-0.02em",
          fontWeight:    700,
        }}>
          ◈ CodeScan
        </span>
        <span style={{
          fontSize:   "11px",
          color:      "var(--text-muted)",
          fontFamily: "var(--font-mono)",
        }}>
          / dashboard
        </span>
      </button>

      <button
        onClick={onBack}
        style={{
          display:       "flex",
          alignItems:    "center",
          gap:           "6px",
          padding:       "6px 14px",
          background:    "var(--bg-elevated)",
          border:        "1px solid var(--border-default)",
          borderRadius:  "6px",
          color:         "var(--text-secondary)",
          fontFamily:    "var(--font-mono)",
          fontSize:      "11px",
          cursor:        "pointer",
          transition:    "all 0.2s ease",
          letterSpacing: "0.04em",
        }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent-border)";
          (e.currentTarget as HTMLButtonElement).style.color       = "var(--accent)";
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-default)";
          (e.currentTarget as HTMLButtonElement).style.color       = "var(--text-secondary)";
        }}
      >
        + New Analysis
      </button>
    </nav>
  );
}

// ── Plagiarism / AI-Detection Banner ─────────────────────────────────────────

interface PlagiarismBannerProps {
  result: {
    score: number;
    verdict: string;
    blocked: boolean;
    summary?: string;
    evidence?: string[];
    remedies?: string[];
    heuristic_score?: number;
    llm_score?: number;
  };
}

function PlagiarismBanner({ result }: PlagiarismBannerProps) {
  const [expanded, setExpanded] = useState(false);

  const isBlocked    = result.blocked;
  const isSuspicious = result.verdict === "SUSPICIOUS";
  const score        = Math.round(result.score);

  // Color scheme based on severity
  const accentColor  = isBlocked    ? "#FF4444"
                     : isSuspicious ? "#FF9500"
                     :                "#4CAF50";
  const bgColor      = isBlocked    ? "rgba(255, 68,  68,  0.08)"
                     : isSuspicious ? "rgba(255,149,  0,  0.08)"
                     :                "rgba( 76,175, 80,  0.08)";
  const borderColor  = isBlocked    ? "rgba(255, 68,  68,  0.35)"
                     : isSuspicious ? "rgba(255,149,  0,  0.35)"
                     :                "rgba( 76,175, 80,  0.35)";

  const icon  = isBlocked ? "🚫" : isSuspicious ? "⚠️" : "✅";
  const label = isBlocked    ? "REVIEW BLOCKED — AI/Plagiarism Detected"
              : isSuspicious ? "SUSPICIOUS — Possible AI/Plagiarism"
              :                "PASSED — No Plagiarism Detected";

  return (
    <div style={{
      background:   bgColor,
      border:       `1px solid ${borderColor}`,
      borderRadius: "10px",
      marginBottom: "28px",
      overflow:     "hidden",
    }}>
      {/* ── Header row ── */}
      <div style={{
        display:     "flex",
        alignItems:  "center",
        gap:         "12px",
        padding:     "16px 20px",
        cursor:      result.evidence?.length ? "pointer" : "default",
        userSelect:  "none",
      }}
        onClick={() => result.evidence?.length && setExpanded(p => !p)}
      >
        {/* Score ring */}
        <div style={{
          flexShrink:    0,
          width:         "52px",
          height:        "52px",
          borderRadius:  "50%",
          border:        `2px solid ${accentColor}`,
          display:       "flex",
          flexDirection: "column",
          alignItems:    "center",
          justifyContent:"center",
          background:    `${accentColor}18`,
          boxShadow:     `0 0 12px ${accentColor}30`,
        }}>
          <span style={{ fontSize: "15px", fontWeight: 800, color: accentColor, fontFamily: "var(--font-mono)", lineHeight: 1 }}>
            {score}
          </span>
          <span style={{ fontSize: "8px", color: accentColor, fontFamily: "var(--font-mono)", opacity: 0.8 }}>
            /100
          </span>
        </div>

        {/* Label + summary */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            display:    "flex",
            alignItems: "center",
            gap:        "8px",
            flexWrap:   "wrap",
          }}>
            <span style={{ fontSize: "13px" }}>{icon}</span>
            <span style={{
              fontFamily:    "var(--font-mono)",
              fontSize:      "12px",
              fontWeight:    700,
              color:         accentColor,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
            }}>
              {label}
            </span>
            {isBlocked && (
              <span style={{
                fontFamily:   "var(--font-mono)",
                fontSize:     "10px",
                padding:      "2px 7px",
                borderRadius: "4px",
                background:   `${accentColor}22`,
                border:       `1px solid ${accentColor}44`,
                color:        accentColor,
              }}>
                Pipeline Halted
              </span>
            )}
          </div>

          {result.summary && (
            <p style={{
              fontFamily:  "var(--font-mono)",
              fontSize:    "11px",
              color:       "var(--text-muted)",
              marginTop:   "4px",
              lineHeight:  1.5,
              whiteSpace:  "pre-wrap",
            }}>
              {/* Strip leading emoji from summary to avoid duplication */}
              {result.summary.replace(/^[^\w]*/, "")}
            </p>
          )}
        </div>

        {/* Scores pills */}
        <div style={{ display: "flex", gap: "8px", flexShrink: 0, alignItems: "center" }}>
          {result.heuristic_score !== undefined && (
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
                {result.heuristic_score.toFixed(0)}
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                Heuristic
              </div>
            </div>
          )}
          {result.heuristic_score !== undefined && result.llm_score !== undefined && (
            <div style={{ width: "1px", height: "28px", background: "var(--border-subtle)" }} />
          )}
          {result.llm_score !== undefined && (
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
                {result.llm_score.toFixed(0)}
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                LLM
              </div>
            </div>
          )}

          {/* Expand chevron */}
          {result.evidence?.length ? (
            <div style={{
              marginLeft:  "4px",
              color:       "var(--text-muted)",
              fontSize:    "12px",
              transition:  "transform 0.2s ease",
              transform:   expanded ? "rotate(180deg)" : "rotate(0deg)",
            }}>
              ▾
            </div>
          ) : null}
        </div>
      </div>

      {/* ── Expanded details ── */}
      {expanded && (
        <div style={{
          borderTop:  `1px solid ${borderColor}`,
          padding:    "16px 20px",
          display:    "grid",
          gridTemplateColumns: "1fr 1fr",
          gap:        "16px",
        }}>
          {/* Evidence */}
          {result.evidence && result.evidence.length > 0 && (
            <div>
              <div style={{
                fontFamily:    "var(--font-mono)",
                fontSize:      "10px",
                color:         accentColor,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                marginBottom:  "8px",
              }}>
                🔍 Evidence
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "6px" }}>
                {result.evidence.map((e, i) => (
                  <li key={i} style={{
                    fontFamily:  "var(--font-mono)",
                    fontSize:    "11px",
                    color:       "var(--text-secondary)",
                    paddingLeft: "12px",
                    position:    "relative",
                    lineHeight:  1.5,
                  }}>
                    <span style={{ position: "absolute", left: 0, color: accentColor }}>›</span>
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Remedies */}
          {result.remedies && result.remedies.length > 0 && (
            <div>
              <div style={{
                fontFamily:    "var(--font-mono)",
                fontSize:      "10px",
                color:         "var(--accent)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                marginBottom:  "8px",
              }}>
                💡 How to Fix
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "6px" }}>
                {result.remedies.map((r, i) => (
                  <li key={i} style={{
                    fontFamily:  "var(--font-mono)",
                    fontSize:    "11px",
                    color:       "var(--text-secondary)",
                    paddingLeft: "12px",
                    position:    "relative",
                    lineHeight:  1.5,
                  }}>
                    <span style={{ position: "absolute", left: 0, color: "var(--accent)" }}>›</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Loading state (pipeline running) ─────────────────────────────────────────

function LoadingState({ stages, status }: {
  stages: ReturnType<typeof useAnalysisStatus>["stages"];
  status: ReturnType<typeof useAnalysisStatus>["status"];
}) {
  return (
    <div style={{
      display:        "flex",
      flexDirection:  "column",
      alignItems:     "center",
      justifyContent: "center",
      minHeight:      "60vh",
      gap:            "32px",
      padding:        "32px",
    }}>
      <div style={{
        fontFamily:  "var(--font-mono)",
        fontSize:    "32px",
        color:       "var(--accent)",
        animation:   "pulse 2s ease infinite",
        textShadow:  "0 0 30px rgba(0,212,255,0.5)",
      }}>
        ◈
      </div>

      <div style={{ textAlign: "center" }}>
        <h2 style={{
          fontFamily:    "var(--font-mono)",
          fontSize:      "18px",
          color:         "var(--text-primary)",
          marginBottom:  "8px",
          letterSpacing: "-0.02em",
        }}>
          Analyzing your code
        </h2>
        <p style={{
          fontSize:   "13px",
          color:      "var(--text-muted)",
          fontFamily: "var(--font-mono)",
        }}>
          {status?.message ?? "Starting pipeline…"}
        </p>
      </div>

      <div style={{ width: "100%", maxWidth: "860px" }}>
        <PipelineTracker
          stages={stages}
          currentMessage={status?.message}
          progress={status?.progress ?? 0}
        />
      </div>
    </div>
  );
}

// ── Error state ───────────────────────────────────────────────────────────────

function ErrorState({ error, onBack }: { error: string; onBack: () => void }) {
  return (
    <div style={{
      display:        "flex",
      flexDirection:  "column",
      alignItems:     "center",
      justifyContent: "center",
      minHeight:      "60vh",
      gap:            "16px",
      padding:        "32px",
      textAlign:      "center",
    }}>
      <div style={{ fontSize: "40px" }}>⚠</div>
      <h2 style={{
        fontFamily: "var(--font-mono)",
        fontSize:   "18px",
        color:      "var(--sev-critical)",
      }}>
        Pipeline Failed
      </h2>
      <p style={{
        fontFamily: "var(--font-mono)",
        fontSize:   "12px",
        color:      "var(--text-muted)",
        maxWidth:   "400px",
      }}>
        {error}
      </p>
      <button
        onClick={onBack}
        style={{
          marginTop:    "8px",
          padding:      "9px 20px",
          background:   "var(--bg-elevated)",
          border:       "1px solid var(--border-default)",
          borderRadius: "6px",
          color:        "var(--text-secondary)",
          fontFamily:   "var(--font-mono)",
          fontSize:     "12px",
          cursor:       "pointer",
        }}
      >
        ← Try Again
      </button>
    </div>
  );
}

// ── Main Dashboard Page ───────────────────────────────────────────────────────

export default function DashboardPage() {
  const params    = useParams();
  const router    = useRouter();
  const jobId     = params?.jobId as string ?? "";

  const { status, stages, report, isComplete, isFailed, error } =
    useAnalysisStatus(jobId);

  const [activeFile,  setActiveFile]  = useState<string | null>(null);
  const [pageVisible, setPageVisible] = useState(false);

  useEffect(() => {
    if (isComplete) {
      const t = setTimeout(() => setPageVisible(true), 100);
      return () => clearTimeout(t);
    }
  }, [isComplete]);

  const handleBack = () => router.push("/");

  // Merge agent + static findings for display
  const allFindings = report
    ? [...(report.findings ?? []), ...(report.static_findings ?? [])]
    : [];

  // ── Plagiarism blocked? Show minimal blocked view instead of full dashboard ──
  const plagiarism       = report?.plagiarism_result;
  const isPlagiarismBlocked = plagiarism?.blocked === true;

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div style={{ minHeight: "100vh" }}>
      <NavBar onBack={handleBack} />

      {/* ── Pipeline still running ───────────────────────────────────────────── */}
      {!isComplete && !isFailed && (
        <LoadingState stages={stages} status={status} />
      )}

      {/* ── Failed ──────────────────────────────────────────────────────────── */}
      {isFailed && (
        <ErrorState error={error ?? "Unknown error"} onBack={handleBack} />
      )}

      {/* ── Complete ────────────────────────────────────────────────────────── */}
      {isComplete && report && (
        <div style={{
          maxWidth:  "1400px",
          margin:    "0 auto",
          padding:   "32px 24px 80px",
          opacity:   pageVisible ? 1 : 0,
          transform: pageVisible ? "translateY(0)" : "translateY(12px)",
          transition:"opacity 0.5s ease, transform 0.5s ease",
        }}>

          {/* ── File info bar ─────────────────────────────────────────────────── */}
          <div style={{
            display:       "flex",
            alignItems:    "center",
            gap:           "12px",
            marginBottom:  "32px",
            paddingBottom: "20px",
            borderBottom:  "1px solid var(--border-subtle)",
            flexWrap:      "wrap",
          }}>
            <span style={{ fontSize: "20px" }}>
              {report.language === "python"     ? "🐍" :
               report.language === "java"       ? "☕" :
               report.language === "javascript" ? "⚡" : "📄"}
            </span>
            <div>
              <div style={{
                fontFamily:    "var(--font-mono)",
                fontSize:      "16px",
                fontWeight:    700,
                color:         "var(--text-primary)",
                letterSpacing: "-0.02em",
              }}>
                {report.filename}
              </div>
              <div style={{
                fontFamily: "var(--font-mono)",
                fontSize:   "11px",
                color:      "var(--text-muted)",
                marginTop:  "2px",
              }}>
                {report.language} · {report.total_findings} findings
              </div>
            </div>

            <div style={{ flex: 1 }} />

            {/* Severity chips — only when NOT blocked */}
            {!isPlagiarismBlocked && (["Critical","High","Medium","Low"] as const).map(sev => {
              const count = allFindings.filter(f => f.severity === sev).length;
              if (!count) return null;
              const colors: Record<string,string> = {
                Critical: "var(--sev-critical)",
                High:     "var(--sev-high)",
                Medium:   "var(--sev-medium)",
                Low:      "var(--sev-low)",
              };
              return (
                <span key={sev} style={{
                  fontFamily:   "var(--font-mono)",
                  fontSize:     "10px",
                  color:        colors[sev],
                  background:   `${colors[sev]}18`,
                  border:       `1px solid ${colors[sev]}30`,
                  borderRadius: "4px",
                  padding:      "3px 8px",
                }}>
                  {count} {sev}
                </span>
              );
            })}
          </div>

          {/* ── Pipeline tracker (completed state) ──────────────────────────── */}
          <div style={{ marginBottom: "32px" }}>
            <PipelineTracker stages={stages} progress={100} />
          </div>

          {/* ── PLAGIARISM BANNER (always shown when present) ─────────────────── */}
          {plagiarism && (
            <PlagiarismBanner result={plagiarism} />
          )}

          {/* ── BLOCKED STATE — no findings to show ─────────────────────────── */}
          {isPlagiarismBlocked ? (
            <div style={{
              display:        "flex",
              flexDirection:  "column",
              alignItems:     "center",
              justifyContent: "center",
              padding:        "60px 24px",
              gap:            "12px",
              textAlign:      "center",
              background:     "rgba(255,68,68,0.04)",
              border:         "1px dashed rgba(255,68,68,0.25)",
              borderRadius:   "12px",
            }}>
              <div style={{ fontSize: "48px" }}>🚫</div>
              <h2 style={{
                fontFamily:    "var(--font-mono)",
                fontSize:      "16px",
                fontWeight:    700,
                color:         "var(--sev-critical, #FF4444)",
                letterSpacing: "-0.02em",
              }}>
                Analysis Blocked
              </h2>
              <p style={{
                fontFamily: "var(--font-mono)",
                fontSize:   "12px",
                color:      "var(--text-muted)",
                maxWidth:   "480px",
                lineHeight: 1.6,
              }}>
                The pipeline was halted because this file exceeded the AI/plagiarism
                threshold. No code review findings are available. See the banner above
                for details and remediation steps.
              </p>
              <button
                onClick={handleBack}
                style={{
                  marginTop:    "8px",
                  padding:      "9px 22px",
                  background:   "var(--bg-elevated)",
                  border:       "1px solid var(--border-default)",
                  borderRadius: "6px",
                  color:        "var(--text-secondary)",
                  fontFamily:   "var(--font-mono)",
                  fontSize:     "12px",
                  cursor:       "pointer",
                }}
              >
                ← Submit a new file
              </button>
            </div>

          ) : (
            /* ── NORMAL DASHBOARD (not blocked) ────────────────────────────── */
            <div style={{
              display:             "grid",
              gridTemplateColumns: "340px 1fr",
              gap:                 "24px",
              alignItems:          "start",
            }}>
              {/* LEFT COLUMN */}
              <div style={{
                display:       "flex",
                flexDirection: "column",
                gap:           "24px",
                position:      "sticky",
                top:           "80px",
              }}>
                <div style={{
                  background:   "var(--bg-surface)",
                  border:       "1px solid var(--border-subtle)",
                  borderRadius: "12px",
                  padding:      "28px 20px 20px",
                  display:      "flex",
                  flexDirection:"column",
                  alignItems:   "center",
                  gap:          "24px",
                  marginLeft:   "-8px",
                  marginRight:  "-4px",
                }}>
                  <ScoreGauge
                    score={report.overall_score}
                    verdict={report.verdict}
                    animate={true}
                  />
                  <div style={{ width: "100%" }}>
                    <SubScoreRings
                      scores={report.sub_scores}
                      animate={true}
                    />
                  </div>
                </div>

                <FileHeatmap
                  findings={allFindings}
                  activeFile={activeFile}
                  onFileSelect={setActiveFile}
                />

                <ExportBar jobId={jobId} filename={report.filename} />
              </div>

              {/* RIGHT COLUMN */}
              <div>
                <FindingsPanel
                  findings={allFindings}
                  activeFile={activeFile}
                  onFileClick={(file) =>
                    setActiveFile(prev => prev === file ? null : file)
                  }
                />
              </div>
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1;   }
          50%       { opacity: 0.3; }
        }
        @media (max-width: 900px) {
          .dashboard-grid {
            grid-template-columns: 1fr !important;
          }
          .left-col-sticky {
            position: static !important;
          }
        }
      `}</style>
    </div>
  );
}
