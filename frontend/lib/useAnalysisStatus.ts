// lib/useAnalysisStatus.ts
import { useState, useEffect, useRef, useCallback } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

export type PipelineStage =
  | "idle" | "pending" | "running"
  | "ingestion" | "static_analysis"
  | "bug_agent" | "security_agent" | "performance_agent" | "style_agent"
  | "aggregation" | "complete" | "done" | "failed";

export type StageStatus = "idle" | "running" | "complete" | "failed";

export interface StageState {
  name:   string;
  label:  string;
  status: StageStatus;
}

export interface Finding {
  id?:             string;
  file_path:       string;
  start_line:      number;
  end_line:        number;
  issue_type:      "bug" | "security" | "performance" | "style";
  severity:        "Critical" | "High" | "Medium" | "Low" | "Info";
  confidence:      number;
  description:     string;
  remediation:     string;
  code_suggestion: string;
  tags:            string[];
  references:      string[];
}

export interface SubScores {
  bug:         number;
  security:    number;
  performance: number;
  style:       number;
}

export interface AnalysisReport {
  job_id:          string;
  filename:        string;
  language:        string;
  overall_score:   number;
  sub_scores:      SubScores;
  verdict:         "accept" | "needs_changes" | "reject";
  total_findings:  number;
  findings:        Finding[];
  static_findings: Finding[];
}

export interface AnalysisStatus {
  job_id:         string;
  status:         PipelineStage;
  stage:          string;
  progress:       number;
  message:        string;
  findings_count: number;
}

// ── Stage Definitions ─────────────────────────────────────────────────────────

export const PIPELINE_STAGES: StageState[] = [
  { name: "ingestion",         label: "Ingestion",         status: "idle" },
  { name: "static_analysis",   label: "Static Analysis",   status: "idle" },
  { name: "bug_agent",         label: "Bug Agent",         status: "idle" },
  { name: "security_agent",    label: "Security Agent",    status: "idle" },
  { name: "performance_agent", label: "Performance Agent", status: "idle" },
  { name: "style_agent",       label: "Style Agent",       status: "idle" },
  { name: "aggregation",       label: "Aggregation",       status: "idle" },
];

const STAGE_INDEX: Record<string, number> = {
  ingestion:         0,
  static_analysis:   1,
  bug_agent:         2,
  security_agent:    3,
  performance_agent: 4,
  style_agent:       5,
  aggregation:       6,
};

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAnalysisStatus(jobId: string | null) {
  const [status,     setStatus]     = useState<AnalysisStatus | null>(null);
  const [stages,     setStages]     = useState<StageState[]>(PIPELINE_STAGES);
  const [report,     setReport]     = useState<AnalysisReport | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [isFailed,   setIsFailed]   = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  const intervalRef      = useRef<NodeJS.Timeout | null>(null);
  const isFetchingReport = useRef(false);

  // ── Fetch final report ─────────────────────────────────────────────────────
  const fetchReport = useCallback(async (id: string) => {
    if (isFetchingReport.current) return;
    isFetchingReport.current = true;
    try {
      const res = await fetch(`/api/backend/report/${id}/json`);
      if (!res.ok) throw new Error(`Report fetch failed: ${res.status}`);
      const raw = await res.json();

      // ✅ Backend returns flat shape — read directly
      const normalized: AnalysisReport = {
        job_id:         raw.job_id          ?? id,
        filename:       raw.filename        ?? "unknown",
        language:       raw.language        ?? "python",
        overall_score:  raw.overall_score   ?? 0,
        sub_scores: {
          bug:         raw.sub_scores?.bug         ?? 100,
          security:    raw.sub_scores?.security    ?? 100,
          performance: raw.sub_scores?.performance ?? 100,
          style:       raw.sub_scores?.style       ?? 100,
        },
        verdict:        raw.verdict         ?? "needs_changes",
        total_findings: raw.total_findings  ?? 0,
        findings:       raw.findings        ?? [],
        static_findings: raw.static_findings ?? [],
      };

      setReport(normalized);
      setIsComplete(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch report");
      setIsFailed(true);
    } finally {
      isFetchingReport.current = false;
    }
  }, []);

  // ── Update stage states ────────────────────────────────────────────────────
  const updateStages = useCallback((currentStage: string, jobStatus: PipelineStage) => {
    const currentIdx = STAGE_INDEX[currentStage] ?? -1;
    setStages(prev =>
      prev.map((s, i) => {
        if (jobStatus === "complete") return { ...s, status: "complete" };
        if (jobStatus === "failed") {
          if (i < currentIdx)   return { ...s, status: "complete" };
          if (i === currentIdx) return { ...s, status: "failed" };
          return { ...s, status: "idle" };
        }
        if (i < currentIdx)   return { ...s, status: "complete" };
        if (i === currentIdx) return { ...s, status: "running" };
        return { ...s, status: "idle" };
      })
    );
  }, []);

  // ── Polling loop ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!jobId) return;

    setStatus(null);
    setStages(PIPELINE_STAGES);
    setReport(null);
    setIsComplete(false);
    setIsFailed(false);
    setError(null);
    isFetchingReport.current = false;

    const poll = async () => {
      try {
        const res = await fetch(`/api/backend/status/${jobId}`);
        if (!res.ok) throw new Error(`Status ${res.status}`);
        const data: AnalysisStatus = await res.json();

        setStatus(data);
        updateStages(data.stage, data.status);

        if (data.status === "complete" || data.status === "done") {
          clearInterval(intervalRef.current!);
          await fetchReport(jobId);
        } else if (data.status === "failed") {
          clearInterval(intervalRef.current!);
          setIsFailed(true);
          setError(data.message || "Pipeline failed");
        }
      } catch (err) {
        console.warn("[useAnalysisStatus] Poll error:", err);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [jobId, fetchReport, updateStages]);

  return { status, stages, report, isComplete, isFailed, error };
}