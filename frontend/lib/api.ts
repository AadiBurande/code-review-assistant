// lib/api.ts

// ── Types ─────────────────────────────────────────────────────────────────────

export interface UploadResponse {
  job_id: string;
  session_id: string;
  filename: string;
  language: string;
  status: string;
  message: string;
}

export type DownloadFormat = "json" | "markdown" | "sarif";

// ── Base ──────────────────────────────────────────────────────────────────────

const BASE = "/api/backend";

// ── Upload & Trigger Analysis ─────────────────────────────────────────────────

export async function uploadAndAnalyze(
  file: File,
  language?: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (language) formData.append("language", language);

  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || `Upload failed: ${res.status}`);
  }

  const data = await res.json();
  return { ...data, job_id: data.job_id ?? data.session_id };
}

// ── Fetch Status ──────────────────────────────────────────────────────────────

export async function fetchStatus(jobId: string) {
  const res = await fetch(`${BASE}/status/${jobId}`);
  if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`);
  return res.json();
}

// ── Fetch Report ──────────────────────────────────────────────────────────────

export async function fetchReport(jobId: string) {
  const res = await fetch(`${BASE}/report/${jobId}/json`);
  if (!res.ok) throw new Error(`Report fetch failed: ${res.status}`);
  return res.json();
}

// ── Download Report ───────────────────────────────────────────────────────────

export function downloadReport(jobId: string, format: "json" | "markdown" | "sarif") {
  const formatMap = {
    json:     "json",
    markdown: "markdown",
    sarif:    "sarif",
  };
  const url = `${BASE}/report/${jobId}/${formatMap[format]}`;
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `report-${jobId}.${format === "markdown" ? "md" : format}`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
}

// ── Detect Language from File Extension ───────────────────────────────────────

export function detectLanguage(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = {
    py:   "python",
    java: "java",
    js:   "javascript",
    jsx:  "javascript",
    ts:   "javascript",
    tsx:  "javascript",
  };
  return map[ext ?? ""] ?? "unknown";
}

// ── Accepted File Types ───────────────────────────────────────────────────────

export const ACCEPTED_EXTENSIONS = [".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".zip"];

export const ACCEPTED_MIME_TYPES: Record<string, string[]> = {
  "text/x-python":       [".py"],
  "text/x-java-source":  [".java"],
  "application/javascript": [".js", ".jsx"],
  "application/typescript": [".ts", ".tsx"],
  "application/zip":     [".zip"],
  "application/x-zip-compressed": [".zip"],
};

// ── Language Icons (emoji fallback — swap with SVG icons later) ───────────────

export const LANGUAGE_META: Record<string, { label: string; color: string; icon: string }> = {
  python:     { label: "Python",     color: "#3B82F6", icon: "🐍" },
  java:       { label: "Java",       color: "#F97316", icon: "☕" },
  javascript: { label: "JavaScript", color: "#EAB308", icon: "⚡" },
  unknown:    { label: "Unknown",    color: "#6B7280", icon: "📄" },
};
