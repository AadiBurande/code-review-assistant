// app/page.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import DropZone from "@/components/upload/DropZone";

// ── Animated code lines in background ────────────────────────────────────────

const CODE_LINES = [
  "def authenticate(user, pwd): ...",
  "SELECT * FROM users WHERE id = ?",
  "eval(user_input)  # ← dangerous",
  "const token = Math.random()",
  "Runtime.exec(cmd + userInput)",
  "password = 'hardcoded123'",
  "innerHTML = req.body.data",
  "while(true) { process() }",
  "catch(Exception e) {}",
  "new Random().nextInt(999999)",
  "exec(`ls ${userDir}`)",
  "res.send(req.query.input)",
];

function FloatingCodeLine({ text, delay, top, left, duration }: {
  text: string; delay: number; top: string; left: string; duration: number;
}) {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        top,
        left,
        fontFamily: "var(--font-mono)",
        fontSize: "11px",
        color: "rgba(0, 212, 255, 0.12)",
        whiteSpace: "nowrap",
        animation: `floatUp ${duration}s ${delay}s ease-in-out infinite`,
        pointerEvents: "none",
        userSelect: "none",
      }}
    >
      {text}
    </div>
  );
}

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{
        fontFamily: "var(--font-mono)",
        fontSize: "22px",
        fontWeight: 700,
        color: "var(--accent)",
        letterSpacing: "-0.02em",
      }}>
        {value}
      </div>
      <div style={{
        fontSize: "11px",
        color: "var(--text-muted)",
        marginTop: "4px",
        letterSpacing: "0.06em",
        textTransform: "uppercase",
      }}>
        {label}
      </div>
    </div>
  );
}

// ── GitHub Tab Component ──────────────────────────────────────────────────────

type ValidationState = "idle" | "loading" | "valid" | "error";

interface RepoMeta {
  owner: string;
  repo: string;
  branch: string;
  description: string;
  language: string;
  stars: number;
  private: boolean;
}

