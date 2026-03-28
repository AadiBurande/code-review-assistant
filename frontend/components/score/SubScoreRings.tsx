// components/score/SubScoreRings.tsx
"use client";

import { useEffect, useRef, useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface SubScores {
  bug: number;
  security: number;
  performance: number;
  style: number;
}

interface SubScoreRingsProps {
  scores: SubScores;
  animate?: boolean;
}

// ── Per-category config ───────────────────────────────────────────────────────

const CATEGORY_CONFIG = {
  bug: {
    label:  "Bug",
    icon:   "🐛",
    color:  "#FF6B6B",
    glow:   "rgba(255, 107, 107, 0.30)",
  },
  security: {
    label:  "Security",
    icon:   "🔒",
    color:  "#FF6B35",
    glow:   "rgba(255, 107, 53, 0.30)",
  },
  performance: {
    label:  "Perf",
    icon:   "⚡",
    color:  "#A78BFA",
    glow:   "rgba(167, 139, 250, 0.30)",
  },
  style: {
    label:  "Style",
    icon:   "✦",
    color:  "#34D399",
    glow:   "rgba(52, 211, 153, 0.30)",
  },
};

// ── Mini Ring Canvas ──────────────────────────────────────────────────────────

function MiniRing({
  score,
  color,
  size = 80,
  animate,
}: {
  score: number;
  color: string;
  size?: number;
  animate: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef   = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const CX      = size / 2;
    const CY      = size / 2;
    const RADIUS  = size * 0.38;
    const START   = -Math.PI / 2;   // top
    const TOTAL   = Math.PI * 2;    // full circle
    const TRACK_W = size * 0.09;
    const TARGET  = score;

    const draw = (val: number) => {
      ctx.clearRect(0, 0, size, size);

      // Track
      ctx.beginPath();
      ctx.arc(CX, CY, RADIUS, 0, TOTAL);
      ctx.strokeStyle = "rgba(255,255,255,0.05)";
      ctx.lineWidth   = TRACK_W;
      ctx.stroke();

      // Filled arc
      if (val > 0) {
        const end = START + (TOTAL * val) / 100;

        ctx.shadowColor = color;
        ctx.shadowBlur  = size * 0.15;

        ctx.beginPath();
        ctx.arc(CX, CY, RADIUS, START, end);
        ctx.strokeStyle = color;
        ctx.lineWidth   = TRACK_W;
        ctx.lineCap     = "round";
        ctx.stroke();
        ctx.shadowBlur  = 0;
      }
    };

    if (!animate) {
      draw(TARGET);
      return;
    }

    const DURATION = 1200;
    const startT   = performance.now();

    const tick = (now: number) => {
      const elapsed  = now - startT;
      const progress = Math.min(elapsed / DURATION, 1);
      const eased    = 1 - Math.pow(1 - progress, 3);
      draw(TARGET * eased);
      if (progress < 1) animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [score, color, size, animate]);

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      style={{ width: `${size}px`, height: `${size}px` }}
    />
  );
}

// ── Animated counter ──────────────────────────────────────────────────────────

function CountUp({ target, duration = 1200 }: { target: number; duration?: number }) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const startT = performance.now();
    const tick = (now: number) => {
      const elapsed  = now - startT;
      const progress = Math.min(elapsed / duration, 1);
      const eased    = 1 - Math.pow(1 - progress, 3);
      setDisplay(target * eased);
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return <>{display.toFixed(0)}</>;
}

// ── Single Ring Card ──────────────────────────────────────────────────────────

function RingCard({
  category,
  score,
  animate,
  delay,
}: {
  category: keyof typeof CATEGORY_CONFIG;
  score: number;
  animate: boolean;
  delay: number;
}) {
  const [visible, setVisible] = useState(false);
  const cfg = CATEGORY_CONFIG[category];

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  return (
    <div
      style={{
        flex:          1,
        minWidth:      "100px",
        background:    "var(--bg-elevated)",
        border:        "1px solid var(--border-subtle)",
        borderRadius:  "10px",
        padding:       "16px 12px",
        display:       "flex",
        flexDirection: "column",
        alignItems:    "center",
        gap:           "10px",
        opacity:       visible ? 1 : 0,
        transform:     visible ? "translateY(0)" : "translateY(12px)",
        transition:    "opacity 0.4s ease, transform 0.4s ease",
        cursor:        "default",
        position:      "relative",
        overflow:      "hidden",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = `${cfg.color}44`;
        (e.currentTarget as HTMLDivElement).style.boxShadow   = `0 0 16px ${cfg.glow}`;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-subtle)";
        (e.currentTarget as HTMLDivElement).style.boxShadow   = "none";
      }}
    >
      {/* Ring + center score */}
      <div style={{ position: "relative", width: "80px", height: "80px" }}>
        <MiniRing score={score} color={cfg.color} size={80} animate={animate} />

        {/* Center text */}
        <div style={{
          position:       "absolute",
          inset:          0,
          display:        "flex",
          flexDirection:  "column",
          alignItems:     "center",
          justifyContent: "center",
          gap:            "1px",
        }}>
          <span style={{ fontSize: "13px" }}>{cfg.icon}</span>
          <span style={{
            fontFamily:    "var(--font-mono)",
            fontSize:      "13px",
            fontWeight:    700,
            color:         cfg.color,
            lineHeight:    1,
          }}>
            {animate ? <CountUp target={score} /> : Math.round(score)}
          </span>
        </div>
      </div>

      {/* Label */}
      <div style={{
        fontFamily:    "var(--font-mono)",
        fontSize:      "10px",
        fontWeight:    600,
        color:         "var(--text-secondary)",
        letterSpacing: "0.08em",
        textTransform: "uppercase",
      }}>
        {cfg.label}
      </div>

      {/* Score bar at bottom */}
      <div style={{
        width:        "100%",
        height:       "2px",
        background:   "var(--border-subtle)",
        borderRadius: "1px",
        overflow:     "hidden",
      }}>
        <div style={{
          height:     "100%",
          width:      visible ? `${score}%` : "0%",
          background: cfg.color,
          borderRadius: "1px",
          transition: `width 1.2s ease ${delay}ms`,
          boxShadow:  `0 0 6px ${cfg.glow}`,
        }} />
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function SubScoreRings({ scores, animate = true }: SubScoreRingsProps) {
  return (
    <div style={{ width: "100%" }}>

      {/* Section label */}
      <div style={{
        display:       "flex",
        alignItems:    "center",
        gap:           "10px",
        marginBottom:  "14px",
      }}>
        <span style={{
          fontFamily:    "var(--font-mono)",
          fontSize:      "11px",
          fontWeight:    600,
          color:         "var(--text-secondary)",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}>
          Agent Scores
        </span>
        <div style={{ flex: 1, height: "1px", background: "var(--border-subtle)" }} />
      </div>

      {/* 4 ring cards */}
      <div style={{
        display:  "flex",
        gap:      "10px",
        flexWrap: "wrap",
      }}>
        {(Object.keys(CATEGORY_CONFIG) as Array<keyof typeof CATEGORY_CONFIG>).map((key, i) => (
          <RingCard
            key={key}
            category={key}
            score={scores[key]}
            animate={animate}
            delay={200 + i * 100}
          />
        ))}
      </div>
    </div>
  );
}
