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
      {/* Logo / back */}
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

      {/* Right: new analysis */}
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
      {/* Animated logo */}
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

      {/* Pipeline tracker */}
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

  // Stagger page reveal on complete
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

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div style={{ minHeight: "100vh" }}>
      <NavBar onBack={handleBack} />

      {/* ── Pipeline still running ─────────────────────────────────────────── */}
      {!isComplete && !isFailed && (
        <LoadingState stages={stages} status={status} />
      )}

      {/* ── Failed ─────────────────────────────────────────────────────────── */}
      {isFailed && (
        <ErrorState error={error ?? "Unknown error"} onBack={handleBack} />
      )}

      {/* ── Complete — full dashboard ───────────────────────────────────────── */}
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

            {/* Spacer */}
            <div style={{ flex: 1 }} />

            {/* Finding count chips */}
            {(["Critical","High","Medium","Low"] as const).map(sev => {
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

          {/* ── Pipeline tracker (completed state) ───────────────────────────── */}
          <div style={{ marginBottom: "32px" }}>
            <PipelineTracker
              stages={stages}
              progress={100}
            />
          </div>

          {/* ── Two-column layout ─────────────────────────────────────────────── */}
          <div style={{
            display:             "grid",
            gridTemplateColumns: "340px 1fr",
            gap:                 "24px",
            alignItems:          "start",
          }}>

            {/* ── LEFT COLUMN ──────────────────────────────────────────────────── */}
            <div style={{
              display:       "flex",
              flexDirection: "column",
              gap:           "24px",
              position:      "sticky",
              top:           "80px",
            }}>

              {/* Score gauge — bleeds slightly */}
              <div style={{
                background:   "var(--bg-surface)",
                border:       "1px solid var(--border-subtle)",
                borderRadius: "12px",
                padding:      "28px 20px 20px",
                display:      "flex",
                flexDirection:"column",
                alignItems:   "center",
                gap:          "24px",
                marginLeft:   "-8px",   // subtle bleed
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

              {/* File heatmap */}
              <FileHeatmap
                findings={allFindings}
                activeFile={activeFile}
                onFileSelect={setActiveFile}
              />

              {/* Export bar */}
              <ExportBar
                jobId={jobId}
                filename={report.filename}
              />
            </div>

            {/* ── RIGHT COLUMN ─────────────────────────────────────────────────── */}
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
        </div>
      )}

      {/* ── Keyframes ─────────────────────────────────────────────────────────── */}
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
