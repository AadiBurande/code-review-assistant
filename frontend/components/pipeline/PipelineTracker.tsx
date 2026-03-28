// components/pipeline/PipelineTracker.tsx
"use client";

import { useEffect, useState } from "react";
import { StageState, StageStatus } from "@/lib/useAnalysisStatus";

// ── Types ─────────────────────────────────────────────────────────────────────

interface PipelineTrackerProps {
  stages: StageState[];
  currentMessage?: string;
  progress?: number;
}

// ── Stage Icons ───────────────────────────────────────────────────────────────

const STAGE_ICONS: Record<string, string> = {
  ingestion:         "⬆",
  static_analysis:   "⚙",
  bug_agent:         "🐛",
  security_agent:    "🔒",
  performance_agent: "⚡",
  style_agent:       "✦",
  aggregation:       "◈",
};

// ── Status Colors ─────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<StageStatus, string> = {
  idle:     "var(--text-muted)",
  running:  "var(--accent)",
  complete: "#00FF87",
  failed:   "var(--sev-critical)",
};

const STATUS_BG: Record<StageStatus, string> = {
  idle:     "var(--bg-elevated)",
  running:  "rgba(0, 212, 255, 0.10)",
  complete: "rgba(0, 255, 135, 0.08)",
  failed:   "var(--sev-critical-bg)",
};

const STATUS_BORDER: Record<StageStatus, string> = {
  idle:     "var(--border-subtle)",
  running:  "var(--accent-border)",
  complete: "rgba(0, 255, 135, 0.30)",
  failed:   "var(--sev-critical)",
};

const STATUS_LABEL: Record<StageStatus, string> = {
  idle:     "Waiting",
  running:  "Running",
  complete: "Done",
  failed:   "Failed",
};

// ── Single Stage Node ─────────────────────────────────────────────────────────

function StageNode({ stage, index }: { stage: StageState; index: number }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), index * 80);
    return () => clearTimeout(t);
  }, [index]);

  const isRunning  = stage.status === "running";
  const isComplete = stage.status === "complete";

  return (
    <div
      style={{
        opacity:   visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(8px)",
        transition: "opacity 0.3s ease, transform 0.3s ease",
        flex: 1,
        minWidth: "100px",
        maxWidth: "160px",
      }}
    >
      {/* Node box */}
      <div
        style={{
          background:   STATUS_BG[stage.status],
          border:       `1px solid ${STATUS_BORDER[stage.status]}`,
          borderRadius: "8px",
          padding:      "12px 10px",
          textAlign:    "center",
          position:     "relative",
          overflow:     "hidden",
          transition:   "all 0.3s ease",
          boxShadow:    isRunning
            ? `0 0 16px rgba(0,212,255,0.20)`
            : isComplete
            ? `0 0 10px rgba(0,255,135,0.10)`
            : "none",
        }}
      >
        {/* Running shimmer sweep */}
        {isRunning && (
          <div
            aria-hidden="true"
            style={{
              position:   "absolute",
              inset:      0,
              background: "linear-gradient(90deg, transparent 0%, rgba(0,212,255,0.06) 50%, transparent 100%)",
              animation:  "shimmerSweep 1.4s ease-in-out infinite",
            }}
          />
        )}

        {/* Icon */}
        <div style={{
          fontSize:     "18px",
          marginBottom: "6px",
          filter:       isRunning
            ? "drop-shadow(0 0 6px rgba(0,212,255,0.6))"
            : "none",
          transition:   "filter 0.3s ease",
        }}>
          {STAGE_ICONS[stage.name] ?? "◉"}
        </div>

        {/* Label */}
        <div style={{
          fontFamily:    "var(--font-mono)",
          fontSize:      "10px",
          fontWeight:    600,
          color:         STATUS_COLOR[stage.status],
          letterSpacing: "0.04em",
          marginBottom:  "6px",
          whiteSpace:    "nowrap",
          overflow:      "hidden",
          textOverflow:  "ellipsis",
          transition:    "color 0.3s ease",
        }}>
          {stage.label}
        </div>

        {/* Status pill */}
        <div style={{
          display:       "inline-flex",
          alignItems:    "center",
          gap:           "4px",
          fontSize:      "9px",
          fontFamily:    "var(--font-mono)",
          color:         STATUS_COLOR[stage.status],
          letterSpacing: "0.06em",
          textTransform: "uppercase",
        }}>
          {/* Dot indicator */}
          <span style={{
            width:        "5px",
            height:       "5px",
            borderRadius: "50%",
            background:   STATUS_COLOR[stage.status],
            display:      "inline-block",
            animation:    isRunning ? "pulseDot 1s ease infinite" : "none",
            flexShrink:   0,
          }} />
          {STATUS_LABEL[stage.status]}
        </div>
      </div>
    </div>
  );
}

