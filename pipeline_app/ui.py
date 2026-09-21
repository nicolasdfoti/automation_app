from __future__ import annotations

import streamlit as st

_CSS = """
<style>
:root {
    --app-accent: #2f6f4f; --app-accent-soft: #e7f2ec;
    --app-warn: #a15c00; --app-warn-soft: #fbeedd;
    --app-border: #dfe3e0;
}
.app-breadcrumbs { font-size: 0.82rem; color: #6b7570; margin-bottom: 0.4rem; }
.app-header-title { font-size: 1.6rem; font-weight: 700; margin-bottom: 0.1rem; }
.app-header-subtitle { color: #6b7570; font-size: 0.92rem; margin-bottom: 1rem; }
.app-section-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em;
    color: #6b7570; margin: 1.4rem 0 0.5rem 0; font-weight: 600; }
.app-pill { display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.app-pill-success { background: var(--app-accent-soft); color: var(--app-accent); }
.app-pill-warning { background: var(--app-warn-soft); color: var(--app-warn); }
.app-pill-neutral { background: #eef0ef; color: #555; }
.app-file-row { display: grid; grid-template-columns: 110px 1fr 140px 120px; align-items: center;
    padding: 0.4rem 0.2rem; border-bottom: 1px solid var(--app-border); font-size: 0.86rem; }
.app-file-head { font-weight: 600; color: #6b7570; font-size: 0.78rem; text-transform: uppercase; }
.app-empty { text-align: center; padding: 2.2rem 1rem; color: #6b7570; }
.app-empty-icon { font-size: 2rem; margin-bottom: 0.4rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def breadcrumbs(items: list[str]) -> None:
    st.markdown(f'<div class="app-breadcrumbs">{" &rsaquo; ".join(items)}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="app-header-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="app-header-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def section_label(text: str) -> None:
    st.markdown(f'<div class="app-section-label">{text}</div>', unsafe_allow_html=True)


def metric_row(metrics: list[dict]) -> None:
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            with st.container(border=True):
                st.caption(m["label"])
                st.markdown(f"### {m['value']}")
                if m.get("hint"):
                    st.caption(m["hint"])


def status_pill(text: str, tone: str = "neutral") -> str:
    return f'<span class="app-pill app-pill-{tone}">{text}</span>'


def button_primary(label: str, key: str | None = None, disabled: bool = False) -> bool:
    return st.button(label, key=key, disabled=disabled, type="primary", use_container_width=True)


def info_banner(text: str, tone: str = "info") -> None:
    {"danger": st.error, "warning": st.warning, "success": st.success}.get(tone, st.info)(text)


def empty_state(icon: str, title: str, desc: str) -> None:
    st.markdown(
        f'<div class="app-empty"><div class="app-empty-icon">{icon}</div>'
        f'<div style="font-weight:600;">{title}</div><div>{desc}</div></div>',
        unsafe_allow_html=True,
    )