function GitHubInput() {
  const router = useRouter();
  const [repoUrl, setRepoUrl]           = useState("");
  const [token, setToken]               = useState("");
  const [showToken, setShowToken]       = useState(false);
  const [context, setContext]           = useState("");
  const [validation, setValidation]     = useState<ValidationState>("idle");
  const [repoMeta, setRepoMeta]         = useState<RepoMeta | null>(null);
  const [validationMsg, setValidationMsg] = useState("");
  const [submitting, setSubmitting]     = useState(false);
  const validateTimeout                 = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Live URL validation ───────────────────────────────────────────────────
  useEffect(() => {
    if (validateTimeout.current) clearTimeout(validateTimeout.current);

    const url = repoUrl.trim();
    if (!url || !url.startsWith("https://github.com/")) {
      setValidation("idle");
      setRepoMeta(null);
      return;
    }

    setValidation("loading");

    validateTimeout.current = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ url });
        if (token) params.append("token", token);

        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/analyze/github/validate?${params}`
        );

        if (!res.ok) {
          const err = await res.json();
          setValidation("error");
          setValidationMsg(err.detail || "Repository not found or inaccessible.");
          setRepoMeta(null);
          return;
        }

        const data = await res.json();
        setValidation("valid");
        setValidationMsg(data.message);
        setRepoMeta({
          owner:       data.owner,
          repo:        data.repo,
          branch:      data.branch,
          description: data.description || "",
          language:    data.language    || "unknown",
          stars:       data.stars       || 0,
          private:     data.private     || false,
        });
      } catch {
        setValidation("error");
        setValidationMsg("Could not reach backend. Is the server running?");
        setRepoMeta(null);
      }
    }, 700);

    return () => {
      if (validateTimeout.current) clearTimeout(validateTimeout.current);
    };
  }, [repoUrl, token]);

  // ── Submit ────────────────────────────────────────────────────────────────
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim() || submitting) return;

    setSubmitting(true);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/analyze/github`,
        {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({
            repo_url:        repoUrl.trim(),
            token:           token || undefined,
            project_context: context,
            project_name:    repoMeta?.repo,
            language:        repoMeta?.language !== "unknown" ? repoMeta?.language : undefined,
          }),
        }
      );

      if (!res.ok) {
        const err = await res.json();
        alert(`Error: ${err.detail || "Submission failed."}`);
        setSubmitting(false);
        return;
      }

      const data = await res.json();
      router.push(`/results/${data.session_id}`);
    } catch (err) {
      alert("Network error. Is the backend running?");
      setSubmitting(false);
    }
  }

  const inputBorder =
    validation === "valid"   ? "1px solid rgba(0, 212, 120, 0.5)"  :
    validation === "error"   ? "1px solid rgba(255, 80, 80, 0.5)"  :
    validation === "loading" ? "1px solid rgba(0, 212, 255, 0.3)"  :
                               "1px solid var(--border-subtle)";

  const inputGlow =
    validation === "valid"   ? "0 0 12px rgba(0, 212, 120, 0.15)"  :
    validation === "error"   ? "0 0 12px rgba(255, 80, 80, 0.15)"  :
    validation === "loading" ? "0 0 12px rgba(0, 212, 255, 0.10)"  :
                               "none";

  return (
    <form onSubmit={handleSubmit} style={{ width: "100%" }}>

      {/* ── URL Input ───────────────────────────────────────────────────── */}
      <div style={{ position: "relative" }}>
        <div style={{
          display:     "flex",
          alignItems:  "center",
          gap:         "10px",
          background:  "var(--bg-surface)",
          border:      inputBorder,
          borderRadius: "10px",
          padding:     "12px 16px",
          transition:  "all 0.2s ease",
          boxShadow:   inputGlow,
        }}>
          {/* GitHub icon */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"
            style={{ color: "var(--text-muted)", flexShrink: 0 }}>
            <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
          </svg>

          <input
            type="url"
            value={repoUrl}
            onChange={e => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repository"
            required
            style={{
              flex:        1,
              background:  "transparent",
              border:      "none",
              outline:     "none",
              fontFamily:  "var(--font-mono)",
              fontSize:    "13px",
              color:       "var(--text-primary)",
            }}
          />

          {/* Validation indicator */}
          {validation === "loading" && (
            <div style={{
              width: "14px", height: "14px", borderRadius: "50%",
              border: "2px solid rgba(0,212,255,0.3)",
              borderTopColor: "var(--accent)",
              animation: "spin 0.6s linear infinite",
              flexShrink: 0,
            }} />
          )}
          {validation === "valid" && (
            <span style={{ color: "#00d478", fontSize: "16px", flexShrink: 0 }}>✓</span>
          )}
          {validation === "error" && (
            <span style={{ color: "#ff5050", fontSize: "16px", flexShrink: 0 }}>✗</span>
          )}
        </div>

        {/* Validation message */}
        {validation !== "idle" && validationMsg && (
          <p style={{
            fontSize: "11px",
            color:    validation === "valid" ? "#00d478" : validation === "error" ? "#ff5050" : "var(--text-muted)",
            marginTop: "6px",
            paddingLeft: "4px",
          }}>
            {validationMsg}
          </p>
        )}
      </div>

      {/* ── Repo metadata preview ────────────────────────────────────────── */}
      {validation === "valid" && repoMeta && (
        <div style={{
          marginTop:   "12px",
          padding:     "12px 14px",
          background:  "rgba(0, 212, 255, 0.04)",
          border:      "1px solid rgba(0, 212, 255, 0.12)",
          borderRadius: "8px",
          display:     "flex",
          gap:         "16px",
          flexWrap:    "wrap",
          alignItems:  "center",
        }}>
          <div style={{ flex: 1, minWidth: "120px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--accent)", fontWeight: 600 }}>
              {repoMeta.owner}/{repoMeta.repo}
            </div>
            {repoMeta.description && (
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "3px" }}>
                {repoMeta.description.slice(0, 80)}{repoMeta.description.length > 80 ? "…" : ""}
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: "12px", flexShrink: 0 }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              {repoMeta.branch}
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              {repoMeta.language}
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              ⭐ {repoMeta.stars.toLocaleString()}
            </span>
            {repoMeta.private && (
              <span style={{
                fontSize: "10px", background: "rgba(255,165,0,0.15)",
                color: "#ffaa44", padding: "1px 7px", borderRadius: "100px",
                border: "1px solid rgba(255,165,0,0.25)",
              }}>
                private
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Token input (expandable) ─────────────────────────────────────── */}
      <div style={{ marginTop: "10px" }}>
        <button
          type="button"
          onClick={() => setShowToken(!showToken)}
          style={{
            background:  "none",
            border:      "none",
            color:       "var(--text-muted)",
            fontFamily:  "var(--font-mono)",
            fontSize:    "11px",
            cursor:      "pointer",
            padding:     "2px 0",
            display:     "flex",
            alignItems:  "center",
            gap:         "6px",
            transition:  "color 0.15s",
          }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--accent)")}
          onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}
        >
          <span style={{ fontSize: "10px" }}>{showToken ? "▼" : "▶"}</span>
          {repoMeta?.private ? "⚠️ Private repo — token required" : "Add GitHub token (optional, for private repos)"}
        </button>

        {showToken && (
          <div style={{ marginTop: "8px" }}>
            <input
              type="password"
              value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              style={{
                width:       "100%",
                background:  "var(--bg-surface)",
                border:      "1px solid var(--border-subtle)",
                borderRadius: "8px",
                padding:     "10px 14px",
                fontFamily:  "var(--font-mono)",
                fontSize:    "12px",
                color:       "var(--text-primary)",
                outline:     "none",
              }}
              onFocus={e => (e.currentTarget.style.borderColor = "var(--accent-border)")}
              onBlur={e => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
            />
            <p style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "5px", paddingLeft: "2px" }}>
              Token never stored. Used only for this request. Create one at github.com/settings/tokens
            </p>
          </div>
        )}
      </div>

      {/* ── Project context ───────────────────────────────────────────────── */}
      <div style={{ marginTop: "10px" }}>
        <textarea
          value={context}
          onChange={e => setContext(e.target.value)}
          placeholder="Optional: describe the project (e.g. 'FastAPI REST API for a fintech app')"
          rows={2}
          style={{
            width:       "100%",
            resize:      "vertical",
            background:  "var(--bg-surface)",
            border:      "1px solid var(--border-subtle)",
            borderRadius: "8px",
            padding:     "10px 14px",
            fontFamily:  "var(--font-body, sans-serif)",
            fontSize:    "13px",
            color:       "var(--text-primary)",
            outline:     "none",
            lineHeight:  1.5,
          }}
          onFocus={e => (e.currentTarget.style.borderColor = "var(--accent-border)")}
          onBlur={e => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
        />
      </div>

      {/* ── Submit button ─────────────────────────────────────────────────── */}
      <button
        type="submit"
        disabled={submitting || !repoUrl.trim()}
        style={{
          marginTop:    "14px",
          width:        "100%",
          padding:      "13px",
          background:   submitting || !repoUrl.trim()
            ? "rgba(0,212,255,0.08)"
            : "linear-gradient(135deg, rgba(0,212,255,0.15), rgba(0,212,255,0.08))",
          border:       "1px solid var(--accent-border)",
          borderRadius: "10px",
          color:        submitting || !repoUrl.trim() ? "var(--text-muted)" : "var(--accent)",
          fontFamily:   "var(--font-mono)",
          fontSize:     "13px",
          fontWeight:   600,
          cursor:       submitting || !repoUrl.trim() ? "not-allowed" : "pointer",
          transition:   "all 0.2s ease",
          letterSpacing: "0.05em",
          display:      "flex",
          alignItems:   "center",
          justifyContent: "center",
          gap:          "10px",
        }}
        onMouseEnter={e => {
          if (!submitting && repoUrl.trim()) {
            (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 0 20px rgba(0,212,255,0.2)";
            (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent)";
          }
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
          (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent-border)";
        }}
      >
        {submitting ? (
          <>
            <div style={{
              width: "14px", height: "14px", borderRadius: "50%",
              border: "2px solid rgba(0,212,255,0.3)",
              borderTopColor: "var(--accent)",
              animation: "spin 0.6s linear infinite",
            }} />
            Fetching & analyzing…
          </>
        ) : (
          <>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
            </svg>
            Analyze GitHub Repository
          </>
        )}
      </button>
    </form>
  );
}

// ── Tab Switch ────────────────────────────────────────────────────────────────

type Tab = "upload" | "github";

function InputTabs() {
  const [activeTab, setActiveTab] = useState<Tab>("upload");

  const tabStyle = (tab: Tab): React.CSSProperties => ({
    flex:         1,
    padding:      "9px 0",
    background:   activeTab === tab ? "rgba(0,212,255,0.08)" : "transparent",
    border:       "none",
    borderBottom: activeTab === tab
      ? "2px solid var(--accent)"
      : "2px solid transparent",
    color:        activeTab === tab ? "var(--accent)" : "var(--text-muted)",
    fontFamily:   "var(--font-mono)",
    fontSize:     "12px",
    fontWeight:   activeTab === tab ? 600 : 400,
    cursor:       "pointer",
    transition:   "all 0.18s ease",
    letterSpacing: "0.06em",
    display:      "flex",
    alignItems:   "center",
    justifyContent: "center",
    gap:          "7px",
  });

  return (
    <div style={{
      width:        "100%",
      maxWidth:     "640px",
      background:   "var(--bg-surface)",
      border:       "1px solid var(--border-subtle)",
      borderRadius: "12px",
      overflow:     "hidden",
    }}>
      {/* Tab headers */}
      <div style={{
        display:      "flex",
        borderBottom: "1px solid var(--border-subtle)",
        background:   "rgba(0,0,0,0.15)",
      }}>
        <button style={tabStyle("upload")} onClick={() => setActiveTab("upload")}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          UPLOAD FILE
        </button>

        <button style={tabStyle("github")} onClick={() => setActiveTab("github")}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
          </svg>
          GITHUB REPO
        </button>
      </div>

      {/* Tab content */}
      <div style={{ padding: "20px" }}>
        {activeTab === "upload" ? <DropZone /> : <GitHubInput />}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [mounted, setMounted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const router = useRouter();

  useEffect(() => { setMounted(true); }, []);

  // ── Particle canvas ────────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles: { x: number; y: number; vx: number; vy: number; size: number; opacity: number }[] = [];
    for (let i = 0; i < 60; i++) {
      particles.push({
        x:       Math.random() * canvas.width,
        y:       Math.random() * canvas.height,
        vx:      (Math.random() - 0.5) * 0.3,
        vy:      (Math.random() - 0.5) * 0.3,
        size:    Math.random() * 1.5 + 0.5,
        opacity: Math.random() * 0.4 + 0.1,
      });
    }

    let animId: number;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p) => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 212, 255, ${p.opacity})`;
        ctx.fill();
      });
      particles.forEach((a, i) => {
        particles.slice(i + 1).forEach((b) => {
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `rgba(0, 212, 255, ${0.06 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        });
      });
      animId = requestAnimationFrame(draw);
    };
    draw();

    const handleResize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);
    return () => { cancelAnimationFrame(animId); window.removeEventListener("resize", handleResize); };
  }, []);

  return (
    <main style={{ minHeight: "100vh", position: "relative", overflow: "hidden" }}>
      <canvas ref={canvasRef} aria-hidden="true" style={{
        position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none", opacity: 0.6,
      }} />

      <div style={{ position: "fixed", inset: 0, zIndex: 0, overflow: "hidden", pointerEvents: "none" }}>
        {CODE_LINES.map((line, i) => (
          <FloatingCodeLine key={i} text={line} delay={i * 1.1}
            top={`${8 + i * 7}%`}
            left={i % 2 === 0 ? `${2 + i * 3}%` : `${55 + (i % 4) * 8}%`}
            duration={12 + i * 1.5}
          />
        ))}
      </div>

      {/* History button */}
      <div style={{
        position: "fixed", top: "20px", right: "28px", zIndex: 50,
        opacity: mounted ? 1 : 0, transition: "opacity 0.4s ease 0.3s",
      }}>
        <button onClick={() => router.push("/history")} style={{
          background: "var(--bg-surface)", border: "1px solid var(--border-subtle)",
          borderRadius: "8px", color: "var(--text-muted)", fontFamily: "var(--font-mono)",
          fontSize: "11px", padding: "7px 16px", cursor: "pointer",
          transition: "all 0.15s", backdropFilter: "blur(8px)",
        }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent-border)";
          (e.currentTarget as HTMLButtonElement).style.color = "var(--accent)";
          (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 0 12px rgba(0,212,255,0.15)";
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-subtle)";
          (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
          (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
        }}>
          History →
        </button>
      </div>

      {/* Page content */}
      <div style={{
        position: "relative", zIndex: 1, display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "80px 24px",
      }}>
        {/* Top label */}
        <div style={{
          display: "inline-flex", alignItems: "center", gap: "8px",
          padding: "5px 14px", border: "1px solid var(--accent-border)",
          borderRadius: "100px", marginBottom: "32px",
          opacity: mounted ? 1 : 0,
          transform: mounted ? "translateY(0)" : "translateY(-8px)",
          transition: "all 0.5s ease",
        }}>
          <span style={{
            width: "6px", height: "6px", borderRadius: "50%",
            background: "var(--accent)", boxShadow: "0 0 8px var(--accent)",
            animation: "pulse 2s ease infinite",
          }} />
          <span style={{
            fontFamily: "var(--font-mono)", fontSize: "11px",
            color: "var(--accent)", letterSpacing: "0.1em",
          }}>
            MULTI-AGENT AI PIPELINE · v1.1
          </span>
        </div>

        {/* Headline */}
        <h1 style={{
          fontFamily: "var(--font-mono)", fontSize: "clamp(28px, 5vw, 52px)",
          fontWeight: 700, textAlign: "center", lineHeight: 1.15,
          letterSpacing: "-0.03em", marginBottom: "20px", maxWidth: "780px",
          opacity: mounted ? 1 : 0,
          transform: mounted ? "translateY(0)" : "translateY(12px)",
          transition: "all 0.6s ease 0.1s",
        }}>
          Code Review{" "}
          <span style={{ color: "var(--accent)", textShadow: "0 0 30px rgba(0,212,255,0.4)" }}>
            Powered by AI
          </span>
          <br />
          <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>Agents</span>
        </h1>

        {/* Subtitle */}
        <p style={{
          fontSize: "15px", color: "var(--text-secondary)", textAlign: "center",
          maxWidth: "520px", lineHeight: 1.7, marginBottom: "48px",
          opacity: mounted ? 1 : 0,
          transform: mounted ? "translateY(0)" : "translateY(12px)",
          transition: "all 0.6s ease 0.2s",
        }}>
          Upload a file or paste a GitHub repo URL. Four specialized AI agents analyze
          it for bugs, security vulnerabilities, performance bottlenecks, and style
          violations — in seconds.
        </p>

        {/* ── TABBED INPUT (replaces plain DropZone) ── */}
        <div style={{
          width: "100%", maxWidth: "640px",
          opacity: mounted ? 1 : 0,
          transform: mounted ? "translateY(0)" : "translateY(16px)",
          transition: "all 0.6s ease 0.3s",
        }}>
          <InputTabs />
        </div>

        {/* Stats row */}
        <div style={{
          display: "flex", gap: "48px", marginTop: "64px",
          paddingTop: "32px", borderTop: "1px solid var(--border-subtle)",
          opacity: mounted ? 1 : 0, transition: "opacity 0.6s ease 0.5s",
          flexWrap: "wrap", justifyContent: "center",
        }}>
          <StatItem value="4"      label="AI Agents"       />
          <StatItem value="3"      label="Languages"       />
          <StatItem value="50+"    label="Detection Rules" />
          <StatItem value="0→100"  label="Quality Score"   />
        </div>

        {/* Pipeline stages */}
        <div style={{
          display: "flex", alignItems: "center", gap: "0",
          marginTop: "40px", flexWrap: "wrap", justifyContent: "center",
          opacity: mounted ? 0.6 : 0, transition: "opacity 0.6s ease 0.6s",
        }}>
          {["Ingestion", "Static", "Bug", "Security", "Perf", "Style", "Report"].map((s, i, arr) => (
            <div key={s} style={{ display: "flex", alignItems: "center" }}>
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)",
                padding: "3px 8px", border: "1px solid var(--border-subtle)",
                borderRadius: "4px", letterSpacing: "0.05em",
              }}>
                {s}
              </span>
              {i < arr.length - 1 && (
                <span style={{ width: "16px", height: "1px", background: "var(--border-subtle)", display: "block" }} />
              )}
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes floatUp {
          0%, 100% { opacity: 0.06; transform: translateY(0px); }
          50%       { opacity: 0.14; transform: translateY(-8px); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </main>
  );
}
