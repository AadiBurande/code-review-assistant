"use client";

import { useEffect, useRef, useState } from "react";

interface ScoreGaugeProps {
  score:   number;
  verdict: "accept" | "needs_changes" | "reject";
  animate?: boolean;
}

const VERDICT_CONFIG = {
  accept: {
    label:  "✓ Accept",
    color:  "#00FF87",
    bg:     "rgba(0, 255, 135, 0.10)",
    border: "rgba(0, 255, 135, 0.35)",
    glow:   "rgba(0, 255, 135, 0.30)",
  },
  needs_changes: {
    label:  "⚠ Needs Changes",
    color:  "#FFB347",
    bg:     "rgba(255, 179, 71, 0.10)",
    border: "rgba(255, 179, 71, 0.35)",
    glow:   "rgba(255, 179, 71, 0.25)",
  },
  reject: {
    label:  "✕ Reject",
    color:  "#FF3B3B",
    bg:     "rgba(255, 59, 59, 0.10)",
    border: "rgba(255, 59, 59, 0.35)",
    glow:   "rgba(255, 59, 59, 0.25)",
  },
};

function scoreColor(score: number): string {
  if (score >= 80) return "#00FF87";
  if (score >= 60) return "#00D4FF";
  if (score >= 40) return "#FFB347";
  return "#FF3B3B";
}

function ArcCanvas({ score, animate }: { score: number; animate: boolean }) {
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const animRef    = useRef<number>(0);
  const currentRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx)  return;

    const SIZE    = canvas.width;
    const CX      = SIZE / 2;
    const CY      = SIZE / 2;
    const RADIUS  = SIZE * 0.38;
    const START   = Math.PI * 0.75;
    const TOTAL   = Math.PI * 1.5;
    const TARGET  = score;
    const COLOR   = scoreColor(score);
    const TRACK_W = SIZE * 0.048;

    const draw = (val: number) => {
      ctx.clearRect(0, 0, SIZE, SIZE);

      ctx.beginPath();
      ctx.arc(CX, CY, RADIUS, START, START + TOTAL);
      ctx.strokeStyle = "rgba(255,255,255,0.06)";
      ctx.lineWidth   = TRACK_W;
      ctx.lineCap     = "round";
      ctx.stroke();

      const end = START + (TOTAL * val) / 100;
      if (val > 0) {
        ctx.shadowColor = COLOR;
        ctx.shadowBlur  = SIZE * 0.06;

        const grad = ctx.createLinearGradient(0, SIZE, SIZE, 0);
        grad.addColorStop(0, scoreColor(Math.max(0, score - 40)));
        grad.addColorStop(1, COLOR);

        ctx.beginPath();
        ctx.arc(CX, CY, RADIUS, START, end);
        ctx.strokeStyle = grad;
        ctx.lineWidth   = TRACK_W;
        ctx.lineCap     = "round";
        ctx.stroke();
        ctx.shadowBlur  = 0;

        const dotX = CX + RADIUS * Math.cos(end);
        const dotY = CY + RADIUS * Math.sin(end);
        ctx.beginPath();
        ctx.arc(dotX, dotY, TRACK_W * 0.55, 0, Math.PI * 2);
        ctx.fillStyle   = COLOR;
        ctx.shadowColor = COLOR;
        ctx.shadowBlur  = SIZE * 0.04;
        ctx.fill();
        ctx.shadowBlur  = 0;
      }

      for (let t = 0; t <= 10; t++) {
        const angle   = START + (TOTAL * t) / 10;
        const isMajor = t % 5 === 0;
        const innerR  = RADIUS - (isMajor ? TRACK_W * 1.4 : TRACK_W * 1.1);
        const outerR  = RADIUS - TRACK_W * 0.6;
        ctx.beginPath();
        ctx.moveTo(CX + innerR * Math.cos(angle), CY + innerR * Math.sin(angle));
        ctx.lineTo(CX + outerR * Math.cos(angle), CY + outerR * Math.sin(angle));
        ctx.strokeStyle = isMajor ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.06)";
        ctx.lineWidth   = isMajor ? 1.5 : 0.8;
        ctx.stroke();
      }
    };

    if (!animate) {
      currentRef.current = TARGET;
      draw(TARGET);
      return;
    }

    const DURATION = 1400;
    const start    = performance.now();
    const from     = currentRef.current;

    const tick = (now: number) => {
      const elapsed  = now - start;
      const progress = Math.min(elapsed / DURATION, 1);
      const eased    = 1 - Math.pow(1 - progress, 3);
      const val      = from + (TARGET - from) * eased;
      currentRef.current = val;
      draw(val);
      if (progress < 1) animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [score, animate]);

  return (
    <canvas
      ref={canvasRef}
      width={260}
      height={260}
      style={{ width: "260px", height: "260px" }}
    />
  );
}

