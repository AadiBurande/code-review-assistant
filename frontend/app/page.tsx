// app/page.tsx
"use client";

import { useEffect, useRef, useState } from "react";
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

// ── Stat counter ──────────────────────────────────────────────────────────────

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

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [mounted, setMounted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

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
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 212, 255, ${p.opacity})`;
        ctx.fill();
      });

      // Draw connections
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

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <main style={{ minHeight: "100vh", position: "relative", overflow: "hidden" }}>

      {/* ── Particle canvas ─────────────────────────────────────────────────── */}
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
          opacity: 0.6,
        }}
      />

      {/* ── Floating code lines ──────────────────────────────────────────────── */}
      <div style={{ position: "fixed", inset: 0, zIndex: 0, overflow: "hidden", pointerEvents: "none" }}>
        {CODE_LINES.map((line, i) => (
          <FloatingCodeLine
            key={i}
            text={line}
            delay={i * 1.1}
            top={`${8 + i * 7}%`}
            left={i % 2 === 0 ? `${2 + i * 3}%` : `${55 + (i % 4) * 8}%`}
            duration={12 + i * 1.5}
          />
        ))}
      </div>

      {/* ── Page content ────────────────────────────────────────────────────── */}
      <div style={{
        position: "relative",
        zIndex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "80px 24px",
      }}>

        {/* ── Top label ──────────────────────────────────────────────────────── */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "5px 14px",
            border: "1px solid var(--accent-border)",
            borderRadius: "100px",
            marginBottom: "32px",
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(-8px)",
            transition: "all 0.5s ease",
          }}
        >
          <span style={{
            width: "6px", height: "6px",
            borderRadius: "50%",
            background: "var(--accent)",
            boxShadow: "0 0 8px var(--accent)",
            animation: "pulse 2s ease infinite",
          }} />
          <span style={{
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "var(--accent)",
            letterSpacing: "0.1em",
          }}>
            MULTI-AGENT AI PIPELINE · v1.0
          </span>
        </div>

        {/* ── Headline ───────────────────────────────────────────────────────── */}
        <h1
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "clamp(28px, 5vw, 52px)",
            fontWeight: 700,
            textAlign: "center",
            lineHeight: 1.15,
            letterSpacing: "-0.03em",
            marginBottom: "20px",
            maxWidth: "780px",
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(12px)",
            transition: "all 0.6s ease 0.1s",
          }}
        >
          Code Review{" "}
          <span style={{
            color: "var(--accent)",
            textShadow: "0 0 30px rgba(0,212,255,0.4)",
          }}>
            Powered by AI
          </span>
          <br />
          <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>
            Agents
          </span>
        </h1>

        {/* ── Subtitle ───────────────────────────────────────────────────────── */}
        <p
          style={{
            fontSize: "15px",
            color: "var(--text-secondary)",
            textAlign: "center",
            maxWidth: "520px",
            lineHeight: 1.7,
            marginBottom: "48px",
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(12px)",
            transition: "all 0.6s ease 0.2s",
          }}
        >
          Drop your source file. Four specialized AI agents analyze it for bugs,
          security vulnerabilities, performance bottlenecks, and style violations —
          in seconds.
        </p>

        {/* ── DropZone ───────────────────────────────────────────────────────── */}
        <div
          style={{
            width: "100%",
            maxWidth: "640px",
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(16px)",
            transition: "all 0.6s ease 0.3s",
          }}
        >
          <DropZone />
        </div>

        {/* ── Stats row ──────────────────────────────────────────────────────── */}
        <div
          style={{
            display: "flex",
            gap: "48px",
            marginTop: "64px",
            paddingTop: "32px",
            borderTop: "1px solid var(--border-subtle)",
            opacity: mounted ? 1 : 0,
            transition: "opacity 0.6s ease 0.5s",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          <StatItem value="4"         label="AI Agents"        />
          <StatItem value="3"         label="Languages"        />
          <StatItem value="50+"       label="Detection Rules"  />
          <StatItem value="0→100"     label="Quality Score"    />
        </div>

        {/* ── Pipeline stages preview ─────────────────────────────────────────── */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0",
            marginTop: "40px",
            flexWrap: "wrap",
            justifyContent: "center",
            opacity: mounted ? 0.6 : 0,
            transition: "opacity 0.6s ease 0.6s",
          }}
        >
          {["Ingestion", "Static", "Bug", "Security", "Perf", "Style", "Report"].map((s, i, arr) => (
            <div key={s} style={{ display: "flex", alignItems: "center" }}>
              <span style={{
                fontFamily: "var(--font-mono)",
                fontSize: "10px",
                color: "var(--text-muted)",
                padding: "3px 8px",
                border: "1px solid var(--border-subtle)",
                borderRadius: "4px",
                letterSpacing: "0.05em",
              }}>
                {s}
              </span>
              {i < arr.length - 1 && (
                <span style={{
                  width: "16px",
                  height: "1px",
                  background: "var(--border-subtle)",
                  display: "block",
                }} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Keyframes ─────────────────────────────────────────────────────────── */}
      <style>{`
        @keyframes floatUp {
          0%, 100% { opacity: 0.06; transform: translateY(0px); }
          50%       { opacity: 0.14; transform: translateY(-8px); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }
      `}</style>
    </main>
  );
}
