<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>CodeScan — AI-Powered Code Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Syncopate:wght@400;700&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet" />
<style>
  :root {
    --bg:        #050508;
    --bg2:       #0b0b12;
    --bg3:       #111120;
    --green:     #00ff88;
    --cyan:      #00d4ff;
    --red:       #ff3b5c;
    --orange:    #ff8c42;
    --yellow:    #ffe033;
    --purple:    #9b5de5;
    --text:      #c8d8e8;
    --muted:     #4a5568;
    --border:    #1a2035;
    --glow-g:    0 0 20px #00ff8855, 0 0 60px #00ff8822;
    --glow-c:    0 0 20px #00d4ff55, 0 0 60px #00d4ff22;
    --glow-r:    0 0 20px #ff3b5c55;
    --font-mono: 'Share Tech Mono', monospace;
    --font-head: 'Syncopate', sans-serif;
    --font-body: 'DM Mono', monospace;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-body);
    font-size: 14px;
    line-height: 1.7;
    overflow-x: hidden;
  }

  /* ── SCANLINE OVERLAY ── */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,.07) 2px, rgba(0,0,0,.07) 4px);
    pointer-events: none;
    z-index: 1000;
  }

  /* ── NOISE GRAIN ── */
  body::after {
    content: '';
    position: fixed;
    inset: -200%;
    width: 400%;
    height: 400%;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
    opacity: .4;
    pointer-events: none;
    z-index: 999;
    animation: grain 0.5s steps(1) infinite;
  }
  @keyframes grain { 0%,100%{transform:translate(0,0)} 10%{transform:translate(-2%,-3%)} 30%{transform:translate(3%,2%)} 50%{transform:translate(-1%,4%)} 70%{transform:translate(4%,-1%)} 90%{transform:translate(-3%,3%)} }

  /* ────────────── HERO ────────────── */
  .hero {
    position: relative;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 80px 20px 60px;
    overflow: hidden;
  }

  .hero-grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(0,255,136,.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,136,.04) 1px, transparent 1px);
    background-size: 48px 48px;
    animation: gridPulse 8s ease-in-out infinite;
  }
  @keyframes gridPulse { 0%,100%{opacity:.5} 50%{opacity:1} }

  .hero-glow {
    position: absolute;
    width: 700px; height: 700px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,255,136,.12) 0%, transparent 70%);
    top: 50%; left: 50%;
    transform: translate(-50%,-50%);
    animation: glowPulse 4s ease-in-out infinite;
  }
  @keyframes glowPulse { 0%,100%{transform:translate(-50%,-50%) scale(1);opacity:.8} 50%{transform:translate(-50%,-50%) scale(1.15);opacity:1} }

  .hero-corner {
    position: absolute;
    width: 80px; height: 80px;
    border-color: var(--green);
    border-style: solid;
    opacity: 0.4;
  }
  .hero-corner.tl { top: 40px; left: 40px; border-width: 2px 0 0 2px; }
  .hero-corner.tr { top: 40px; right: 40px; border-width: 2px 2px 0 0; }
  .hero-corner.bl { bottom: 40px; left: 40px; border-width: 0 0 2px 2px; }
  .hero-corner.br { bottom: 40px; right: 40px; border-width: 0 2px 2px 0; }

  .badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-bottom: 32px;
    position: relative;
    animation: fadeUp 1s ease 0.2s both;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 3px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    border: 1px solid;
    transition: all .2s;
  }
  .badge:hover { transform: translateY(-2px); }
  .badge.blue  { background: rgba(59,130,246,.1); border-color: rgba(59,130,246,.4); color: #60a5fa; }
  .badge.teal  { background: rgba(0,212,255,.08); border-color: rgba(0,212,255,.35); color: var(--cyan); }
  .badge.dark  { background: rgba(255,255,255,.04); border-color: rgba(255,255,255,.12); color: #94a3b8; }
  .badge.purple{ background: rgba(155,93,229,.1); border-color: rgba(155,93,229,.4); color: #c084fc; }
  .badge.orange{ background: rgba(255,140,66,.1); border-color: rgba(255,140,66,.35); color: var(--orange); }
  .badge.green { background: rgba(0,255,136,.08); border-color: rgba(0,255,136,.35); color: var(--green); }

  .logo-ascii {
    position: relative;
    font-family: var(--font-mono);
    font-size: clamp(6px, 1.3vw, 14px);
    line-height: 1.2;
    color: var(--green);
    text-shadow: var(--glow-g);
    white-space: pre;
    animation: fadeUp 1s ease 0.4s both;
    letter-spacing: 0;
  }

  .hero-tagline {
    font-family: var(--font-head);
    font-size: clamp(11px, 2vw, 15px);
    letter-spacing: .25em;
    color: var(--cyan);
    text-transform: uppercase;
    margin-top: 24px;
    animation: fadeUp 1s ease 0.6s both;
  }

  .hero-sub {
    font-size: 13px;
    color: var(--muted);
    margin-top: 16px;
    max-width: 520px;
    animation: fadeUp 1s ease 0.8s both;
    font-style: italic;
  }
  .hero-sub span { color: var(--green); font-style: normal; }

  .hero-stat-row {
    display: flex;
    gap: 40px;
    margin-top: 48px;
    flex-wrap: wrap;
    justify-content: center;
    animation: fadeUp 1s ease 1s both;
  }
  .hero-stat { text-align: center; }
  .hero-stat .num {
    font-family: var(--font-head);
    font-size: 28px;
    color: var(--green);
    text-shadow: var(--glow-g);
    display: block;
  }
  .hero-stat .lbl {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .15em;
    color: var(--muted);
  }

  @keyframes fadeUp { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:none} }

  /* ────────────── SECTION SHELL ────────────── */
  .section { padding: 80px 20px; max-width: 1100px; margin: 0 auto; }
  .section + .section { padding-top: 0; }

  .section-label {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-family: var(--font-mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .2em;
    color: var(--green);
    margin-bottom: 32px;
  }
  .section-label::before {
    content: '';
    display: block;
    width: 24px; height: 1px;
    background: var(--green);
    box-shadow: var(--glow-g);
  }

  .section-title {
    font-family: var(--font-head);
    font-size: clamp(22px, 4vw, 40px);
    font-weight: 700;
    letter-spacing: .05em;
    line-height: 1.1;
    color: #fff;
    margin-bottom: 20px;
  }
  .section-title .accent { color: var(--green); text-shadow: var(--glow-g); }
  .section-title .accent-c { color: var(--cyan); text-shadow: var(--glow-c); }

  /* ────────────── DIVIDER ────────────── */
  .divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border) 20%, var(--green) 50%, var(--border) 80%, transparent);
    margin: 0 20px;
    opacity: .5;
  }

  /* ────────────── WHAT IS CODESCAN ────────────── */
  .intro-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-top: 48px;
  }
  @media(max-width:700px){ .intro-grid { grid-template-columns: 1fr; } }

  .intro-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 28px;
    position: relative;
    overflow: hidden;
    transition: border-color .3s, transform .3s;
  }
  .intro-card:hover { border-color: var(--green); transform: translateY(-4px); }
  .intro-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at top left, rgba(0,255,136,.06) 0%, transparent 60%);
    opacity: 0;
    transition: opacity .3s;
  }
  .intro-card:hover::before { opacity: 1; }
  .intro-card .icon { font-size: 28px; margin-bottom: 12px; display: block; }
  .intro-card h3 { font-family: var(--font-head); font-size: 13px; letter-spacing: .1em; color: #fff; margin-bottom: 8px; text-transform: uppercase; }
  .intro-card p { color: var(--muted); font-size: 13px; line-height: 1.6; }

  .intro-desc {
    font-size: 15px;
    color: var(--text);
    line-height: 1.8;
    max-width: 680px;
    margin-bottom: 12px;
  }
  .intro-desc strong { color: var(--green); }

  /* ────────────── PIPELINE ────────────── */
  .pipeline-wrap {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 48px 32px;
    position: relative;
    overflow: hidden;
    margin-top: 16px;
  }
  .pipeline-wrap::before {
    content: 'PIPELINE';
    position: absolute;
    top: 20px; right: 24px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: .2em;
  }

  .pipe-flow {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
  }

  .pipe-input {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 14px 28px;
    background: var(--bg3);
    border: 2px solid var(--cyan);
    border-radius: 6px;
    font-family: var(--font-head);
    font-size: 11px;
    letter-spacing: .15em;
    color: var(--cyan);
    text-shadow: var(--glow-c);
    box-shadow: var(--glow-c);
    animation: inputPulse 3s ease-in-out infinite;
  }
  @keyframes inputPulse { 0%,100%{box-shadow: 0 0 12px rgba(0,212,255,.3)} 50%{box-shadow: 0 0 30px rgba(0,212,255,.6)} }

  .pipe-arrow {
    width: 2px;
    height: 40px;
    background: linear-gradient(to bottom, var(--cyan), var(--green));
    position: relative;
    overflow: hidden;
  }
  .pipe-arrow::after {
    content: '';
    position: absolute;
    top: -100%;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to bottom, transparent, #fff, transparent);
    animation: flowDown 1.5s ease-in-out infinite;
  }
  @keyframes flowDown { 0%{top:-100%} 100%{top:200%} }

  .pipe-arrow-down {
    width: 0; height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid var(--green);
  }

  .agents-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    width: 100%;
    margin: 24px 0;
  }
  @media(max-width:700px){ .agents-row { grid-template-columns: repeat(2,1fr); } }

  .agent-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all .3s;
    cursor: default;
  }
  .agent-card::before {
    content: '';
    position: absolute;
    inset: 0;
    opacity: 0;
    transition: opacity .3s;
  }
  .agent-card:hover { transform: translateY(-6px); }
  .agent-card:hover::before { opacity: 1; }

  .agent-card.bug  { --ac: #ff3b5c; }
  .agent-card.sec  { --ac: #ff8c42; }
  .agent-card.perf { --ac: #ffe033; }
  .agent-card.style{ --ac: #9b5de5; }

  .agent-card:hover { border-color: var(--ac); box-shadow: 0 0 24px color-mix(in srgb, var(--ac) 30%, transparent); }
  .agent-card::before { background: radial-gradient(circle at center, color-mix(in srgb, var(--ac) 12%, transparent), transparent 70%); }

  .agent-icon { font-size: 26px; display: block; margin-bottom: 8px; }
  .agent-name {
    font-family: var(--font-head);
    font-size: 9px;
    letter-spacing: .15em;
    text-transform: uppercase;
    color: var(--ac, #fff);
    margin-bottom: 10px;
    display: block;
  }
  .agent-tags { display: flex; flex-direction: column; gap: 3px; }
  .agent-tag {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    line-height: 1.4;
  }

  .pipe-engine {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 32px;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 6px;
    width: 100%;
    max-width: 500px;
  }
  .pipe-engine-icon { font-size: 20px; }
  .pipe-engine-label {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--muted);
  }
  .pipe-engine-label span { color: var(--text); }

  .pipe-output {
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 12px;
    width: 100%;
    max-width: 600px;
    margin-top: 8px;
  }
  @media(max-width:500px){ .pipe-output { grid-template-columns: 1fr; } }

  .output-pill {
    text-align: center;
    padding: 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 11px;
    transition: all .2s;
  }
  .output-pill:hover { border-color: var(--green); color: var(--green); }
  .output-pill .pill-icon { font-size: 18px; display: block; margin-bottom: 4px; }
  .output-pill .pill-label { color: var(--muted); font-size: 10px; }

  /* ────────────── WHAT GETS CAUGHT ────────────── */
  .agents-detail { display: flex; flex-direction: column; gap: 16px; margin-top: 16px; }

  .agent-detail-row {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 20px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 24px;
    transition: all .3s;
    align-items: start;
  }
  @media(max-width:700px){ .agent-detail-row { grid-template-columns: 1fr; } }
  .agent-detail-row:hover { border-color: var(--col); box-shadow: 0 0 20px color-mix(in srgb, var(--col) 20%, transparent); transform: translateX(4px); }

  .agent-detail-row.bug   { --col: #ff3b5c; }
  .agent-detail-row.sec   { --col: #ff8c42; }
  .agent-detail-row.perf  { --col: #ffe033; }
  .agent-detail-row.style { --col: #9b5de5; }

  .adr-head {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .adr-icon { font-size: 22px; }
  .adr-name {
    font-family: var(--font-head);
    font-size: 11px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--col);
  }

  .adr-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .adr-tag {
    font-family: var(--font-mono);
    font-size: 11px;
    padding: 4px 10px;
    background: color-mix(in srgb, var(--col) 10%, transparent);
    border: 1px solid color-mix(in srgb, var(--col) 25%, transparent);
    color: var(--col);
    border-radius: 3px;
    letter-spacing: .04em;
  }

  /* ────────────── TECH STACK ────────────── */
  .stack-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-top: 16px;
  }
  @media(max-width:800px){ .stack-grid { grid-template-columns: 1fr 1fr; } }
  @media(max-width:500px){ .stack-grid { grid-template-columns: 1fr; } }

  .stack-col {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
  }
  .stack-col-head {
    padding: 14px 20px;
    font-family: var(--font-head);
    font-size: 10px;
    letter-spacing: .15em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .stack-col-head.be { color: var(--cyan); background: rgba(0,212,255,.05); }
  .stack-col-head.fe { color: var(--purple); background: rgba(155,93,229,.05); }
  .stack-col-head.llm { color: var(--green); background: rgba(0,255,136,.05); }

  .stack-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    border-bottom: 1px solid rgba(255,255,255,.03);
    transition: background .2s;
  }
  .stack-item:hover { background: rgba(255,255,255,.02); }
  .stack-item:last-child { border-bottom: none; }
  .stack-name { font-family: var(--font-mono); font-size: 12px; color: var(--text); font-weight: 500; }
  .stack-role { font-size: 11px; color: var(--muted); text-align: right; max-width: 140px; line-height: 1.3; }

  .llm-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .llm-dot.green  { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .llm-dot.blue   { background: var(--cyan); box-shadow: 0 0 6px var(--cyan); }
  .llm-dot.orange { background: var(--orange); box-shadow: 0 0 6px var(--orange); }
  .llm-dot.white  { background: #94a3b8; }
  .llm-rec { font-size: 9px; color: var(--green); border: 1px solid rgba(0,255,136,.3); padding: 2px 6px; border-radius: 2px; }

  /* ────────────── GETTING STARTED ────────────── */
  .steps { display: flex; flex-direction: column; gap: 0; margin-top: 16px; }

  .step {
    display: grid;
    grid-template-columns: 64px 1fr;
    gap: 0;
  }

  .step-left {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .step-num {
    width: 40px; height: 40px;
    border-radius: 50%;
    background: var(--bg3);
    border: 2px solid var(--green);
    display: flex; align-items: center; justify-content: center;
    font-family: var(--font-head);
    font-size: 13px;
    color: var(--green);
    text-shadow: var(--glow-g);
    box-shadow: var(--glow-g);
    flex-shrink: 0;
    position: relative;
    z-index: 1;
  }
  .step-line {
    flex: 1;
    width: 2px;
    background: linear-gradient(to bottom, var(--green), var(--border));
    margin-top: 4px;
    position: relative;
    overflow: hidden;
  }
  .step-line::after {
    content: '';
    position: absolute;
    width: 100%; height: 40%;
    background: linear-gradient(to bottom, transparent, var(--green), transparent);
    animation: flowDown 2s ease-in-out infinite;
  }
  .step:last-child .step-line { background: none; }

  .step-content {
    padding: 0 0 48px 20px;
  }
  .step-title {
    font-family: var(--font-head);
    font-size: 12px;
    letter-spacing: .12em;
    color: #fff;
    text-transform: uppercase;
    margin-bottom: 12px;
    margin-top: 8px;
  }

  .code-block {
    background: #020204;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    font-family: var(--font-mono);
    font-size: 13px;
  }
  .code-block-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
  }
  .code-dots { display: flex; gap: 6px; }
  .code-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
  }
  .code-dot.r { background: #ff5f57; }
  .code-dot.y { background: #ffbd2e; }
  .code-dot.g { background: #28ca41; }
  .code-lang {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: .1em;
  }
  .code-block pre {
    padding: 16px;
    overflow-x: auto;
    line-height: 1.6;
  }
  .code-block code { color: var(--text); }
  .tok-cmd   { color: var(--green); }
  .tok-arg   { color: var(--cyan); }
  .tok-cmt   { color: var(--muted); font-style: italic; }
  .tok-str   { color: var(--yellow); }
  .tok-key   { color: var(--orange); }
  .tok-val   { color: var(--purple); }

  .env-block {
    background: #020204;
    border: 1px solid var(--border);
    border-left: 3px solid var(--green);
    border-radius: 0 6px 6px 0;
    padding: 16px;
    font-family: var(--font-mono);
    font-size: 12.5px;
    margin-top: 12px;
    line-height: 1.8;
  }

  .prereq-grid { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 12px; }
  .prereq-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 16px;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text);
    transition: all .2s;
  }
  .prereq-pill:hover { border-color: var(--cyan); color: var(--cyan); }
  .prereq-pill .icon { font-size: 16px; }

  .tip-box {
    display: flex;
    gap: 12px;
    padding: 14px 16px;
    background: rgba(255,224,51,.04);
    border: 1px solid rgba(255,224,51,.2);
    border-left: 3px solid var(--yellow);
    border-radius: 0 6px 6px 0;
    margin-top: 12px;
    font-size: 12.5px;
    color: var(--text);
  }
  .tip-box .tip-icon { font-size: 16px; flex-shrink: 0; margin-top: 2px; }

  /* ────────────── API REFERENCE ────────────── */
  .endpoint-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 20px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px 6px 0 0;
    border-bottom: none;
    margin-top: 32px;
  }
  .method {
    font-family: var(--font-head);
    font-size: 11px;
    letter-spacing: .1em;
    padding: 4px 10px;
    border-radius: 3px;
  }
  .method.post { background: rgba(0,255,136,.15); color: var(--green); border: 1px solid rgba(0,255,136,.3); }
  .method.get  { background: rgba(0,212,255,.1); color: var(--cyan); border: 1px solid rgba(0,212,255,.3); }
  .endpoint-path {
    font-family: var(--font-mono);
    font-size: 15px;
    color: #fff;
  }
  .endpoint-desc { font-size: 12px; color: var(--muted); margin-left: auto; }

  .api-table-wrap {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 0 0 6px 6px;
    overflow: hidden;
  }
  .api-table { width: 100%; border-collapse: collapse; }
  .api-table th {
    text-align: left;
    padding: 10px 16px;
    font-family: var(--font-mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .12em;
    color: var(--muted);
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
  }
  .api-table td {
    padding: 10px 16px;
    font-family: var(--font-mono);
    font-size: 12px;
    border-bottom: 1px solid rgba(255,255,255,.03);
    vertical-align: top;
  }
  .api-table tr:last-child td { border-bottom: none; }
  .api-table tr:hover td { background: rgba(255,255,255,.015); }
  td.field { color: var(--cyan); }
  td.type  { color: var(--purple); }
  td.req   { color: var(--green); text-align: center; }
  td.nreq  { color: var(--muted); text-align: center; }

  /* ────────────── FILE STRUCTURE ────────────── */
  .tree {
    background: #020204;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    margin-top: 16px;
  }
  .tree-head {
    padding: 10px 16px;
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .tree pre {
    padding: 20px;
    font-family: var(--font-mono);
    font-size: 12.5px;
    line-height: 1.8;
    overflow-x: auto;
    color: var(--text);
  }
  .t-dir   { color: var(--cyan); }
  .t-file  { color: var(--text); }
  .t-arrow { color: var(--muted); }
  .t-cmt   { color: var(--muted); font-style: italic; }
  .t-root  { color: var(--green); }

  /* ────────────── VERDICT TERMINAL ────────────── */
  .terminal {
    background: #020204;
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin-top: 16px;
    box-shadow: 0 0 40px rgba(0,0,0,.6);
  }
  .terminal-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
  }
  .terminal-title { font-family: var(--font-mono); font-size: 12px; color: var(--muted); }
  .terminal-body { padding: 24px; font-family: var(--font-mono); font-size: 13px; line-height: 2; }

  .verdict-box {
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 24px;
  }
  .verdict-head {
    padding: 10px 20px;
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
    text-align: center;
    font-family: var(--font-head);
    font-size: 11px;
    letter-spacing: .2em;
    color: var(--cyan);
  }
  .verdict-body { padding: 0; }
  .verdict-row {
    display: grid;
    grid-template-columns: 160px 1fr auto;
    gap: 16px;
    padding: 8px 20px;
    border-bottom: 1px solid rgba(255,255,255,.03);
    font-size: 13px;
  }
  .verdict-row:last-child { border-bottom: none; }
  .verdict-row .label { color: var(--muted); }
  .verdict-row .value { color: var(--text); }
  .verdict-score { color: var(--red); font-weight: bold; }
  .verdict-badge {
    font-family: var(--font-head);
    font-size: 11px;
    letter-spacing: .1em;
    padding: 2px 10px;
    border-radius: 3px;
  }
  .verdict-badge.reject { background: rgba(255,59,92,.15); color: var(--red); border: 1px solid rgba(255,59,92,.3); }
  .verdict-badge.accept { background: rgba(0,255,136,.1); color: var(--green); border: 1px solid rgba(0,255,136,.3); }
  .verdict-badge.review { background: rgba(255,224,51,.1); color: var(--yellow); border: 1px solid rgba(255,224,51,.3); }

  .findings-list { margin-top: 8px; }
  .finding {
    display: grid;
    grid-template-columns: 90px 60px 1fr;
    gap: 12px;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,.03);
    font-size: 12.5px;
    align-items: baseline;
  }
  .finding:last-child { border-bottom: none; }
  .sev { font-family: var(--font-head); font-size: 9px; letter-spacing: .1em; padding: 2px 6px; border-radius: 2px; text-align: center; }
  .sev.crit { background: rgba(255,59,92,.15); color: var(--red); border: 1px solid rgba(255,59,92,.3); }
  .sev.high { background: rgba(255,140,66,.12); color: var(--orange); border: 1px solid rgba(255,140,66,.3); }
  .sev.med  { background: rgba(255,224,51,.08); color: var(--yellow); border: 1px solid rgba(255,224,51,.25); }
  .finding-line { color: var(--muted); font-size: 11px; }
  .finding-msg  { color: var(--text); font-size: 12px; }

  /* ────────────── CONFIG TABLE ────────────── */
  .config-table-wrap {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    margin-top: 16px;
  }
  .cfg-table { width: 100%; border-collapse: collapse; }
  .cfg-table th {
    text-align: left;
    padding: 10px 16px;
    font-family: var(--font-mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .12em;
    color: var(--muted);
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
  }
  .cfg-table td {
    padding: 10px 16px;
    font-family: var(--font-mono);
    font-size: 12px;
    border-bottom: 1px solid rgba(255,255,255,.03);
    vertical-align: top;
  }
  .cfg-table tr:last-child td { border-bottom: none; }
  .cfg-table tr:hover td { background: rgba(255,255,255,.015); }
  .cfg-var { color: var(--cyan); }
  .cfg-def { color: var(--purple); }
  .cfg-desc { color: var(--muted); }

  /* ────────────── CONTRIBUTING ────────────── */
  .contrib-wrap {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 40px;
    margin-top: 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .contrib-wrap::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at center, rgba(0,255,136,.04) 0%, transparent 70%);
  }
  .contrib-title {
    font-family: var(--font-head);
    font-size: 18px;
    letter-spacing: .1em;
    color: #fff;
    margin-bottom: 12px;
  }
  .contrib-sub { color: var(--muted); font-size: 13px; max-width: 440px; margin: 0 auto 24px; }

  /* ────────────── FOOTER ────────────── */
  .footer {
    border-top: 1px solid var(--border);
    padding: 60px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .footer-glow {
    position: absolute;
    width: 400px; height: 200px;
    background: radial-gradient(ellipse, rgba(0,255,136,.08) 0%, transparent 70%);
    top: 0; left: 50%;
    transform: translateX(-50%);
  }
  .footer-logo {
    font-family: var(--font-head);
    font-size: 20px;
    letter-spacing: .3em;
    color: var(--green);
    text-shadow: var(--glow-g);
    margin-bottom: 8px;
  }
  .footer-sub {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--muted);
    letter-spacing: .08em;
    margin-bottom: 24px;
  }
  .footer-links {
    display: flex;
    gap: 24px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 32px;
  }
  .footer-link {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--muted);
    text-decoration: none;
    letter-spacing: .08em;
    transition: color .2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .footer-link:hover { color: var(--green); }

  .footer-stack {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 40px;
  }
  .footer-tag {
    font-family: var(--font-mono);
    font-size: 11px;
    padding: 4px 12px;
    background: rgba(255,255,255,.03);
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--muted);
  }
  .footer-copy {
    font-size: 12px;
    color: rgba(74,85,104,.6);
  }
  .footer-copy a { color: var(--muted); text-decoration: none; }
  .footer-copy a:hover { color: var(--green); }

  /* ────────────── MISC ────────────── */
  a { color: var(--green); text-decoration: none; }
  a:hover { text-decoration: underline; }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--muted); }

  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
  .cursor::after { content: '▋'; animation: blink 1s step-end infinite; margin-left: 2px; font-size: .8em; }
</style>
</head>
<body>

<!-- ═══════════════ HERO ═══════════════ -->
<section class="hero">
  <div class="hero-grid"></div>
  <div class="hero-glow"></div>
  <div class="hero-corner tl"></div>
  <div class="hero-corner tr"></div>
  <div class="hero-corner bl"></div>
  <div class="hero-corner br"></div>

  <div class="badge-row">
    <span class="badge blue">🐍 Python 3.10+</span>
    <span class="badge teal">⚡ FastAPI 0.135+</span>
    <span class="badge dark">▲ Next.js 16+</span>
    <span class="badge purple">🔗 LangChain Multi-Agent</span>
    <span class="badge orange">🟢 Ollama Local LLM</span>
    <span class="badge green">MIT License</span>
  </div>

  <div class="logo-ascii">
 ██████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║
██║     ██║   ██║██║  ██║█████╗  ███████╗██║     ███████║██╔██╗ ██║
██║     ██║   ██║██║  ██║██╔══╝  ╚════██║██║     ██╔══██║██║╚██╗██║
╚██████╗╚██████╔╝██████╔╝███████╗███████║╚██████╗██║  ██║██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝</div>

  <p class="hero-tagline">Drop your code. Get a verdict. Ship with confidence.</p>
  <p class="hero-sub">
    <span>4 AI agents</span> · <span>1 quality score</span> · <span>Zero excuses</span> for shipping broken code.
  </p>

  <div class="hero-stat-row">
    <div class="hero-stat"><span class="num">4</span><span class="lbl">Parallel Agents</span></div>
    <div class="hero-stat"><span class="num">&lt;60s</span><span class="lbl">Analysis Time</span></div>
    <div class="hero-stat"><span class="num">100</span><span class="lbl">Quality Score</span></div>
    <div class="hero-stat"><span class="num">4</span><span class="lbl">Report Formats</span></div>
  </div>
</section>

<div class="divider"></div>

<!-- ═══════════════ WHAT IS CODESCAN ═══════════════ -->
<div class="section">
  <div class="section-label">01 &nbsp;Overview</div>
  <h2 class="section-title">What is <span class="accent">CodeScan</span>?</h2>

  <p class="intro-desc">
    <strong>CodeScan</strong> is a full-stack, AI-powered code review platform that runs your source code through a
    <strong>parallel multi-agent pipeline</strong> — simultaneously hunting bugs, security holes, performance bottlenecks,
    and style violations — all in under 60 seconds.
  </p>
  <p class="intro-desc">
    You get a <strong>quality score out of 100</strong>, a clear verdict, line-level findings with actionable fixes,
    and downloadable reports. No meetings. No waiting. Just answers.
  </p>

  <div class="intro-grid">
    <div class="intro-card">
      <span class="icon">📊</span>
      <h3>Quality Score</h3>
      <p>Weighted 0–100 score with per-agent sub-scores and a clear ACCEPT / REVIEW / REJECT verdict.</p>
    </div>
    <div class="intro-card">
      <span class="icon">⚡</span>
      <h3>Parallel Execution</h3>
      <p>All 4 agents run simultaneously via ThreadPoolExecutor. Because waiting is for pipelines that don't respect your time.</p>
    </div>
    <div class="intro-card">
      <span class="icon">🧹</span>
      <h3>Smart Deduplication</h3>
      <p>Cross-agent findings are intelligently merged and deduplicated. Zero noise, maximum signal.</p>
    </div>
    <div class="intro-card">
      <span class="icon">📄</span>
      <h3>Multi-Format Reports</h3>
      <p>Export findings as JSON, Markdown, PDF, and SARIF for seamless CI/CD integration.</p>
    </div>
    <div class="intro-card">
      <span class="icon">🌐</span>
      <h3>Real-Time Dashboard</h3>
      <p>Pipeline tracker, findings panel, and file risk heatmap — watch the analysis unfold live.</p>
    </div>
    <div class="intro-card">
      <span class="icon">🔌</span>
      <h3>Pluggable LLMs</h3>
      <p>Ollama · Gemini · Groq · OpenAI. Swap your backend with a single environment variable.</p>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ PIPELINE ═══════════════ -->
<div class="section">
  <div class="section-label">02 &nbsp;Architecture</div>
  <h2 class="section-title">The <span class="accent-c">Pipeline</span></h2>

  <div class="pipeline-wrap">
    <div class="pipe-flow">
      <div class="pipe-input">⌨ &nbsp;YOUR CODE</div>

      <div class="pipe-arrow"></div>
      <div class="pipe-arrow-down"></div>

      <div class="agents-row">
        <div class="agent-card bug">
          <span class="agent-icon">🐛</span>
          <span class="agent-name">Bug Agent</span>
          <div class="agent-tags">
            <span class="agent-tag">Logic errors</span>
            <span class="agent-tag">Null dereference</span>
            <span class="agent-tag">Off-by-one</span>
            <span class="agent-tag">Type mismatches</span>
          </div>
        </div>
        <div class="agent-card sec">
          <span class="agent-icon">🔒</span>
          <span class="agent-name">Security Agent</span>
          <div class="agent-tags">
            <span class="agent-tag">OWASP Top 10</span>
            <span class="agent-tag">SQL injection</span>
            <span class="agent-tag">Hardcoded keys</span>
            <span class="agent-tag">Weak crypto</span>
          </div>
        </div>
        <div class="agent-card perf">
          <span class="agent-icon">⚡</span>
          <span class="agent-name">Perf Agent</span>
          <div class="agent-tags">
            <span class="agent-tag">O(n²) loops</span>
            <span class="agent-tag">Memory leaks</span>
            <span class="agent-tag">Blocking I/O</span>
            <span class="agent-tag">N+1 DB queries</span>
          </div>
        </div>
        <div class="agent-card style">
          <span class="agent-icon">🎨</span>
          <span class="agent-name">Style Agent</span>
          <div class="agent-tags">
            <span class="agent-tag">PEP 8</span>
            <span class="agent-tag">Dead code</span>
            <span class="agent-tag">Missing docs</span>
            <span class="agent-tag">Complexity</span>
          </div>
        </div>
      </div>

      <div class="pipe-arrow-down"></div>
      <div class="pipe-arrow"></div>

      <div class="pipe-engine">
        <span class="pipe-engine-icon">🧮</span>
        <div class="pipe-engine-label">
          Aggregator + Deduplicator<br>
          <span>Smart merge · no duplicate noise · weighted scoring</span>
        </div>
      </div>

      <div class="pipe-arrow"></div>
      <div class="pipe-arrow-down"></div>

      <div class="pipe-output">
        <div class="output-pill">
          <span class="pill-icon">📊</span>
          Score &amp; Verdict
          <div class="pill-label">0–100 · ACCEPT/REVIEW/REJECT</div>
        </div>
        <div class="output-pill">
          <span class="pill-icon">🔍</span>
          Line Findings
          <div class="pill-label">File · line · fix suggestion</div>
        </div>
        <div class="output-pill">
          <span class="pill-icon">📄</span>
          Reports
          <div class="pill-label">JSON · MD · PDF · SARIF</div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ WHAT GETS CAUGHT ═══════════════ -->
<div class="section">
  <div class="section-label">03 &nbsp;Detection</div>
  <h2 class="section-title">What Gets <span class="accent">Caught</span></h2>

  <div class="agents-detail">
    <div class="agent-detail-row bug">
      <div class="adr-head">
        <span class="adr-icon">🐛</span>
        <span class="adr-name">Bug Detection</span>
      </div>
      <div class="adr-tags">
        <span class="adr-tag">Logic errors</span>
        <span class="adr-tag">Null dereferences</span>
        <span class="adr-tag">Unhandled exceptions</span>
        <span class="adr-tag">Off-by-one</span>
        <span class="adr-tag">Type mismatches</span>
      </div>
    </div>
    <div class="agent-detail-row sec">
      <div class="adr-head">
        <span class="adr-icon">🔒</span>
        <span class="adr-name">Security Audit</span>
      </div>
      <div class="adr-tags">
        <span class="adr-tag">OWASP Top 10</span>
        <span class="adr-tag">SQL / command injection</span>
        <span class="adr-tag">Weak crypto</span>
        <span class="adr-tag">Hardcoded secrets</span>
        <span class="adr-tag">CVEs</span>
      </div>
    </div>
    <div class="agent-detail-row perf">
      <div class="adr-head">
        <span class="adr-icon">⚡</span>
        <span class="adr-name">Performance</span>
      </div>
      <div class="adr-tags">
        <span class="adr-tag">O(n²) loops</span>
        <span class="adr-tag">Memory leaks</span>
        <span class="adr-tag">Blocking I/O</span>
        <span class="adr-tag">N+1 DB queries</span>
        <span class="adr-tag">Unnecessary allocations</span>
      </div>
    </div>
    <div class="agent-detail-row style">
      <div class="adr-head">
        <span class="adr-icon">🎨</span>
        <span class="adr-name">Style &amp; Quality</span>
      </div>
      <div class="adr-tags">
        <span class="adr-tag">PEP 8</span>
        <span class="adr-tag">Naming conventions</span>
        <span class="adr-tag">Dead code</span>
        <span class="adr-tag">Missing docs</span>
        <span class="adr-tag">Cyclomatic complexity</span>
      </div>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ TECH STACK ═══════════════ -->
<div class="section">
  <div class="section-label">04 &nbsp;Stack</div>
  <h2 class="section-title">Tech <span class="accent-c">Stack</span></h2>

  <div class="stack-grid">
    <div class="stack-col">
      <div class="stack-col-head be">⚙ &nbsp;Backend</div>
      <div class="stack-item"><span class="stack-name">FastAPI</span><span class="stack-role">REST API + SSE streaming</span></div>
      <div class="stack-item"><span class="stack-name">LangChain</span><span class="stack-role">LLM abstraction layer</span></div>
      <div class="stack-item"><span class="stack-name">ThreadPoolExecutor</span><span class="stack-role">Parallel agent execution</span></div>
      <div class="stack-item"><span class="stack-name">Pydantic</span><span class="stack-role">Finding schema validation</span></div>
      <div class="stack-item"><span class="stack-name">pylint / flake8</span><span class="stack-role">Style static analysis</span></div>
      <div class="stack-item"><span class="stack-name">bandit</span><span class="stack-role">Security static scan</span></div>
      <div class="stack-item"><span class="stack-name">radon</span><span class="stack-role">Cyclomatic complexity</span></div>
      <div class="stack-item"><span class="stack-name">semgrep</span><span class="stack-role">Pattern-based vuln detection</span></div>
      <div class="stack-item"><span class="stack-name">ReportLab</span><span class="stack-role">PDF report generation</span></div>
    </div>
    <div class="stack-col">
      <div class="stack-col-head fe">◈ &nbsp;Frontend</div>
      <div class="stack-item"><span class="stack-name">Next.js 16</span><span class="stack-role">App Router, SSR</span></div>
      <div class="stack-item"><span class="stack-name">TypeScript</span><span class="stack-role">End-to-end type safety</span></div>
      <div class="stack-item"><span class="stack-name">Tailwind CSS</span><span class="stack-role">Dark-first UI system</span></div>
      <div class="stack-item"><span class="stack-name">SSE Hook</span><span class="stack-role">Real-time pipeline tracking</span></div>
    </div>
    <div class="stack-col">
      <div class="stack-col-head llm">🤖 &nbsp;LLM Providers</div>
      <div class="stack-item">
        <span class="stack-name"><span class="llm-dot green"></span>Ollama</span>
        <span class="llm-rec">recommended</span>
      </div>
      <div class="stack-item"><span class="stack-name"><span class="llm-dot blue"></span>Google Gemini</span><span class="stack-role">Cloud API</span></div>
      <div class="stack-item"><span class="stack-name"><span class="llm-dot orange"></span>Groq</span><span class="stack-role">Ultra-fast inference</span></div>
      <div class="stack-item"><span class="stack-name"><span class="llm-dot white"></span>OpenAI</span><span class="stack-role">GPT-4 series</span></div>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ GETTING STARTED ═══════════════ -->
<div class="section">
  <div class="section-label">05 &nbsp;Setup</div>
  <h2 class="section-title">Getting <span class="accent">Started</span></h2>

  <p style="color:var(--muted);margin-bottom:32px;font-size:13px;">Prerequisites before you begin:</p>
  <div class="prereq-grid">
    <div class="prereq-pill"><span class="icon">🐍</span> Python 3.10+</div>
    <div class="prereq-pill"><span class="icon">📦</span> Node.js 18+</div>
    <div class="prereq-pill"><span class="icon">📜</span> Poetry</div>
    <div class="prereq-pill"><span class="icon">🤖</span> Ollama (or API key)</div>
  </div>

  <div style="margin-top:48px;" class="steps">
    <!-- Step 1 -->
    <div class="step">
      <div class="step-left">
        <div class="step-num">1</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <div class="step-title">Clone the repository</div>
        <div class="code-block">
          <div class="code-block-head">
            <div class="code-dots"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
            <span class="code-lang">bash</span>
          </div>
          <pre><code><span class="tok-cmd">git</span> <span class="tok-arg">clone</span> https://github.com/AadiBurande/code-review-assistant.git
<span class="tok-cmd">cd</span> code-review-assistant</code></pre>
        </div>
      </div>
    </div>

    <!-- Step 2 -->
    <div class="step">
      <div class="step-left">
        <div class="step-num">2</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <div class="step-title">Backend setup</div>
        <div class="code-block">
          <div class="code-block-head">
            <div class="code-dots"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
            <span class="code-lang">bash</span>
          </div>
          <pre><code><span class="tok-cmd">cd</span> backend
<span class="tok-cmd">poetry</span> <span class="tok-arg">install</span>
<span class="tok-cmd">cp</span> .env.example .env</code></pre>
        </div>
        <div class="env-block">
<span class="tok-cmt"># ── Pick ONE LLM Provider ────────────────────────</span>
<span class="tok-key">LLM_PROVIDER</span>=<span class="tok-val">ollama</span>          <span class="tok-cmt"># free · runs locally · recommended</span>
<span class="tok-key">OLLAMA_MODEL</span>=<span class="tok-val">qwen2.5-coder:7b-instruct-q4_K_M</span>

<span class="tok-cmt"># LLM_PROVIDER=gemini</span>
<span class="tok-cmt"># GEMINI_API_KEY=your_key_here</span>

<span class="tok-cmt"># LLM_PROVIDER=groq</span>
<span class="tok-cmt"># GROQ_API_KEY=your_key_here</span>

<span class="tok-cmt"># LLM_PROVIDER=openai</span>
<span class="tok-cmt"># OPENAI_API_KEY=your_key_here</span>
<span class="tok-cmt"># ─────────────────────────────────────────────────</span>
        </div>
      </div>
    </div>

    <!-- Step 3 -->
    <div class="step">
      <div class="step-left">
        <div class="step-num">3</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <div class="step-title">Frontend setup</div>
        <div class="code-block">
          <div class="code-block-head">
            <div class="code-dots"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
            <span class="code-lang">bash</span>
          </div>
          <pre><code><span class="tok-cmd">cd</span> ../frontend
<span class="tok-cmd">npm</span> <span class="tok-arg">install</span></code></pre>
        </div>
      </div>
    </div>

    <!-- Step 4 -->
    <div class="step">
      <div class="step-left">
        <div class="step-num">4</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <div class="step-title">Launch</div>
        <div class="code-block">
          <div class="code-block-head">
            <div class="code-dots"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
            <span class="code-lang">bash</span>
          </div>
          <pre><code><span class="tok-cmt"># Terminal 1 — API server</span>
<span class="tok-cmd">cd</span> backend
<span class="tok-cmd">poetry</span> <span class="tok-arg">run</span> uvicorn main:app --reload --port 8000 --reload-exclude <span class="tok-str">"temp_uploads"</span>

<span class="tok-cmt"># Terminal 2 — Web dashboard</span>
<span class="tok-cmd">cd</span> frontend
<span class="tok-cmd">npm</span> <span class="tok-arg">run</span> dev</code></pre>
        </div>
        <div class="tip-box">
          <span class="tip-icon">⚠️</span>
          <span>Always use <code style="color:var(--yellow)">--reload-exclude "temp_uploads"</code>. Without it, Uvicorn's file watcher sees uploaded files being written mid-analysis and restarts the server, killing the pipeline. Open <strong style="color:var(--green)">http://localhost:3000</strong> once both processes are running.</span>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ API REFERENCE ═══════════════ -->
<div class="section">
  <div class="section-label">06 &nbsp;API</div>
  <h2 class="section-title">API <span class="accent-c">Reference</span></h2>

  <!-- POST /analyze -->
  <div class="endpoint-header">
    <span class="method post">POST</span>
    <span class="endpoint-path">/analyze</span>
    <span class="endpoint-desc">Submit a file for full multi-agent review</span>
  </div>
  <div class="api-table-wrap">
    <table class="api-table">
      <thead>
        <tr><th>Field</th><th>Type</th><th>Req</th><th>Description</th></tr>
      </thead>
      <tbody>
        <tr><td class="field">file</td><td class="type">File</td><td class="req">✓</td><td>Source file or .zip project</td></tr>
        <tr><td class="field">language</td><td class="type">string</td><td class="req">✓</td><td>python · javascript · java</td></tr>
        <tr><td class="field">project_name</td><td class="type">string</td><td class="nreq">—</td><td>Label for the report (default: unnamed_project)</td></tr>
      </tbody>
    </table>
  </div>

  <div class="code-block" style="margin-top:16px;">
    <div class="code-block-head">
      <div class="code-dots"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
      <span class="code-lang">json — Response</span>
    </div>
    <pre><code>{
  <span class="tok-key">"job_id"</span>:   <span class="tok-str">"abc123"</span>,
  <span class="tok-key">"score"</span>:    <span class="tok-val">13.5</span>,
  <span class="tok-key">"verdict"</span>:  <span class="tok-str">"REJECT"</span>,  <span class="tok-cmt">// "ACCEPT" | "REVIEW" | "REJECT"</span>
  <span class="tok-key">"findings"</span>: [{
    <span class="tok-key">"agent"</span>:      <span class="tok-str">"security"</span>,
    <span class="tok-key">"severity"</span>:   <span class="tok-str">"HIGH"</span>,  <span class="tok-cmt">// CRITICAL | HIGH | MEDIUM | LOW | INFO</span>
    <span class="tok-key">"file"</span>:       <span class="tok-str">"app/auth.py"</span>,
    <span class="tok-key">"line"</span>:       <span class="tok-val">42</span>,
    <span class="tok-key">"message"</span>:    <span class="tok-str">"Hardcoded API key detected in variable `secret`"</span>,
    <span class="tok-key">"suggestion"</span>: <span class="tok-str">"Use os.environ or a secrets manager instead."</span>
  }],
  <span class="tok-key">"summary"</span>: { <span class="tok-key">"total"</span>: <span class="tok-val">38</span>, <span class="tok-key">"bugs"</span>: <span class="tok-val">13</span>, <span class="tok-key">"security"</span>: <span class="tok-val">12</span>, <span class="tok-key">"performance"</span>: <span class="tok-val">5</span>, <span class="tok-key">"style"</span>: <span class="tok-val">11</span> },
  <span class="tok-key">"reports"</span>:  {
    <span class="tok-key">"markdown_url"</span>: <span class="tok-str">"/reports/abc123.md"</span>,
    <span class="tok-key">"pdf_url"</span>:      <span class="tok-str">"/reports/abc123.pdf"</span>,
    <span class="tok-key">"sarif_url"</span>:    <span class="tok-str">"/reports/abc123.sarif"</span>,
    <span class="tok-key">"json_url"</span>:     <span class="tok-str">"/reports/abc123.json"</span>
  }
}</code></pre>
  </div>

  <!-- GET /status -->
  <div class="endpoint-header">
    <span class="method get">GET</span>
    <span class="endpoint-path">/status/{job_id}</span>
    <span class="endpoint-desc">Real-time pipeline status</span>
  </div>
  <div class="api-table-wrap" style="border-radius:0 0 6px 6px;">
    <div class="code-block" style="border:none;border-radius:0;">
      <pre><code>{
  <span class="tok-key">"job_id"</span>:      <span class="tok-str">"abc123"</span>,
  <span class="tok-key">"status"</span>:      <span class="tok-str">"running"</span>,  <span class="tok-cmt">// "queued" | "running" | "complete" | "failed"</span>
  <span class="tok-key">"stage"</span>:       <span class="tok-str">"security_agent"</span>,
  <span class="tok-key">"progress"</span>:    <span class="tok-val">60</span>,
  <span class="tok-key">"message"</span>:     <span class="tok-str">"Running security audit..."</span>,
  <span class="tok-key">"eta_seconds"</span>: <span class="tok-val">12</span>
}</code></pre>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ FILE STRUCTURE ═══════════════ -->
<div class="section">
  <div class="section-label">07 &nbsp;Structure</div>
  <h2 class="section-title">Project <span class="accent">Structure</span></h2>

  <div class="tree">
    <div class="tree-head">📁 &nbsp;code-review-assistant/</div>
    <pre><code><span class="t-root">code-review-assistant/</span>
│
├── <span class="t-dir">backend/</span>
│   ├── <span class="t-file">main.py</span>                  <span class="t-cmt">← FastAPI app + all endpoints</span>
│   ├── <span class="t-file">agents.py</span>                <span class="t-cmt">← Bug / Security / Perf / Style agents</span>
│   ├── <span class="t-file">langgraph_pipeline.py</span>    <span class="t-cmt">← Pipeline orchestration</span>
│   ├── <span class="t-file">aggregator.py</span>            <span class="t-cmt">← Finding dedup + weighted scoring</span>
│   ├── <span class="t-file">analyzers.py</span>             <span class="t-cmt">← Static analysis runners</span>
│   ├── <span class="t-file">validators.py</span>            <span class="t-cmt">← Finding validation + noise filter</span>
│   ├── <span class="t-file">prompts.py</span>               <span class="t-cmt">← All agent system prompts</span>
│   ├── <span class="t-file">pdf_generator.py</span>         <span class="t-cmt">← PDF report (ReportLab)</span>
│   ├── <span class="t-file">.env.example</span>             <span class="t-cmt">← Environment variable template</span>
│   └── <span class="t-dir">tests/</span>                   <span class="t-cmt">← Integration + accuracy tests</span>
│
├── <span class="t-dir">frontend/</span>
│   ├── <span class="t-dir">app/</span>
│   │   ├── <span class="t-file">page.tsx</span>               <span class="t-cmt">← Upload landing page</span>
│   │   ├── <span class="t-dir">dashboard/[jobId]/</span>     <span class="t-cmt">← Real-time pipeline tracker</span>
│   │   └── <span class="t-dir">api/backend/</span>           <span class="t-cmt">← Next.js → FastAPI proxy</span>
│   ├── <span class="t-dir">components/</span>
│   │   ├── <span class="t-file">upload/DropZone.tsx</span>
│   │   ├── <span class="t-file">pipeline/PipelineTracker.tsx</span>
│   │   ├── <span class="t-file">score/ScoreGauge.tsx</span>
│   │   ├── <span class="t-file">findings/FindingsPanel.tsx</span>
│   │   └── <span class="t-file">heatmap/FileHeatmap.tsx</span>
│   └── <span class="t-dir">lib/</span>
│       ├── <span class="t-file">api.ts</span>                 <span class="t-cmt">← Typed API client</span>
│       └── <span class="t-file">useAnalysisStatus.ts</span>   <span class="t-cmt">← SSE pipeline hook</span>
│
├── <span class="t-dir">temp_uploads/</span>              <span class="t-cmt">← Auto-created · gitignored</span>
└── <span class="t-dir">reports/</span>                   <span class="t-cmt">← Auto-created · gitignored</span></code></pre>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ SAMPLE VERDICT ═══════════════ -->
<div class="section">
  <div class="section-label">08 &nbsp;Output</div>
  <h2 class="section-title">Sample <span class="accent">Verdict</span></h2>

  <div class="terminal">
    <div class="terminal-bar">
      <div class="code-dots"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
      <span class="terminal-title">codescan — analysis complete</span>
      <span style="font-family:var(--font-mono);font-size:11px;color:var(--green);">● DONE</span>
    </div>
    <div class="terminal-body">
      <div class="verdict-box">
        <div class="verdict-head">CODESCAN — ANALYSIS COMPLETE</div>
        <div class="verdict-body">
          <div class="verdict-row">
            <span class="label">Project</span>
            <span class="value">my_service</span>
          </div>
          <div class="verdict-row">
            <span class="label">Language</span>
            <span class="value">Python</span>
          </div>
          <div class="verdict-row">
            <span class="label">Score</span>
            <span class="verdict-score">13.5 / 100</span>
            <span class="verdict-badge reject">✕ REJECT</span>
          </div>
          <div class="verdict-row">
            <span class="label">🐛 Bugs</span>
            <span class="value" style="color:var(--red)">13</span>
          </div>
          <div class="verdict-row">
            <span class="label">🔒 Security</span>
            <span class="value" style="color:var(--orange)">12</span>
          </div>
          <div class="verdict-row">
            <span class="label">⚡ Performance</span>
            <span class="value" style="color:var(--yellow)">5</span>
          </div>
          <div class="verdict-row">
            <span class="label">🎨 Style</span>
            <span class="value" style="color:var(--purple)">11</span>
          </div>
          <div class="verdict-row">
            <span class="label">Total findings</span>
            <span class="value">38 (deduped)</span>
          </div>
        </div>
      </div>

      <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:.1em;">TOP CRITICAL FINDINGS</div>
      <div class="findings-list">
        <div class="finding">
          <span class="sev crit">CRITICAL</span>
          <span class="finding-line">Line 42</span>
          <span class="finding-msg">Hardcoded API key detected in variable <code style="color:var(--cyan)">`secret`</code></span>
        </div>
        <div class="finding">
          <span class="sev high">HIGH</span>
          <span class="finding-line">Line 87</span>
          <span class="finding-msg">Unhandled IndexError — list may be empty</span>
        </div>
        <div class="finding">
          <span class="sev high">HIGH</span>
          <span class="finding-line">Line 103</span>
          <span class="finding-msg">SQL query via string concat → injection risk</span>
        </div>
        <div class="finding">
          <span class="sev med">MEDIUM</span>
          <span class="finding-line">Line 56</span>
          <span class="finding-msg">N+1 query inside loop — use batch fetch</span>
        </div>
        <div class="finding">
          <span class="sev med">MEDIUM</span>
          <span class="finding-line">Line 99</span>
          <span class="finding-msg">O(n²) nested loop — replace with set lookup</span>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ CONFIG ═══════════════ -->
<div class="section">
  <div class="section-label">09 &nbsp;Config</div>
  <h2 class="section-title">Configuration <span class="accent-c">Reference</span></h2>

  <div class="config-table-wrap">
    <table class="cfg-table">
      <thead>
        <tr><th>Variable</th><th>Default</th><th>Description</th></tr>
      </thead>
      <tbody>
        <tr><td class="cfg-var">LLM_PROVIDER</td><td class="cfg-def">ollama</td><td class="cfg-desc">ollama · gemini · groq · openai</td></tr>
        <tr><td class="cfg-var">OLLAMA_MODEL</td><td class="cfg-def">qwen2.5-coder:7b-instruct-q4_K_M</td><td class="cfg-desc">Model name for Ollama</td></tr>
        <tr><td class="cfg-var">GEMINI_API_KEY</td><td class="cfg-def">—</td><td class="cfg-desc">Google Gemini API key</td></tr>
        <tr><td class="cfg-var">GROQ_API_KEY</td><td class="cfg-def">—</td><td class="cfg-desc">Groq Cloud API key</td></tr>
        <tr><td class="cfg-var">OPENAI_API_KEY</td><td class="cfg-def">—</td><td class="cfg-desc">OpenAI API key</td></tr>
        <tr><td class="cfg-var">MAX_FILE_SIZE_MB</td><td class="cfg-def">10</td><td class="cfg-desc">Upload size limit in MB</td></tr>
        <tr><td class="cfg-var">PLAGIARISM_THRESHOLD</td><td class="cfg-def">65</td><td class="cfg-desc">Score above which submission is blocked</td></tr>
        <tr><td class="cfg-var">TEMP_UPLOAD_DIR</td><td class="cfg-def">temp_uploads</td><td class="cfg-desc">Staging directory for uploads</td></tr>
        <tr><td class="cfg-var">REPORTS_DIR</td><td class="cfg-def">reports</td><td class="cfg-desc">Output directory for generated reports</td></tr>
      </tbody>
    </table>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ CONTRIBUTING ═══════════════ -->
<div class="section">
  <div class="section-label">10 &nbsp;Contributing</div>
  <h2 class="section-title">Get <span class="accent">Involved</span></h2>

  <div class="contrib-wrap">
    <div class="contrib-title">Bug reports, new agent ideas &amp; language support PRs are welcome.</div>
    <p class="contrib-sub">Please open an Issue first for significant changes so we can align before you invest time building.</p>

    <div class="code-block" style="text-align:left;max-width:520px;margin:0 auto;">
      <div class="code-block-head">
        <div class="code-dots"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
        <span class="code-lang">bash</span>
      </div>
      <pre><code><span class="tok-cmt"># 1. Fork &amp; clone your fork</span>
<span class="tok-cmt"># 2. Create a feature branch</span>
<span class="tok-cmd">git</span> <span class="tok-arg">checkout</span> -b feat/add-rust-support

<span class="tok-cmt"># 3. Make your changes + add tests</span>
<span class="tok-cmt"># 4. Push and open a PR</span>
<span class="tok-cmd">git</span> <span class="tok-arg">push</span> origin feat/add-rust-support</code></pre>
    </div>
  </div>
</div>

<div class="divider"></div>

<!-- ═══════════════ FOOTER ═══════════════ -->
<footer class="footer">
  <div class="footer-glow"></div>

  <div class="footer-logo">CODESCAN</div>
  <div class="footer-sub">because code review shouldn't require a meeting</div>

  <div class="footer-stack">
    <span class="footer-tag">⚡ FastAPI</span>
    <span class="footer-tag">▲ Next.js</span>
    <span class="footer-tag">🔗 LangChain</span>
    <span class="footer-tag">🟢 Ollama</span>
  </div>

  <div class="footer-links">
    <a href="https://github.com/AadiBurande/code-review-assistant" class="footer-link">⌥ GitHub</a>
    <a href="#" class="footer-link">📄 Docs</a>
    <a href="#" class="footer-link">🐛 Issues</a>
    <a href="#" class="footer-link">💬 Discussions</a>
  </div>

  <div class="footer-copy">
    MIT License &nbsp;©&nbsp;
    <a href="https://github.com/AadiBurande">Aadi Burande</a>
  </div>
</footer>

</body>
</html>