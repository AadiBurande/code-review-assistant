// app/results/[jobId]/page.tsx
"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import ScoreGauge from "@/components/score/ScoreGauge";
import SubScoreRings from "@/components/score/SubScoreRings";
import FindingsPanel from "@/components/findings/FindingsPanel";
import FileHeatmap from "@/components/heatmap/FileHeatmap";
import ExportBar from "@/components/export/ExportBar";
import { AnalysisReport } from "@/lib/useAnalysisStatus";

/* ── tiny skeleton ─────────────────────────────────────── */
function Skeleton({ w, h }: { w: string; h: string }) {
  return (
    <div
      className="animate-pulse rounded bg-[#1a2233]"
      style={{ width: w, height: h }}
    />
  );
}

/* ── plagiarism banner ──────────────────────────────────── */
interface PlagiarismResult {
  score:      number;
  verdict:    string;   // "clean" | "suspicious" | "likely_ai" | "blocked"
  blocked:    boolean;
  summary:    string;
  evidence:   string[];
  remedies:   string[];
  heuristic_score?: number;
  llm_score?:       number;
}

function PlagiarismBanner({ p }: { p: PlagiarismResult }) {
  const [open, setOpen] = useState(true);

  const blocked    = p.blocked;
  const suspicious = !blocked && p.score >= 30;

  /* colours */
  const border = blocked    ? "border-red-500"    : "border-yellow-400";
  const bg     = blocked    ? "bg-red-950/60"     : "bg-yellow-950/40";
  const icon   = blocked    ? "🚫"                : "⚠️";
  const label  = blocked
    ? "REVIEW BLOCKED — AI-Generated / Plagiarised Code Detected"
    : "SUSPICIOUS CODE — Possible AI Generation Detected";
  const labelColor = blocked ? "text-red-400" : "text-yellow-300";
  const scoreColor = blocked ? "text-red-400" : "text-yellow-400";

  if (!open) return null;

  return (
    <div
      className={`rounded-lg border ${border} ${bg} p-4 mb-6 font-mono text-sm`}
      role="alert"
    >
      {/* header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span className={`font-bold uppercase tracking-wide ${labelColor}`}>
            {label}
          </span>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="text-[#8899aa] hover:text-white transition-colors text-lg leading-none"
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>

      {/* score row */}
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-[#8899aa]">
        <span>
          AI Score:{" "}
          <span className={`font-bold text-sm ${scoreColor}`}>
            {p.score.toFixed(1)}
            <span className="text-[#8899aa] font-normal">/100</span>
          </span>
        </span>
        {p.heuristic_score !== undefined && (
          <span>
            Heuristic: <span className="text-white">{p.heuristic_score.toFixed(1)}</span>
          </span>
        )}
        {p.llm_score !== undefined && (
          <span>
            LLM: <span className="text-white">{p.llm_score.toFixed(1)}</span>
          </span>
        )}
        <span>
          Verdict:{" "}
          <span className={`font-bold uppercase ${scoreColor}`}>{p.verdict}</span>
        </span>
      </div>

      {/* summary */}
      {p.summary && (
        <p className="mt-3 text-[#b0bec5] leading-relaxed">{p.summary}</p>
      )}

      {/* evidence + remedies side by side */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* evidence */}
        {p.evidence?.length > 0 && (
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#8899aa] mb-2">
              Why we flagged it
            </p>
            <ul className="space-y-1">
              {p.evidence.map((e, i) => (
                <li key={i} className="flex gap-2 text-[#cdd5e0] text-xs">
                  <span className={blocked ? "text-red-400" : "text-yellow-400"}>
                    •
                  </span>
                  {e}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* remedies */}
        {p.remedies?.length > 0 && (
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#8899aa] mb-2">
              What you should do
            </p>
            <ol className="space-y-1">
              {p.remedies.map((r, i) => (
                <li key={i} className="flex gap-2 text-[#cdd5e0] text-xs">
                  <span className={`font-bold min-w-[16px] ${blocked ? "text-red-400" : "text-yellow-400"}`}>
                    {i + 1}.
                  </span>
                  {r}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* blocked message */}
      {blocked && (
        <div className="mt-4 rounded border border-red-800 bg-red-900/30 px-4 py-2 text-xs text-red-300">
          🔒 The full code review was <strong>not performed</strong> because the
          code appears to be AI-generated or plagiarised. Please submit original
          code to receive a review.
        </div>
      )}
    </div>
  );
}

/* ── language icons ─────────────────────────────────────── */
const LANG_ICON: Record<string, string> = {
  python:     "🐍",
  javascript: "🟨",
  typescript: "🔷",
  java:       "☕",
  default:    "📄",
};

/* ── main results page ──────────────────────────────────── */
export default function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router    = useRouter();

  const [report,      setReport]      = useState<AnalysisReport | null>(null);
  const [plagiarism,  setPlagiarism]  = useState<PlagiarismResult | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const fetchReport = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/report/${jobId}/json`
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        setReport(data as AnalysisReport);

        /* ── pick up plagiarism_result ── */
        if (data.plagiarism_result) {
          setPlagiarism(data.plagiarism_result as PlagiarismResult);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load report");
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [jobId]);

  /* ── loading skeleton ── */
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0d1117] p-6">
        <div className="max-w-[1400px] mx-auto space-y-4">
          <Skeleton w="260px" h="28px" />
          <Skeleton w="100%"  h="120px" />
          <div className="grid grid-cols-3 gap-4">
            <Skeleton w="100%" h="320px" />
            <Skeleton w="100%" h="320px" />
            <Skeleton w="100%" h="320px" />
          </div>
        </div>
      </div>
    );
  }

  /* ── error ── */
  if (error || !report) {
    return (
      <div className="min-h-screen bg-[#0d1117] flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-red-400 font-mono text-sm">
            {error ?? "Report not found"}
          </p>
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 rounded bg-[#1a2233] text-[#00e5cc] text-sm font-mono
                       hover:bg-[#243044] transition-colors"
          >
            ← Back to dashboard
          </button>
        </div>
      </div>
    );
  }

  const langIcon  = LANG_ICON[report.language] ?? LANG_ICON.default;
  const isBlocked = plagiarism?.blocked ?? false;

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#e2e8f0] font-mono">
      <div className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">

        {/* ── breadcrumb header ── */}
        <div className="flex items-center gap-2 text-sm text-[#8899aa]">
          <button
            onClick={() => router.push("/")}
            className="hover:text-[#00e5cc] transition-colors"
          >
            ◆ CodeScan
          </button>
          <span>/</span>
          <span className="text-[#e2e8f0]">{langIcon} {report.filename}</span>
          <span className="text-xs text-[#556677]">
            · {report.language} · {report.total_findings} findings
          </span>
        </div>

        {/* ── PLAGIARISM BANNER (shown first, above everything) ── */}
        {plagiarism && (plagiarism.blocked || plagiarism.score >= 30) && (
          <PlagiarismBanner p={plagiarism} />
        )}

        {/* ── pipeline stages strip ── */}
        <PipelineStrip blocked={isBlocked} />

        {/* ── main 3-col grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr_280px] gap-6">

          {/* left: score + sub-scores */}
          <div className="space-y-4">
            <ScoreGauge score={report.overall_score} verdict={report.verdict} />
            <SubScoreRings scores={report.sub_scores} />
          </div>

          {/* center: findings (greyed out if blocked) */}
          <div className={isBlocked ? "opacity-40 pointer-events-none select-none" : ""}>
            {isBlocked ? (
              <BlockedFindingsPlaceholder />
            ) : (
              <FindingsPanel findings={report.findings} />
            )}
          </div>

          {/* right: heatmap + export */}
          <div className="space-y-4">
            <FileHeatmap findings={report.findings} activeFile={null} onFileSelect={() => {}} />
            <ExportBar jobId={jobId} filename={report.filename} />
          </div>
        </div>

      </div>
    </div>
  );
}

/* ── pipeline strip ─────────────────────────────────────── */
const STAGES = [
  { key: "ingestion",    label: "Ingestion",         icon: "↑" },
  { key: "static",       label: "Static Analysis",   icon: "⚙" },
  { key: "bug",          label: "Bug Agent",         icon: "🐛" },
  { key: "security",     label: "Security Agent",    icon: "🔒" },
  { key: "performance",  label: "Performance Agent", icon: "⚡" },
  { key: "style",        label: "Style Agent",       icon: "✦" },
  { key: "aggregation",  label: "Aggregation",       icon: "◈" },
];

function PipelineStrip({ blocked }: { blocked: boolean }) {
  return (
    <div className="rounded-lg border border-[#1e2d3d] bg-[#0f1923] p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold uppercase tracking-widest text-[#8899aa]">
          Pipeline
        </span>
        {blocked ? (
          <span className="text-xs text-red-400 font-bold">
            🚫 Blocked — plagiarism detected
          </span>
        ) : (
          <span className="text-xs text-[#00e5cc]">✓ Complete</span>
        )}
      </div>
      <div className="flex items-center gap-1 flex-wrap">
        {STAGES.map((s, i) => {
          /* if blocked, only ingestion is done, rest are skipped */
          const done    = !blocked || s.key === "ingestion";
          const skipped = blocked && s.key !== "ingestion";
          return (
            <div key={s.key} className="flex items-center gap-1">
              <div
                className={`rounded border px-3 py-2 text-center min-w-[90px]
                  ${skipped
                    ? "border-[#2a1a1a] bg-[#1a1010] text-[#553333]"
                    : done
                    ? "border-[#0e3a2e] bg-[#0a2820] text-[#e2e8f0]"
                    : "border-[#1e2d3d] bg-[#0f1923] text-[#8899aa]"
                  }`}
              >
                <div className="text-base leading-none">{s.icon}</div>
                <div className="text-[10px] font-bold mt-1 uppercase tracking-wide">
                  {s.label}
                </div>
                <div
                  className={`text-[9px] mt-1 font-bold uppercase ${
                    skipped ? "text-[#553333]" : done ? "text-[#00e5cc]" : "text-[#556677]"
                  }`}
                >
                  {skipped ? "skipped" : done ? "done" : "pending"}
                </div>
              </div>
              {i < STAGES.length - 1 && (
                <span className="text-[#1e2d3d] text-xs">—</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── blocked findings placeholder ───────────────────────── */
function BlockedFindingsPlaceholder() {
  return (
    <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-8 text-center space-y-3 h-full flex flex-col items-center justify-center">
      <span className="text-4xl">🚫</span>
      <p className="text-red-400 font-bold text-sm uppercase tracking-wide">
        Review Not Performed
      </p>
      <p className="text-[#8899aa] text-xs max-w-[280px] leading-relaxed">
        Code review findings are hidden because this submission was flagged as
        AI-generated or plagiarised. Submit original code to see the full analysis.
      </p>
    </div>
  );
}
