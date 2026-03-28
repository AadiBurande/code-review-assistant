// components/upload/DropZone.tsx
"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "next/navigation";
import { uploadAndAnalyze, detectLanguage, ACCEPTED_MIME_TYPES, LANGUAGE_META } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface DropZoneProps {
  onJobStart?: (jobId: string) => void;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function DropZone({ onJobStart }: DropZoneProps) {
  const router = useRouter();
  const [file, setFile]         = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[], rejected: any[]) => {
    setError(null);
    if (rejected.length > 0) {
      setError("Unsupported file type. Please upload .py, .java, .js, .ts, or .zip");
      return;
    }
    if (accepted.length > 0) {
      setFile(accepted[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_MIME_TYPES,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleAnalyze = async () => {
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const lang = detectLanguage(file.name);
      const res  = await uploadAndAnalyze(file, lang === "unknown" ? undefined : lang);
      if (onJobStart) onJobStart(res.job_id);
      router.push(`/dashboard/${res.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
      setUploading(false);
    }
  };

  const detectedLang = file ? detectLanguage(file.name) : null;
  const langMeta     = detectedLang ? LANGUAGE_META[detectedLang] : null;

  // ── Border color based on state ──────────────────────────────────────────
  const borderColor = isDragReject
    ? "var(--sev-critical)"
    : isDragActive
    ? "var(--accent)"
    : file
    ? "var(--accent-border)"
    : "var(--border-default)";

  const bgColor = isDragActive
    ? "rgba(0, 212, 255, 0.04)"
    : "var(--bg-surface)";

  return (
    <div style={{ width: "100%", maxWidth: "640px", margin: "0 auto" }}>

      {/* ── Drop Area ─────────────────────────────────────────────────────── */}
      <div
        {...getRootProps()}
        style={{
          border: `1px dashed ${borderColor}`,
          borderRadius: "12px",
          background: bgColor,
          padding: "48px 32px",
          textAlign: "center",
          cursor: "pointer",
          transition: "all 0.2s ease",
          position: "relative",
          overflow: "hidden",
          boxShadow: isDragActive ? `0 0 30px rgba(0,212,255,0.12)` : "none",
        }}
      >
        <input {...getInputProps()} />

        {/* Animated corner accents */}
        {["top-left", "top-right", "bottom-left", "bottom-right"].map((pos) => (
          <div
            key={pos}
            aria-hidden="true"
            style={{
              position: "absolute",
              width: "12px",
              height: "12px",
              borderColor: "var(--accent)",
              borderStyle: "solid",
              opacity: isDragActive ? 0.8 : 0.3,
              transition: "opacity 0.2s",
              ...(pos === "top-left"     && { top: 12, left: 12, borderWidth: "1px 0 0 1px" }),
              ...(pos === "top-right"    && { top: 12, right: 12, borderWidth: "1px 1px 0 0" }),
              ...(pos === "bottom-left"  && { bottom: 12, left: 12, borderWidth: "0 0 1px 1px" }),
              ...(pos === "bottom-right" && { bottom: 12, right: 12, borderWidth: "0 1px 1px 0" }),
            }}
          />
        ))}

        {/* Icon */}
        <div style={{ marginBottom: "16px" }}>
          {file ? (
            <div style={{ fontSize: "40px" }}>{langMeta?.icon ?? "📄"}</div>
          ) : (
            <svg
              width="40" height="40" viewBox="0 0 24 24"
              fill="none" stroke="var(--accent)" strokeWidth="1.2"
              strokeLinecap="round" strokeLinejoin="round"
              style={{ margin: "0 auto", opacity: isDragActive ? 1 : 0.5 }}
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          )}
        </div>

        {/* Text */}
        {file ? (
          <div>
            <p style={{
              fontFamily: "var(--font-mono)",
              fontSize: "14px",
              color: "var(--text-primary)",
              marginBottom: "4px",
            }}>
              {file.name}
            </p>
            <p style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
              {formatBytes(file.size)}
              {langMeta && (
                <span style={{
                  marginLeft: "8px",
                  color: langMeta.color,
                  fontFamily: "var(--font-mono)",
                }}>
                  · {langMeta.label}
                </span>
              )}
            </p>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              style={{
                marginTop: "12px",
                fontSize: "11px",
                color: "var(--text-muted)",
                background: "none",
                border: "none",
                cursor: "pointer",
                textDecoration: "underline",
              }}
            >
              Remove
            </button>
          </div>
        ) : (
          <div>
            <p style={{
              fontFamily: "var(--font-mono)",
              fontSize: "14px",
              color: isDragActive ? "var(--accent)" : "var(--text-primary)",
              marginBottom: "8px",
              transition: "color 0.2s",
            }}>
              {isDragActive ? "Drop to analyze" : "Drag & drop your file here"}
            </p>
            <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              or click to browse
            </p>
          </div>
        )}
      </div>

      {/* ── Supported Languages ──────────────────────────────────────────────── */}
      <div style={{
        display: "flex",
        justifyContent: "center",
        gap: "16px",
        marginTop: "16px",
        flexWrap: "wrap",
      }}>
        {Object.entries(LANGUAGE_META).filter(([k]) => k !== "unknown").map(([key, meta]) => (
          <div
            key={key}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "11px",
              color: detectedLang === key ? meta.color : "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              transition: "color 0.2s",
            }}
          >
            <span>{meta.icon}</span>
            <span>{meta.label}</span>
          </div>
        ))}
        <div style={{
          fontSize: "11px",
          color: "var(--text-muted)",
          fontFamily: "var(--font-mono)",
        }}>
          📦 .zip
        </div>
      </div>

      {/* ── Error ────────────────────────────────────────────────────────────── */}
      {error && (
        <div style={{
          marginTop: "16px",
          padding: "10px 14px",
          background: "var(--sev-critical-bg)",
          border: "1px solid var(--sev-critical)",
          borderRadius: "6px",
          fontSize: "12px",
          color: "var(--sev-critical)",
          fontFamily: "var(--font-mono)",
        }}>
          ⚠ {error}
        </div>
      )}

      {/* ── CTA Button ───────────────────────────────────────────────────────── */}
      <button
        onClick={handleAnalyze}
        disabled={!file || uploading}
        style={{
          marginTop: "24px",
          width: "100%",
          padding: "14px 24px",
          background: file && !uploading
            ? "var(--accent)"
            : "var(--bg-elevated)",
          color: file && !uploading
            ? "var(--bg-base)"
            : "var(--text-muted)",
          border: "1px solid",
          borderColor: file && !uploading
            ? "var(--accent)"
            : "var(--border-default)",
          borderRadius: "8px",
          fontFamily: "var(--font-mono)",
          fontSize: "13px",
          fontWeight: 600,
          letterSpacing: "0.05em",
          cursor: file && !uploading ? "pointer" : "not-allowed",
          transition: "all 0.2s ease",
          boxShadow: file && !uploading
            ? "0 0 20px rgba(0,212,255,0.25)"
            : "none",
        }}
        onMouseEnter={(e) => {
          if (file && !uploading) {
            (e.target as HTMLButtonElement).style.boxShadow =
              "0 0 32px rgba(0,212,255,0.45)";
          }
        }}
        onMouseLeave={(e) => {
          if (file && !uploading) {
            (e.target as HTMLButtonElement).style.boxShadow =
              "0 0 20px rgba(0,212,255,0.25)";
          }
        }}
      >
        {uploading ? (
          <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
            <span style={{
              width: "12px", height: "12px",
              border: "2px solid var(--bg-base)",
              borderTopColor: "transparent",
              borderRadius: "50%",
              display: "inline-block",
              animation: "spin 0.7s linear infinite",
            }} />
            Uploading...
          </span>
        ) : (
          "⚡ Run Analysis"
        )}
      </button>

      {/* Spinner keyframe */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
