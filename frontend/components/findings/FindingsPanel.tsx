// components/findings/FindingsPanel.tsx
"use client";

import { useState, useMemo } from "react";
import { Finding } from "@/lib/useAnalysisStatus";
import FindingCard from "./FindingCard";

// ── Types ─────────────────────────────────────────────────────────────────────

interface FindingsPanelProps {
  findings:      Finding[];
  activeFile?:   string | null;
  onFileClick?:  (file: string) => void;
}

type SeverityFilter = "All" | "Critical" | "High" | "Medium" | "Low" | "Info";
type TypeFilter     = "All" | "bug" | "security" | "performance" | "style";
type SortKey        = "severity" | "line" | "type" | "confidence";

// ── Constants ─────────────────────────────────────────────────────────────────

const SEVERITY_ORDER: Record<string, number> = {
  Critical: 0, High: 1, Medium: 2, Low: 3, Info: 4,
};

const SEVERITY_FILTERS: SeverityFilter[] = [
  "All", "Critical", "High", "Medium", "Low", "Info",
];

const TYPE_FILTERS: { key: TypeFilter; icon: string; label: string }[] = [
  { key: "All",         icon: "◈",  label: "All Types"   },
  { key: "bug",         icon: "🐛", label: "Bug"         },
  { key: "security",    icon: "🔒", label: "Security"    },
  { key: "performance", icon: "⚡", label: "Performance" },
  { key: "style",       icon: "✦",  label: "Style"       },
];

const SEVERITY_COLORS: Record<string, string> = {
  Critical: "var(--sev-critical)",
  High:     "var(--sev-high)",
  Medium:   "var(--sev-medium)",
  Low:      "var(--sev-low)",
  Info:     "var(--sev-info)",
};

// ── Filter Pill ───────────────────────────────────────────────────────────────

function FilterPill({
  label,
  active,
  color,
  count,
  onClick,
}: {
  label:   string;
  active:  boolean;
  color?:  string;
  count?:  number;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display:       "inline-flex",
        alignItems:    "center",
        gap:           "5px",
        padding:       "4px 10px",
        borderRadius:  "100px",
        border:        `1px solid ${active ? (color ?? "var(--accent)") : "var(--border-subtle)"}`,
        background:    active
          ? color
            ? `${color}18`
            : "var(--accent-dim)"
          : "transparent",
        color:         active
          ? (color ?? "var(--accent)")
          : "var(--text-muted)",
        fontFamily:    "var(--font-mono)",
        fontSize:      "10px",
        fontWeight:    active ? 600 : 400,
        cursor:        "pointer",
        transition:    "all 0.15s ease",
        whiteSpace:    "nowrap",
        letterSpacing: "0.04em",
      }}
    >
      {label}
      {count !== undefined && (
        <span style={{
          background:   active ? (color ?? "var(--accent)") : "var(--bg-elevated)",
          color:        active ? "var(--bg-base)" : "var(--text-muted)",
          borderRadius: "100px",
          padding:      "0 5px",
          fontSize:     "9px",
          fontWeight:   700,
          minWidth:     "16px",
          textAlign:    "center",
        }}>
          {count}
        </span>
      )}
    </button>
  );
}

// ── Sort Button ───────────────────────────────────────────────────────────────

function SortButton({
  label,
  active,
  onClick,
}: {
  label:   string;
  active:  boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding:       "4px 10px",
        background:    active ? "var(--bg-elevated)" : "transparent",
        border:        `1px solid ${active ? "var(--border-default)" : "transparent"}`,
        borderRadius:  "4px",
        fontFamily:    "var(--font-mono)",
        fontSize:      "10px",
        color:         active ? "var(--text-primary)" : "var(--text-muted)",
        cursor:        "pointer",
        transition:    "all 0.15s ease",
        letterSpacing: "0.04em",
      }}
    >
      {active ? "↓ " : ""}{label}
    </button>
  );
}

// ── Skeleton Loading Cards ────────────────────────────────────────────────────