function CountUp({ target, duration = 1400 }: { target: number; duration?: number }) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const start = performance.now();
    const tick  = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased    = 1 - Math.pow(1 - progress, 3);
      setDisplay(eased * target);
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return <>{display.toFixed(1)}</>;
}

export default function ScoreGauge({ score, verdict, animate = true }: ScoreGaugeProps) {
  const [verdictVisible, setVerdictVisible] = useState(false);

  // ✅ Safe fallback — normalize "Accept" → "accept", "Needs Changes" → "needs_changes"
  const normalizeVerdict = (v: string): keyof typeof VERDICT_CONFIG => {
    const map: Record<string, keyof typeof VERDICT_CONFIG> = {
      accept:         "accept",
      Accept:         "accept",
      needs_changes:  "needs_changes",
      "Needs Changes":"needs_changes",
      reject:         "reject",
      Reject:         "reject",
    };
    return map[v] ?? "needs_changes";
  };

  const vc = VERDICT_CONFIG[normalizeVerdict(verdict)];

  useEffect(() => {
    if (!animate) { setVerdictVisible(true); return; }
    const t = setTimeout(() => setVerdictVisible(true), 1500);
    return () => clearTimeout(t);
  }, [animate, verdict]);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", position: "relative" }}>

      <div style={{ position: "relative", width: "260px", height: "260px" }}>
        <ArcCanvas score={score} animate={animate} />

        <div style={{
          position:       "absolute",
          inset:          0,
          display:        "flex",
          flexDirection:  "column",
          alignItems:     "center",
          justifyContent: "center",
          paddingBottom:  "20px",
        }}>
          <div style={{
            fontFamily:    "var(--font-mono)",
            fontSize:      "44px",
            fontWeight:    700,
            lineHeight:    1,
            color:         scoreColor(score),
            letterSpacing: "-0.04em",
            textShadow:    `0 0 24px ${scoreColor(score)}66`,
          }}>
            {animate ? <CountUp target={score} /> : score.toFixed(1)}
          </div>

          <div style={{
            fontFamily:    "var(--font-mono)",
            fontSize:      "12px",
            color:         "var(--text-muted)",
            marginTop:     "4px",
            letterSpacing: "0.06em",
          }}>
            / 100
          </div>

          <div style={{
            fontFamily:    "var(--font-mono)",
            fontSize:      "9px",
            color:         "var(--text-muted)",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            marginTop:     "8px",
          }}>
            Quality Score
          </div>
        </div>
      </div>

      <div style={{
        marginTop:    "16px",
        padding:      "8px 20px",
        background:   vc.bg,
        border:       `1px solid ${vc.border}`,
        borderRadius: "100px",
        fontFamily:   "var(--font-mono)",
        fontSize:     "12px",
        fontWeight:   600,
        color:        vc.color,
        letterSpacing:"0.06em",
        boxShadow:    verdictVisible ? `0 0 20px ${vc.glow}` : "none",
        opacity:      verdictVisible ? 1 : 0,
        transform:    verdictVisible ? "scale(1)" : "scale(0.92)",
        transition:   "all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)",
      }}>
        {vc.label}
      </div>
    </div>
  );
}
