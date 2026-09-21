from __future__ import annotations

import streamlit as st

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
    --sige-paper: #F2F3EF;
    --sige-ink: #16232E;
    --sige-blueprint: #2B5D8C;
    --sige-blueprint-soft: #E4ECF2;
    --sige-redline: #B8752B;
    --sige-redline-soft: #F6EBDC;
    --sige-border: #CDD3CD;
}

.stApp {
    background-color: var(--sige-paper);
    background-image:
        linear-gradient(var(--sige-border) 1px, transparent 1px),
        linear-gradient(90deg, var(--sige-border) 1px, transparent 1px);
    background-size: 28px 28px;
    background-position: -1px -1px;
}
.stApp, .stMarkdown, .stText, p, span, label, div[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--sige-ink);
}
h1, h2, h3, .sige-title, div[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--sige-ink) !important;
}
.sige-mono, code, div[data-testid="stDataFrame"] { font-family: 'IBM Plex Mono', monospace; }

.sige-title { font-size: 1.7rem; font-weight: 700; margin-bottom: 0.1rem; letter-spacing: -0.01em; }
.sige-subtitle { color: #5b665f; font-size: 0.92rem; margin-bottom: 1.1rem; max-width: 68ch; }

.sige-banner {
    background: var(--sige-redline-soft); border: 1px solid #e3c592; border-radius: 3px;
    padding: 0.55rem 1rem; font-size: 0.82rem; color: #6b5300; margin-bottom: 1.1rem;
    font-family: 'IBM Plex Mono', monospace;
}

.sige-stamp {
    display: inline-block; padding: 0.18rem 0.65rem; border: 1.5px solid currentColor;
    border-radius: 3px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.03em;
    font-family: 'IBM Plex Mono', monospace;
}
.sige-stamp-ok { color: var(--sige-blueprint); background: var(--sige-blueprint-soft); }
.sige-stamp-warn { color: var(--sige-redline); background: var(--sige-redline-soft); }
.sige-stamp-neutral { color: #555; background: #eceeea; border-color: #ccc; }

.sige-card {
    position: relative; background: #fff; border: 1px solid var(--sige-border);
    border-radius: 3px; padding: 1rem 1.1rem;
}
.sige-card::before {
    content: "+"; position: absolute; top: -0.55rem; left: -0.5rem; font-size: 0.9rem;
    color: var(--sige-blueprint); font-family: monospace;
}

.sige-dim-divider { display: flex; align-items: center; gap: 0.4rem; margin: 1.6rem 0 0.8rem 0; }
.sige-dim-divider .line { flex: 1; height: 1px; background: var(--sige-border); position: relative; }
.sige-dim-divider .line::before, .sige-dim-divider .line::after {
    content: ""; position: absolute; top: -3px; width: 1px; height: 7px; background: var(--sige-border);
}
.sige-dim-divider .line::before { left: 0; } .sige-dim-divider .line::after { right: 0; }
.sige-dim-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #5b665f;
    letter-spacing: 0.03em;
}

.sige-feed-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0.5rem; border-bottom: 1px solid var(--sige-border); font-size: 0.86rem;
    position: relative; overflow: hidden;
}
.sige-feed-row .codigo { font-family: 'IBM Plex Mono', monospace; font-weight: 600; }

.sige-sweep::after {
    content: ""; position: absolute; top: 0; left: -40%; height: 100%; width: 40%;
    background: linear-gradient(90deg, transparent, var(--sige-blueprint-soft) 55%, transparent);
    animation: sige-sweep-move 0.8s ease-out;
}
@keyframes sige-sweep-move {
    from { left: -40%; }
    to { left: 100%; }
}
@media (prefers-reduced-motion: reduce) {
    .sige-sweep::after { animation: none; display: none; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def mock_banner() -> None:
    st.markdown(
        '<div class="sige-banner">\u26A0 ENTORNO DE DEMOSTRACION — propiedades, direcciones y datos '
        'tecnicos 100% sinteticos.</div>',
        unsafe_allow_html=True,
    )


def title(text: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="sige-title">{text}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="sige-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def dim_divider(label: str) -> None:
    st.markdown(
        f'<div class="sige-dim-divider"><div class="line"></div>'
        f'<div class="sige-dim-label">{label}</div><div class="line"></div></div>',
        unsafe_allow_html=True,
    )


def stamp(text: str, tone: str = "neutral") -> str:
    return f'<span class="sige-stamp sige-stamp-{tone}">{text}</span>'


def pill(text: str, tone: str = "neutral") -> str:
    tone_map = {"ok": "ok", "warn": "warn", "neutral": "neutral"}
    return stamp(text, tone_map.get(tone, "neutral"))