function SkeletonCard({ index }: { index: number }) {
  return (
    <div style={{
      background:   "var(--bg-surface)",
      border:       "1px solid var(--border-subtle)",
      borderRadius: "8px",
      padding:      "16px",
      opacity:      1 - index * 0.15,
    }}>
      <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
        <div className="skeleton" style={{ width: "60px",  height: "18px", borderRadius: "4px" }} />
        <div className="skeleton" style={{ width: "80px",  height: "18px", borderRadius: "100px" }} />
        <div className="skeleton" style={{ width: "100px", height: "18px", marginLeft: "auto", borderRadius: "4px" }} />
      </div>
      <div className="skeleton" style={{ width: "100%", height: "14px", borderRadius: "4px", marginBottom: "6px" }} />
      <div className="skeleton" style={{ width: "70%",  height: "14px", borderRadius: "4px" }} />
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function FindingsPanel({
  findings,
  activeFile,
  onFileClick,
}: FindingsPanelProps) {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("All");
  const [typeFilter,     setTypeFilter]     = useState<TypeFilter>("All");
  const [sortKey,        setSortKey]        = useState<SortKey>("severity");
  const [search,         setSearch]         = useState("");
  const [page,           setPage]           = useState(1);
  const PAGE_SIZE = 10;

  // ── Count per severity ───────────────────────────────────────────────────
  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    findings.forEach(f => {
      counts[f.severity] = (counts[f.severity] ?? 0) + 1;
    });
    return counts;
  }, [findings]);

  // ── Filtered + sorted findings ───────────────────────────────────────────
  const filtered = useMemo(() => {
    let result = [...findings];

    if (activeFile)
      result = result.filter(f => f.file_path === activeFile);

    if (severityFilter !== "All")
      result = result.filter(f => f.severity === severityFilter);

    if (typeFilter !== "All")
      result = result.filter(f => f.issue_type === typeFilter);

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(f =>
        f.description.toLowerCase().includes(q) ||
        f.file_path.toLowerCase().includes(q)   ||
        f.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    result.sort((a, b) => {
      if (sortKey === "severity")
        return (SEVERITY_ORDER[a.severity] ?? 5) - (SEVERITY_ORDER[b.severity] ?? 5);
      if (sortKey === "line")
        return a.start_line - b.start_line;
      if (sortKey === "confidence")
        return b.confidence - a.confidence;
      if (sortKey === "type")
        return a.issue_type.localeCompare(b.issue_type);
      return 0;
    });

    return result;
  }, [findings, activeFile, severityFilter, typeFilter, search, sortKey]);

  const totalPages  = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated   = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleFilter = (setter: () => void) => {
    setter();
    setPage(1);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div style={{
        display:        "flex",
        alignItems:     "center",
        justifyContent: "space-between",
        flexWrap:       "wrap",
        gap:            "10px",
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
            Findings
          </span>
          <span style={{
            fontFamily:   "var(--font-mono)",
            fontSize:     "11px",
            color:        "var(--accent)",
            background:   "var(--accent-dim)",
            border:       "1px solid var(--accent-border)",
            borderRadius: "100px",
            padding:      "1px 8px",
          }}>
            {filtered.length} / {findings.length}
          </span>
          {activeFile && (
            <span style={{
              fontFamily:   "var(--font-mono)",
              fontSize:     "10px",
              color:        "var(--text-muted)",
              background:   "var(--bg-elevated)",
              border:       "1px solid var(--border-subtle)",
              borderRadius: "4px",
              padding:      "2px 8px",
              display:      "flex",
              alignItems:   "center",
              gap:          "6px",
            }}>
              {activeFile.split(/[\\/]/).pop()}
              <button
                onClick={() => onFileClick?.(activeFile)}
                style={{
                  background: "none",
                  border:     "none",
                  color:      "var(--text-muted)",
                  cursor:     "pointer",
                  fontSize:   "10px",
                  padding:    0,
                }}
              >
                ✕
              </button>
            </span>
          )}
        </div>

        {/* Sort controls */}
        <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
          <span style={{
            fontFamily: "var(--font-mono)",
            fontSize:   "10px",
            color:      "var(--text-muted)",
            marginRight: "4px",
          }}>
            Sort:
          </span>
          {(["severity", "line", "type", "confidence"] as SortKey[]).map(k => (
            <SortButton
              key={k}
              label={k.charAt(0).toUpperCase() + k.slice(1)}
              active={sortKey === k}
              onClick={() => setSortKey(k)}
            />
          ))}
        </div>
      </div>

      {/* ── Search ──────────────────────────────────────────────────────────── */}
      <div style={{ position: "relative" }}>
        <span style={{
          position:  "absolute",
          left:      "12px",
          top:       "50%",
          transform: "translateY(-50%)",
          fontSize:  "13px",
          color:     "var(--text-muted)",
          pointerEvents: "none",
        }}>
          ⌕
        </span>
        <input
          type="text"
          placeholder="Search findings, files, tags..."
          value={search}
          onChange={e => handleFilter(() => setSearch(e.target.value))}
          style={{
            width:        "100%",
            padding:      "9px 12px 9px 32px",
            background:   "var(--bg-surface)",
            border:       "1px solid var(--border-subtle)",
            borderRadius: "6px",
            color:        "var(--text-primary)",
            fontFamily:   "var(--font-mono)",
            fontSize:     "12px",
            outline:      "none",
            transition:   "border-color 0.2s",
          }}
          onFocus={e  => (e.target.style.borderColor = "var(--accent-border)")}
          onBlur={e   => (e.target.style.borderColor = "var(--border-subtle)")}
        />
      </div>

      {/* ── Severity filters ─────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        {SEVERITY_FILTERS.map(sev => (
          <FilterPill
            key={sev}
            label={sev}
            active={severityFilter === sev}
            color={sev !== "All" ? SEVERITY_COLORS[sev] : undefined}
            count={sev === "All" ? findings.length : severityCounts[sev]}
            onClick={() => handleFilter(() => setSeverityFilter(sev))}
          />
        ))}
      </div>

      {/* ── Type filters ─────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        {TYPE_FILTERS.map(({ key, icon, label }) => (
          <FilterPill
            key={key}
            label={`${icon} ${label}`}
            active={typeFilter === key}
            onClick={() => handleFilter(() => setTypeFilter(key))}
          />
        ))}
      </div>

      {/* ── Divider ──────────────────────────────────────────────────────────── */}
      <div style={{ height: "1px", background: "var(--border-subtle)" }} />

      {/* ── Finding cards ────────────────────────────────────────────────────── */}
      {findings.length === 0 ? (
        // Skeleton loading
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {[0, 1, 2, 3].map(i => <SkeletonCard key={i} index={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <div style={{
          padding:    "48px 24px",
          textAlign:  "center",
          fontFamily: "var(--font-mono)",
          fontSize:   "13px",
          color:      "var(--text-muted)",
        }}>
          No findings match your filters.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {paginated.map((finding, i) => (
            <FindingCard
              key={`${finding.file_path}-${finding.start_line}-${finding.issue_type}-${i}`}
              finding={finding}
              index={i}
            />
          ))}
        </div>
      )}

      {/* ── Pagination ───────────────────────────────────────────────────────── */}
      {totalPages > 1 && (
        <div style={{
          display:        "flex",
          justifyContent: "center",
          alignItems:     "center",
          gap:            "8px",
          marginTop:      "8px",
        }}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            style={{
              padding:    "5px 12px",
              background: "var(--bg-elevated)",
              border:     "1px solid var(--border-subtle)",
              borderRadius: "4px",
              color:      page === 1 ? "var(--text-muted)" : "var(--text-primary)",
              fontFamily: "var(--font-mono)",
              fontSize:   "11px",
              cursor:     page === 1 ? "not-allowed" : "pointer",
            }}
          >
            ← Prev
          </button>

          <span style={{
            fontFamily: "var(--font-mono)",
            fontSize:   "11px",
            color:      "var(--text-muted)",
          }}>
            {page} / {totalPages}
          </span>

          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            style={{
              padding:    "5px 12px",
              background: "var(--bg-elevated)",
              border:     "1px solid var(--border-subtle)",
              borderRadius: "4px",
              color:      page === totalPages ? "var(--text-muted)" : "var(--text-primary)",
              fontFamily: "var(--font-mono)",
              fontSize:   "11px",
              cursor:     page === totalPages ? "not-allowed" : "pointer",
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