// ── Connector Line ────────────────────────────────────────────────────────────

function Connector({ active }: { active: boolean }) {
  return (
    <div style={{
      flexShrink: 0,
      width:      "24px",
      height:     "1px",
      position:   "relative",
      alignSelf:  "center",
      marginTop:  "-20px", // align with node center
    }}>
      <div style={{
        position:   "absolute",
        inset:      0,
        background: active
          ? "linear-gradient(90deg, rgba(0,255,135,0.6), var(--accent))"
          : "var(--border-subtle)",
        transition: "background 0.4s ease",
      }} />
      {active && (
        <div style={{
          position:   "absolute",
          inset:      0,
          background: "linear-gradient(90deg, transparent 0%, rgba(0,212,255,0.8) 50%, transparent 100%)",
          backgroundSize: "200% 100%",
          animation:  "flowLine 1s linear infinite",
        }} />
      )}
    </div>
  );
}

// ── Progress Bar ──────────────────────────────────────────────────────────────

function ProgressBar({ progress }: { progress: number }) {
  return (
    <div style={{
      width:        "100%",
      height:       "2px",
      background:   "var(--border-subtle)",
      borderRadius: "1px",
      overflow:     "hidden",
      marginTop:    "20px",
    }}>
      <div style={{
        height:     "100%",
        width:      `${progress}%`,
        background: `linear-gradient(90deg, var(--accent), #00FF87)`,
        borderRadius: "1px",
        transition: "width 0.5s ease",
        boxShadow:  "0 0 8px rgba(0,212,255,0.5)",
        position:   "relative",
      }}>
        {/* Leading glow tip */}
        <div style={{
          position:   "absolute",
          right:      0,
          top:        "-2px",
          width:      "6px",
          height:     "6px",
          borderRadius: "50%",
          background: "var(--accent)",
          boxShadow:  "0 0 8px var(--accent)",
        }} />
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function PipelineTracker({
  stages,
  currentMessage,
  progress = 0,
}: PipelineTrackerProps) {
  const completedCount = stages.filter(s => s.status === "complete").length;
  const hasFailure     = stages.some(s => s.status === "failed");
  const allComplete    = completedCount === stages.length;

  return (
    <div style={{
      background:   "var(--bg-surface)",
      border:       "1px solid var(--border-subtle)",
      borderRadius: "12px",
      padding:      "24px",
    }}>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div style={{
        display:       "flex",
        alignItems:    "center",
        justifyContent:"space-between",
        marginBottom:  "20px",
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
            Pipeline
          </span>
          <div style={{
            height:     "1px",
            width:      "40px",
            background: "var(--border-subtle)",
          }} />
        </div>

        {/* Stage counter */}
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize:   "11px",
          color:      hasFailure
            ? "var(--sev-critical)"
            : allComplete
            ? "#00FF87"
            : "var(--text-muted)",
        }}>
          {hasFailure
            ? "⚠ Failed"
            : allComplete
            ? "✓ Complete"
            : `${completedCount} / ${stages.length}`}
        </span>
      </div>

      {/* ── Stage nodes + connectors ─────────────────────────────────────────── */}
      <div style={{
        display:    "flex",
        alignItems: "flex-start",
        gap:        "0",
        overflowX:  "auto",
        paddingBottom: "4px",
      }}>
        {stages.map((stage, i) => (
          <div key={stage.name} style={{ display: "flex", alignItems: "center", flex: i < stages.length - 1 ? "1" : "0" }}>
            <StageNode stage={stage} index={i} />
            {i < stages.length - 1 && (
              <Connector active={stage.status === "complete"} />
            )}
          </div>
        ))}
      </div>

      {/* ── Progress bar ─────────────────────────────────────────────────────── */}
      <ProgressBar progress={allComplete ? 100 : progress} />

      {/* ── Status message ───────────────────────────────────────────────────── */}
      {currentMessage && (
        <p style={{
          marginTop:  "12px",
          fontFamily: "var(--font-mono)",
          fontSize:   "11px",
          color:      "var(--text-muted)",
          letterSpacing: "0.02em",
        }}>
          › {currentMessage}
        </p>
      )}

      {/* ── Keyframes ─────────────────────────────────────────────────────────── */}
      <style>{`
        @keyframes shimmerSweep {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        @keyframes pulseDot {
          0%, 100% { opacity: 1;   transform: scale(1);   }
          50%       { opacity: 0.4; transform: scale(0.7); }
        }
        @keyframes flowLine {
          0%   { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}
