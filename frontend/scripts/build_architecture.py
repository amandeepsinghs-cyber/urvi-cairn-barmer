#!/usr/bin/env python3
"""Build the Urvi architecture diagrams (BL-8 / BL-10) as standalone HTML + inline SVG.

    python3 frontend/scripts/build_architecture.py

Writes four files to ``frontend/public/architecture/``:

* ``current.html`` / ``target.html``: dark theme, shown in the app's Architecture tab.
* ``current-light.html`` / ``target-light.html``: light Google Cloud style, for decks and documents.

Standards followed:

* **Icons:** only official Google Cloud icons (go/cloud-icons, H1 2026 system, copied into ``architecture_icons/``).
  Priority products use their unique icon (BigQuery, Cloud Run, Cloud Storage, Apigee, Vertex AI); every other
  product uses its category icon; Gemini uses the Gemini spark. Real third-party products shown in the customer
  architecture use their own official mark (SAP, AVEVA PI, Esri, Leaflet, OSDU); everything else (our own code,
  ONGC-internal systems, people) uses a generic single-colour glyph. The product name is always printed next to
  its icon. No ONGC logo (R-5).
* **Reading order:** left → right, users on the left. Numbered badges show the main path (① … typed question),
  lettered badges the voice path (Ⓐ …), D-badges the data path (target). Secondary flows (offline, build,
  identity) are thin and muted.
* **Layout / style:** ``architecture-diagram`` skill for the dark theme (semantic colours, 40 px grid, no
  JavaScript; hover tooltips are pure CSS). The light theme uses Google colours on white.

Re-run after changing the architecture; commit the generated HTML.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "public" / "architecture"
ICON_DIR = Path(__file__).resolve().parent / "architecture_icons"
W, H = 1460, 960

# Official icon files (go/cloud-icons). Keys are used in the diagram definitions below.
ICONS = {
    "cloud-run": "CloudRun-512-color-rgb.svg",
    "bigquery": "BigQuery-512-color.svg",
    "cloud-storage": "Cloud_Storage-512-color.svg",
    "vertex-ai": "VertexAI-512-color.svg",
    "apigee": "Apigee-512-color-rgb.svg",
    "agents": "Agents-512-color.svg",                     # category: AI Applications & Agents
    "security": "SecurityIdentity-512-color.svg",         # category: Security & Identity
    "observability": "Observability-512-color.svg",       # category: Observability
    "devops": "DevOps-512-color.svg",                     # category: DevOps
    "data-analytics": "DataAnalytics-512-color.svg",      # category: Data Analytics
    "databases": "Databases-512-color.svg",               # category: Databases
    "networking": "Networking-512-color-rgb.svg",         # category: Networking
    "gemini": "GeminiSpark.svg",                          # Gemini spark
    # Real third-party products shown in the customer architecture (official marks, unmodified, always labelled)
    "sap": "SAP.svg",                                     # SAP (open logo pack)
    "aveva": "AVEVA.svg",                                 # AVEVA (PI System), from aveva.com
    "esri": "Esri.svg",                                   # Esri globe mark, Esri blue (simple-icons)
    "leaflet": "Leaflet.svg",                             # Leaflet (open source)
    "osdu": "OSDU.png",                                   # OSDU (The Open Group), the EDP's data standard
}

# Generic single-colour glyphs (24 × 24, outline) for boxes that are not a branded product: our own code,
# ONGC-internal systems and concepts. Same style everywhere so the branded icons stand out.
_G = 'fill="none" stroke="#5f6368" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"'
GENERIC = {
    "g:person": f'<circle cx="12" cy="8" r="3.6" {_G}/><path d="M4.5 20c.8-3.8 3.9-6 7.5-6s6.7 2.2 7.5 6" {_G}/>',
    "g:badge": f'<rect x="3.5" y="5.5" width="17" height="13" rx="2" {_G}/><circle cx="9" cy="11" r="2.2" {_G}/><path d="M5.8 16c.6-1.4 1.8-2.2 3.2-2.2s2.6.8 3.2 2.2M14.5 10h3.5M14.5 13.5h3.5" {_G}/>',
    "g:browser": f'<rect x="3" y="4.5" width="18" height="15" rx="2" {_G}/><path d="M3 8.5h18M6 6.5h.01M8.5 6.5h.01" {_G}/>',
    "g:mic": f'<rect x="9" y="3.5" width="6" height="11" rx="3" {_G}/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3" {_G}/>',
    "g:pin": f'<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z" {_G}/><circle cx="12" cy="10" r="2.4" {_G}/>',
    "g:cursor": f'<path d="M5 4l6.5 16 2.2-6.8L20.5 11z" {_G}/><path d="M14 14l5 5" {_G}/>',
    "g:server": f'<rect x="4" y="4" width="16" height="7" rx="1.5" {_G}/><rect x="4" y="13" width="16" height="7" rx="1.5" {_G}/><path d="M7.5 7.5h.01M7.5 16.5h.01M11 7.5h5M11 16.5h5" {_G}/>',
    "g:insights": f'<path d="M4 20h16M6.5 16v-4M10.5 16V8M14.5 16v-6M18.5 16V5" {_G}/>',
    "g:database": f'<ellipse cx="12" cy="6" rx="7" ry="2.6" {_G}/><path d="M5 6v12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6V6M5 12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6" {_G}/>',
    "g:document": f'<path d="M7 3.5h7l4 4V20a.5.5 0 0 1-.5.5h-10.5a.5.5 0 0 1-.5-.5V4a.5.5 0 0 1 .5-.5z" {_G}/><path d="M14 3.5V8h4M9 12h6M9 15.5h6" {_G}/>',
    "g:search-doc": f'<path d="M7 3.5h7l4 4V11M6.5 3.5V20h5" {_G}/><circle cx="16" cy="16" r="3" {_G}/><path d="M18.2 18.2L20.5 20.5" {_G}/>',
    "g:memory": f'<rect x="5" y="5" width="14" height="14" rx="1.5" {_G}/><rect x="9" y="9" width="6" height="6" {_G}/><path d="M9 2.5V5M15 2.5V5M9 19v2.5M15 19v2.5M2.5 9H5M2.5 15H5M19 9h2.5M19 15h2.5" {_G}/>',
    "g:upload": f'<path d="M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4M12 15V4M7.5 8.5L12 4l4.5 4.5" {_G}/>',
    "g:flask": f'<path d="M9.5 3.5h5M10 3.5v6L4.8 18.6A1.3 1.3 0 0 0 6 20.5h12a1.3 1.3 0 0 0 1.2-1.9L14 9.5v-6M7.2 14.5h9.6" {_G}/>',
    "g:plug": f'<path d="M9 3.5v4M15 3.5v4M6.5 7.5h11V11a5.5 5.5 0 0 1-11 0zM12 16.5v4" {_G}/>',
    "g:wave": f'<path d="M3 12h2M7 8v8M11 5v14M15 8v8M19 10.5v3M21 12h0" {_G}/>',
    "g:canvas": f'<rect x="3" y="4.5" width="18" height="15" rx="2" {_G}/><path d="M6.5 16l3.5-4 3 2.5 4.5-6" {_G}/>',
}

# ----------------------------------------------------------------------------------------------- themes
THEMES = {
    "dark": {
        "font": "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace",
        "font_link": '<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">',
        "bg": "#020617", "panel": "rgba(15,23,42,.5)", "border": "#1e293b", "grid": "#1e293b",
        "under": "#0f172a", "text": "#ffffff", "sub": "#94a3b8", "alabel": "#cbd5e1", "halo": "#020617",
        "footer": "#475569", "tip_bg": "#0b1220", "tip_border": "#334155", "tip_text": "#cbd5e1", "tip_title": "#fff",
        "tile": "#f8fafc", "box_fill": "rgba(15,23,42,.25)", "big_fill": "rgba(251,191,36,.03)",
        "badge_main_fill": "#f8fafc", "badge_main_text": "#020617",
        "kind": {
            "frontend": ("rgba(8,51,68,.4)", "#22d3ee"), "backend": ("rgba(6,78,59,.4)", "#34d399"),
            "data": ("rgba(76,29,149,.4)", "#a78bfa"), "cloud": ("rgba(120,53,15,.3)", "#fbbf24"),
            "security": ("rgba(136,19,55,.4)", "#fb7185"), "ai": ("rgba(30,58,138,.45)", "#60a5fa"),
            "external": ("rgba(30,41,59,.5)", "#94a3b8"),
        },
        "color": {"cyan": "#22d3ee", "emerald": "#34d399", "blue": "#60a5fa", "violet": "#a78bfa",
                  "amber": "#fbbf24", "rose": "#fb7185", "slate": "#94a3b8", "muted": "#64748b"},
        "new": ("#064e3b", "#34d399"),
    },
    "light": {
        "font": "'Google Sans','Google Sans Text',Roboto,Arial,sans-serif",
        "font_link": '<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">',
        "bg": "#ffffff", "panel": "#ffffff", "border": "#dadce0", "grid": "#f1f3f4",
        "under": "#ffffff", "text": "#202124", "sub": "#5f6368", "alabel": "#3c4043", "halo": "#ffffff",
        "footer": "#80868b", "tip_bg": "#ffffff", "tip_border": "#dadce0", "tip_text": "#3c4043", "tip_title": "#202124",
        "tile": "#ffffff", "box_fill": "rgba(241,243,244,.35)", "big_fill": "rgba(251,188,4,.04)",
        "badge_main_fill": "#202124", "badge_main_text": "#ffffff",
        "kind": {
            "frontend": ("#e4f7fb", "#12b5cb"), "backend": ("#e6f4ea", "#188038"),
            "data": ("#f3e8fd", "#9334e6"), "cloud": ("#fef7e0", "#e37400"),
            "security": ("#fce8e6", "#d93025"), "ai": ("#e8f0fe", "#1a73e8"),
            "external": ("#f1f3f4", "#5f6368"),
        },
        "color": {"cyan": "#12b5cb", "emerald": "#188038", "blue": "#1a73e8", "violet": "#9334e6",
                  "amber": "#e37400", "rose": "#d93025", "slate": "#5f6368", "muted": "#9aa0a6"},
        "new": ("#e6f4ea", "#188038"),
    },
}


# ----------------------------------------------------------------------------------------------- icons
_icon_cache: dict[str, tuple[str, str]] = {}
_uid = 0


def _load_icon(key: str) -> tuple[str, str]:
    """(viewBox, inner markup) with <style> classes inlined as fill attributes; PNGs embedded as data URIs."""
    if key not in _icon_cache:
        if key in GENERIC:
            _icon_cache[key] = ("0 0 24 24", GENERIC[key])
            return _icon_cache[key]
        path = ICON_DIR / ICONS[key]
        if path.suffix == ".png":
            import base64
            import struct
            data = path.read_bytes()
            w, h = struct.unpack(">II", data[16:24])
            uri = "data:image/png;base64," + base64.b64encode(data).decode()
            _icon_cache[key] = (f"0 0 {w} {h}", f'<image href="{uri}" width="{w}" height="{h}"/>')
            return _icon_cache[key]
        raw = path.read_text(encoding="utf-8")
        raw = re.sub(r"<\?xml.*?\?>|<!--.*?-->", "", raw, flags=re.S)
        vb = re.search(r'viewBox="([^"]+)"', raw).group(1)
        styles = dict(re.findall(r"\.([A-Za-z][\w-]*)\s*\{\s*fill:\s*([^;]+);\s*\}", raw))
        raw = re.sub(r"<defs>\s*<style>.*?</style>\s*</defs>|<style>.*?</style>", "", raw, flags=re.S)
        raw = re.sub(r'class="([^"]+)"', lambda m: f'fill="{styles.get(m.group(1), "none")}"', raw)
        inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", raw.strip(), flags=re.S)
        _icon_cache[key] = (vb, inner)
    return _icon_cache[key]


def icon_aspect(key: str) -> float:
    vb = _load_icon(key)[0].split()
    return float(vb[2]) / float(vb[3])


def icon_svg(key: str, x: float, y: float, size: float, width: float | None = None) -> str:
    global _uid
    vb, body = _load_icon(key)
    _uid += 1
    tag = f"i{_uid}"
    body = re.sub(r'id="([^"]+)"', lambda m: f'id="{tag}-{m.group(1)}"', body)
    body = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{tag}-{m.group(1)})", body)
    body = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{tag}-{m.group(1)}"', body)
    return f'<svg x="{x}" y="{y}" width="{width or size}" height="{size}" viewBox="{vb}" preserveAspectRatio="xMidYMid meet">{body}</svg>'


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ----------------------------------------------------------------------------------------------- model
@dataclass
class Node:
    x: float
    y: float
    w: float
    h: float
    kind: str
    title: str
    sub: list[str] = field(default_factory=list)
    icon: str | None = None
    tip: str = ""
    new: bool = False


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    label: str
    color: str                 # semantic colour key
    dash: str = "4,4"
    icon: str | None = None
    big: bool = False
    bottom: bool = False


@dataclass
class Arrow:
    d: str
    color: str = "muted"       # semantic colour key
    label: str = ""
    lx: float = 0
    ly: float = 0
    dashed: bool = False
    both: bool = False
    anchor: str = "middle"
    secondary: bool = False    # thin + muted (offline / build / identity / optional)
    badge: str = ""            # "1".."9" main path, "A".."C" voice, "D1".. data
    bx: float = 0
    by: float = 0


@dataclass
class Diagram:
    slug: str
    title: str
    subtitle: str
    boxes: list[Box]
    nodes: list[Node]
    arrows: list[Arrow]
    cards: list[tuple[str, str, list[str]]]
    footer: str
    steps: list[tuple[str, str]]          # (badge, meaning) for the reading guide
    legend_xy: tuple[float, float] = (20, 560)


# ----------------------------------------------------------------------------------------------- render
def render_node(n: Node, T: dict) -> str:
    fill, stroke = T["kind"][n.kind]
    dash = ' stroke-dasharray="6,3"' if n.new else ""
    out = ['<g class="node">',
           f'<rect x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" rx="6" fill="{T["under"]}"/>',
           f'<rect x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>']
    newfill, newstroke = T["new"]
    if n.w < 100:  # narrow vertical node (IAP): icon on top, centred text
        cx = n.x + n.w / 2
        if n.icon:
            out.append(f'<rect x="{cx - 19}" y="{n.y + 14}" width="38" height="38" rx="6" fill="{T["tile"]}"/>')
            out.append(icon_svg(n.icon, cx - 15, n.y + 18, 30))
        out.append(f'<text x="{cx}" y="{n.y + 76}" fill="{T["text"]}" font-size="12" font-weight="600" text-anchor="middle">{esc(n.title)}</text>')
        for i, s in enumerate(n.sub):
            out.append(f'<text x="{cx}" y="{n.y + 92 + i * 12}" fill="{T["sub"]}" font-size="9" text-anchor="middle">{esc(s)}</text>')
        if n.new:
            out.append(f'<rect x="{cx - 16}" y="{n.y - 8}" width="32" height="14" rx="7" fill="{newfill}" stroke="{newstroke}"/>')
            out.append(f'<text x="{cx}" y="{n.y + 2}" fill="{newstroke}" font-size="8" font-weight="700" text-anchor="middle">NEW</text>')
        out.append("</g>")
        return "\n".join(out)
    if n.icon and n.w <= 160 and n.x < 180:  # compact node (left column): small icon + title on one row, details below
        s = 22
        wide = icon_aspect(n.icon) > 1.6
        iw = s * 2.0 if wide else s
        ih = s * 0.8 if wide else s
        out.append(f'<rect x="{n.x + 8}" y="{n.y + 8}" width="{iw + 8}" height="{s + 8}" rx="6" fill="{T["tile"]}"/>')
        out.append(icon_svg(n.icon, n.x + 12, n.y + 12 + (s - ih) / 2, ih, width=iw))
        out.append(f'<text x="{n.x + iw + 24}" y="{n.y + 27}" fill="{T["text"]}" font-size="12" font-weight="600">{esc(n.title)}</text>')
        for i, sub in enumerate(n.sub):
            out.append(f'<text x="{n.x + 12}" y="{n.y + 50 + i * 12}" fill="{T["sub"]}" font-size="9">{esc(sub)}</text>')
        out.append("</g>")
        return "\n".join(out)
    tx = n.x + 12
    if n.icon:
        s = 30 if n.h >= 60 else 24
        wide = icon_aspect(n.icon) > 1.6          # wordmark logos (SAP, AVEVA, Leaflet, OSDU) get a wider tile
        iw = s * 2.0 if wide else s
        ih = s * 0.8 if wide else s
        out.append(f'<rect x="{n.x + 10}" y="{n.y + (n.h - s) / 2 - 4}" width="{iw + 8}" height="{s + 8}" rx="6" fill="{T["tile"]}"/>')
        out.append(icon_svg(n.icon, n.x + 14, n.y + (n.h - ih) / 2, ih, width=iw))
        tx = n.x + iw + 28
    ty = n.y + n.h / 2 - (len(n.sub) * 12) / 2 + 3
    out.append(f'<text x="{tx}" y="{ty}" fill="{T["text"]}" font-size="12" font-weight="600">{esc(n.title)}</text>')
    for i, s in enumerate(n.sub):
        out.append(f'<text x="{tx}" y="{ty + 15 + i * 12}" fill="{T["sub"]}" font-size="9">{esc(s)}</text>')
    if n.new:
        bx = n.x + n.w - 38
        out.append(f'<rect x="{bx}" y="{n.y - 8}" width="32" height="14" rx="7" fill="{newfill}" stroke="{newstroke}"/>')
        out.append(f'<text x="{bx + 16}" y="{n.y + 2}" fill="{newstroke}" font-size="8" font-weight="700" text-anchor="middle">NEW</text>')
    out.append("</g>")
    return "\n".join(out)


def render_box(b: Box, T: dict) -> str:
    color = T["color"][b.color]
    fill = T["big_fill"] if b.big else T["box_fill"]
    out = [f'<rect x="{b.x}" y="{b.y}" width="{b.w}" height="{b.h}" rx="{12 if b.big else 10}" fill="{fill}" stroke="{color}" stroke-width="1" stroke-dasharray="{b.dash}"/>']
    lx = b.x + 12
    top = b.y + b.h - 28 if b.bottom else b.y + 6
    if b.icon:
        out.append(f'<rect x="{b.x + 9}" y="{top}" width="20" height="20" rx="4" fill="{T["tile"]}"/>')
        out.append(icon_svg(b.icon, b.x + 11, top + 2, 16))
        lx = b.x + 36
    out.append(f'<text x="{lx}" y="{top + 14}" fill="{color}" font-size="10" font-weight="600">{esc(b.label)}</text>')
    return "\n".join(out)


def render_arrow(a: Arrow, T: dict) -> str:
    key = "muted" if a.secondary else a.color
    color = T["color"][key]
    width, opacity = ("1", "0.75") if a.secondary else ("1.6", "1")
    dash = ' stroke-dasharray="5,4"' if (a.dashed or a.secondary) else ""
    start = f' marker-start="url(#as-{key})"' if a.both else ""
    out = [f'<path d="{a.d}" fill="none" stroke="{color}" stroke-width="{width}" opacity="{opacity}"{dash} marker-end="url(#ae-{key})"{start}/>']
    if a.label:
        lc = T["sub"] if a.secondary else T["alabel"]
        out.append(f'<text x="{a.lx}" y="{a.ly}" fill="{lc}" font-size="8.5" text-anchor="{a.anchor}" class="alabel">{esc(a.label)}</text>')
    return "\n".join(out)


def badge(text: str, x: float, y: float, T: dict) -> str:
    """① main path (dark/white disc), Ⓐ voice path (cyan disc), D1 data path (violet pill)."""
    if text.startswith("D"):
        c = T["color"]["violet"]
        return (f'<g class="badge"><rect x="{x - 12}" y="{y - 8}" width="24" height="16" rx="8" fill="{c}"/>'
                f'<text x="{x}" y="{y + 3.5}" fill="#fff" font-size="9" font-weight="700" text-anchor="middle">{text}</text></g>')
    if text.isalpha():
        c = T["color"]["cyan"]
        return (f'<g class="badge"><circle cx="{x}" cy="{y}" r="8.5" fill="{c}"/>'
                f'<text x="{x}" y="{y + 3.5}" fill="#fff" font-size="9.5" font-weight="700" text-anchor="middle">{text}</text></g>')
    return (f'<g class="badge"><circle cx="{x}" cy="{y}" r="8.5" fill="{T["badge_main_fill"]}" stroke="{T["color"]["slate"]}" stroke-width="0.8"/>'
            f'<text x="{x}" y="{y + 3.5}" fill="{T["badge_main_text"]}" font-size="9.5" font-weight="700" text-anchor="middle">{text}</text></g>')


def markers(T: dict) -> str:
    out = []
    for key, c in T["color"].items():
        out.append(f'<marker id="ae-{key}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="{c}"/></marker>')
        out.append(f'<marker id="as-{key}" markerWidth="10" markerHeight="7" refX="1" refY="3.5" orient="auto"><polygon points="10 0, 0 3.5, 10 7" fill="{c}"/></marker>')
    return "\n".join(out)


def legend(x: float, y: float, T: dict, data_path: bool) -> str:
    rows = [("frontend", "Browser / UI"), ("backend", "Urvi services (Cloud Run)"), ("ai", "Gemini / Vertex AI"),
            ("data", "Data & storage"), ("cloud", "Build / operations"), ("security", "Identity & security"),
            ("external", "External / on-prem")]
    out = [f'<text x="{x}" y="{y}" fill="{T["text"]}" font-size="10" font-weight="600">Legend</text>']
    yy = y + 12
    for k, label in rows:
        fill, stroke = T["kind"][k]
        out.append(f'<rect x="{x}" y="{yy}" width="16" height="10" rx="2" fill="{fill}" stroke="{stroke}"/>')
        out.append(f'<text x="{x + 22}" y="{yy + 8}" fill="{T["sub"]}" font-size="8">{label}</text>')
        yy += 15
    yy += 4
    out.append(badge("1", x + 8, yy + 4, T))
    out.append(f'<text x="{x + 22}" y="{yy + 7}" fill="{T["sub"]}" font-size="8">Typed question, in order</text>')
    yy += 20
    out.append(badge("A", x + 8, yy + 4, T))
    out.append(f'<text x="{x + 22}" y="{yy + 7}" fill="{T["sub"]}" font-size="8">Voice path</text>')
    yy += 20
    if data_path:
        out.append(badge("D1", x + 10, yy + 4, T))
        out.append(f'<text x="{x + 26}" y="{yy + 7}" fill="{T["sub"]}" font-size="8">Data path</text>')
        yy += 20
    out.append(f'<line x1="{x}" y1="{yy + 4}" x2="{x + 16}" y2="{yy + 4}" stroke="{T["color"]["muted"]}" stroke-dasharray="4,3"/>')
    out.append(f'<text x="{x + 22}" y="{yy + 7}" fill="{T["sub"]}" font-size="8">Secondary / optional flow</text>')
    yy += 16
    nf, ns = T["new"]
    out.append(f'<rect x="{x}" y="{yy}" width="16" height="10" rx="2" fill="none" stroke="{ns}" stroke-dasharray="4,2"/>')
    out.append(f'<text x="{x + 22}" y="{yy + 8}" fill="{T["sub"]}" font-size="8">New in target</text>')
    out.append(f'<text x="{x}" y="{yy + 26}" fill="{T["color"]["muted"]}" font-size="8">Hover any box for details</text>')
    return "\n".join(out)


def hotspot(n: Node) -> str:
    left, top, width, height = n.x / W * 100, n.y / H * 100, n.w / W * 100, n.h / H * 100
    cls = ["hot", "up" if n.y > H * 0.55 else "down"] + (["right"] if n.x > W * 0.62 else [])
    return (f'<div class="{" ".join(cls)}" style="left:{left:.3f}%;top:{top:.3f}%;width:{width:.3f}%;height:{height:.3f}%" '
            f'tabindex="0" aria-label="{esc(n.title)}"><div class="tip"><b>{esc(n.title)}</b><span>{esc(n.tip)}</span></div></div>')


def css(T: dict) -> str:
    return f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{T['bg']};color:{T['text']};font-family:{T['font']}}}
body{{padding:1.25rem 1.5rem 1.5rem}}
.container{{margin:0 auto;max-width:1500px}}
.header{{margin-bottom:.8rem}}
.header-row{{align-items:center;display:flex;gap:.75rem;margin-bottom:.35rem}}
.pulse-dot{{animation:pulse 2s infinite;background:{T['color']['cyan']};border-radius:50%;height:10px;width:10px}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.45}}}}
h1{{font-size:1.2rem;font-weight:700;letter-spacing:-.01em}}
.badge-pill{{border:1px solid {T['border']};border-radius:999px;color:{T['sub']};font-size:.65rem;padding:.1rem .55rem}}
.subtitle{{color:{T['sub']};font-size:.78rem;margin-left:1.4rem}}
.steps{{display:flex;flex-wrap:wrap;gap:.35rem .9rem;margin:.6rem 0 .8rem 1.4rem;font-size:.7rem;color:{T['sub']}}}
.steps b{{color:{T['text']};font-weight:700}}
.diagram-container{{background:{T['panel']};border:1px solid {T['border']};border-radius:1rem;overflow-x:auto;padding:1rem}}
.stage{{position:relative;min-width:1100px}}
svg.diagram{{display:block;width:100%;height:auto}}
.alabel{{paint-order:stroke;stroke:{T['halo']};stroke-width:3px}}
.hot{{position:absolute;border-radius:6px;cursor:help;outline:none}}
.hot:hover,.hot:focus{{box-shadow:0 0 0 2px {T['color']['cyan']},0 0 16px rgba(34,211,238,.3)}}
.tip{{display:none;position:absolute;left:0;z-index:20;width:300px;background:{T['tip_bg']};border:1px solid {T['tip_border']};
  border-radius:8px;padding:.6rem .7rem;box-shadow:0 12px 32px rgba(0,0,0,.35);font-size:.7rem;line-height:1.45;color:{T['tip_text']};pointer-events:none}}
.tip b{{display:block;color:{T['tip_title']};font-size:.75rem;margin-bottom:.25rem}}
.hot.down .tip{{top:calc(100% + 8px)}}
.hot.up .tip{{bottom:calc(100% + 8px)}}
.hot.right .tip{{left:auto;right:0}}
.hot:hover .tip,.hot:focus .tip{{display:block}}
.hot:hover{{z-index:30}}
.cards{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin-top:1.25rem}}
.card{{background:{T['panel']};border:1px solid {T['border']};border-radius:.75rem;padding:1rem 1.1rem}}
.card-header{{align-items:center;display:flex;gap:.5rem;margin-bottom:.6rem}}
.card-dot{{border-radius:50%;height:8px;width:8px}}
.card h3{{font-size:.8rem;font-weight:600}}
.card ul{{color:{T['sub']};font-size:.7rem;list-style:none}}
.card li{{margin-bottom:.3rem}}
.footer{{color:{T['footer']};font-size:.68rem;margin-top:1.1rem;text-align:center}}
"""


def render(d: Diagram, theme: str) -> str:
    T = THEMES[theme]
    data_path = any(a.badge.startswith("D") for a in d.arrows)
    svg = [f'<svg class="diagram" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(d.title)}">',
           "<defs>", markers(T),
           f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="{T["grid"]}" stroke-width="0.5"/></pattern>',
           "</defs>", f'<rect width="{W}" height="{H}" fill="url(#grid)"/>']
    svg += [render_box(b, T) for b in d.boxes]
    svg += [render_arrow(a, T) for a in d.arrows]          # arrows behind nodes
    svg += [render_node(n, T) for n in d.nodes]
    svg += [badge(a.badge, a.bx, a.by, T) for a in d.arrows if a.badge]   # badges on top
    svg.append(legend(*d.legend_xy, T, data_path))
    svg.append("</svg>")
    hots = "\n".join(hotspot(n) for n in d.nodes if n.tip)
    dots = {k: T["color"][k] for k in T["color"]}
    cards = "\n".join(
        f'<div class="card"><div class="card-header"><div class="card-dot" style="background:{dots[dot]}"></div><h3>{esc(t)}</h3></div>'
        f'<ul>{"".join(f"<li>• {esc(i)}</li>" for i in items)}</ul></div>' for t, dot, items in d.cards)
    steps = " ".join(f"<span><b>{esc(b)}</b> {esc(m)}</span>" for b, m in d.steps)
    other = f"{d.slug}{'' if theme == 'light' else '-light'}.html"
    other_label = "Dark version" if theme == "light" else "Light version (for decks)"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="{theme}">
<title>{esc(d.title)}</title>
{T['font_link']}
<style>{css(T)}</style>
</head>
<body>
<!-- Generated by frontend/scripts/build_architecture.py (BL-8). Do not edit by hand. -->
<div class="container">
  <div class="header">
    <div class="header-row"><div class="pulse-dot"></div><h1>{esc(d.title)}</h1>
      <span class="badge-pill">synthetic demo data</span></div>
    <p class="subtitle">{esc(d.subtitle)}</p>
    <div class="steps">{steps}</div>
  </div>
  <div class="diagram-container"><div class="stage">
{chr(10).join(svg)}
{hots}
  </div></div>
  <div class="cards">{cards}</div>
  <p class="footer">{esc(d.footer)} · <a href="{other}" style="color:inherit">{other_label}</a></p>
</div>
</body>
</html>
"""


# ----------------------------------------------------------------------------------------------- current
LX, RX, CW = 570, 835, 215          # Cloud Run left / right column x, column width (channel 785..835)
BX, BW = 205, 212                   # browser nodes
PX, PW = 1120, 290                  # platform column


def current_view() -> tuple[list[Box], list[Node], list[Arrow], list[tuple[str, str]]]:
    boxes = [
        Box(452, 28, 990, 902, "Google Cloud · project workover-operations-agentic-ai (demo: us-central1)", "amber", "8,4", big=True),
        Box(190, 215, 242, 470, "Browser · Urvi web app", "cyan"),
        Box(550, 60, 520, 125, "Vertex AI · Gemini", "blue", icon="vertex-ai"),
        Box(550, 210, 520, 455, "Cloud Run · us-central1 · wellpulse-app · 1 instance", "emerald", icon="cloud-run", bottom=True),
        Box(1100, 60, 330, 185, "Build & deploy", "amber"),
        Box(1100, 340, 330, 310, "Identity · operations", "rose"),
        Box(550, 715, 880, 160, "Data platform · asia-south1 · medallion lakehouse", "violet"),
        Box(190, 715, 242, 160, "Offline · build time", "slate"),
    ]
    nodes = [
        Node(20, 250, 140, 110, "external", "Users", ["ED · Asset Manager", "Field Engineer", "Chrome + microphone"],
             tip="Executive Director, asset / production engineers and field engineers. They use Urvi by mouse, typing "
                 "or voice (English by default; Hindi / Hinglish on request)."),
        Node(20, 420, 140, 60, "external", "Esri imagery", ["satellite basemap"],
             tip="Public satellite tiles behind the field map. Well and GGS positions are synthetic."),
        Node(BX, 250, BW, 70, "frontend", "Voice client", ["16 kHz in · 24 kHz out", "barge-in"],
             tip="Streams microphone audio to the Live proxy over a WebSocket and plays Urvi's reply. A reconnect starts "
                 "a fresh session (D-43)."),
        Node(BX, 340, BW, 70, "frontend", "Urvi UI", ["single-page web app", "map-first"],
             tip="India → Assam → field → cluster → well drill-down, the well panel and the docked Urvi agent."),
        Node(BX, 430, BW, 70, "frontend", "Field map", ["field + GGS outlines", "health-coloured wells"],
             tip="412 wells coloured Healthy / Needs attention / Not producing, flowlines, and an India view."),
        Node(BX, 520, BW, 70, "frontend", "Hands-off control", ["screen commands", "EN / Hinglish / Hindi"],
             tip="Plain screen commands run in the browser with no model call; the agent can also send allow-listed "
                 "screen actions (ui_control)."),
        Node(BX, 610, BW, 60, "frontend", "Answer canvas", ["charts · completion diagram", "field report"],
             tip="Agent answers open the matching view: charts, the completion diagram, comparisons, the printable "
                 "pre-field well pack."),
        Node(LX, 95, CW, 70, "ai", "Gemini 3.8 Live", ["native audio · voice Aoede", "us-central1"], icon="gemini",
             tip="Speech-to-speech model for voice. The demo runs in us-central1 because Gemini Live is not yet offered "
                 "in India regions. Numbers come only from tool results."),
        Node(RX, 95, CW, 70, "ai", "Gemini 3.8 Flash", ["text agent model", "global endpoint"], icon="gemini",
             tip="Reasoning model for the typed agent: chooses tools, reads results, writes a short answer (D-13)."),
        Node(LX, 250, CW, 70, "backend", "Gemini Live proxy", ["WS /ws/live · 13 tools", "screen context"],
             tip="Server-side WebSocket bridge between the browser and Gemini Live. Runs voice tool calls on the "
                 "server; falls back to text after 3 failures."),
        Node(RX, 250, CW, 80, "backend", "ADK agent runner", ["Google ADK · 34 tools", "number guardrail", "role access"],
             icon="agents",
             tip="Google Agent Development Kit runner for chat. Routes the 5-level drill-down to tools; an after-model "
                 "check masks any number that is not in a tool result."),
        Node(LX, 350, CW, 70, "backend", "Urvi API", ["REST /api · /api/chat", "serves the web app"],
             tip="Python API (FastAPI): wells, fields, documents, reports and /api/chat; also serves the web app."),
        Node(RX, 360, CW, 80, "backend", "Analytics & ML", ["TC-001…035 tools", "classifier · physics checks", "NBA · success engine"],
             tip="The tools behind every answer: decline attribution, health, candidate ranking, next best action "
                 "with top 3 and P(success). Shared by chat and voice. See docs/ml_recommendation_engine.md."),
        Node(RX, 470, CW, 70, "backend", "Data access layer", ["parquet (in image)", "BigQuery switch"],
             tip="One repository interface over the landing tables: parquet baked into the image for the demo; the "
                 "same API can read BigQuery Silver (parity-tested)."),
        Node(LX, 460, CW, 70, "backend", "Document search", ["keyword index (in image)", "20,966 synthetic PDFs"],
             tip="Keyword (TF-IDF) retrieval over the synthetic reports and SOP library; 28,675 chunks."),
        Node(LX, 560, CW, 60, "backend", "Field report", ["dossier · HTML / PDF"],
             tip="Printable pre-field well pack and dossier; every digit traces to a tool return."),
        Node(RX, 560, CW, 60, "backend", "In-memory sessions", ["fresh per demo"],
             tip="Chat and voice sessions live in memory, hence one Cloud Run instance with session affinity (D-16)."),
        Node(205, 760, 212, 80, "external", "Data generator", ["synthetic · seeded", "412 wells · 60 months"],
             tip="Deterministic generator for Geleki, Lakwa and Lakhmani (2021-10 → 2026-09). Also baked into the image."),
        Node(570, 760, 190, 80, "data", "Cloud Storage", ["data lake bucket", "bronze/ · documents/"], icon="cloud-storage",
             tip="Raw generator drops, the 20,966 PDFs and Silver exports."),
        Node(805, 760, 180, 80, "data", "BigQuery Bronze", ["external tables", "raw, as landed"], icon="bigquery",
             tip="Dataset wellpulse_bronze: external tables over the bucket."),
        Node(1030, 760, 180, 80, "data", "BigQuery Silver", ["partitioned by date", "clustered by well"], icon="bigquery",
             tip="Dataset wellpulse_silver: typed, de-duplicated tables loaded by MERGE."),
        Node(1255, 760, 170, 80, "data", "BigQuery Gold", ["Dataform models", "KPIs · facts"], icon="bigquery",
             tip="Dataset wellpulse_gold built by Dataform: field KPIs and dossier facts."),
        Node(PX, 100, PW, 60, "cloud", "Cloud Build", ["builds the container image"], icon="devops",
             tip="Builds the image: web app, Python dependencies, document corpus and a self-check."),
        Node(PX, 180, PW, 60, "cloud", "Artifact Registry", ["wellpulse-app images"], icon="devops",
             tip="Stores versioned images (V 1.0 = v1-4b8463d); rollback = shift traffic to an earlier revision."),
        Node(PX, 380, PW, 60, "security", "Runtime service account", ["IAM · least privilege · no API keys"], icon="security",
             tip="Cloud Run runs as a dedicated service account; Vertex AI and BigQuery via Application Default Credentials."),
        Node(PX, 460, PW, 60, "cloud", "Cloud Logging", ["request + app logs"], icon="observability",
             tip="Cloud Run sends request and application logs to Cloud Logging automatically."),
    ]
    arrows = [
        # main path ① → ⑦
        Arrow("M 160 300 L 188 300", "slate", "HTTPS", 174, 288, badge="1", bx=174, by=300),
        Arrow(f"M {BX + BW} 380 L {LX - 2} 380", "cyan", "REST", 494, 369, badge="2", bx=494, by=380),
        Arrow(f"M {LX + CW} 385 L 800 385 L 800 312 L {RX - 2} 312", "emerald", badge="3", bx=800, by=350),
        Arrow(f"M {RX + 107} 250 L {RX + 107} 167", "blue", "prompt + tool results", RX + 120, 214, both=True, anchor="start",
              badge="4", bx=RX + 107, by=208),
        Arrow(f"M {RX + 107} 330 L {RX + 107} 358", "emerald", "tool calls", RX + 120, 348, anchor="start",
              badge="5", bx=RX + 107, by=344),
        Arrow(f"M {RX + 107} 440 L {RX + 107} 468", "emerald", "reads", RX + 120, 458, anchor="start",
              badge="6", bx=RX + 107, by=454),
        Arrow(f"M {RX} 428 L 810 428 L 810 495 L {LX + CW + 2} 495", "emerald", "search", 810, 515),
        Arrow(f"M {LX} 395 L 530 395 L 530 555 L {BX + BW + 2} 555", "cyan", "answer + screen actions", 474, 548,
              badge="7", bx=530, by=475),
        # voice path Ⓐ → Ⓒ
        Arrow(f"M {BX + BW} 285 L {LX - 2} 285", "cyan", "audio", 441, 279, both=True, badge="A", bx=494, by=285),
        Arrow(f"M {LX + 107} 250 L {LX + 107} 167", "blue", "audio + tool calls", LX + 120, 214, both=True, anchor="start",
              badge="B", bx=LX + 107, by=208),
        Arrow(f"M {LX + CW} 272 L 820 272 L 820 400 L {RX - 2} 400", "emerald", badge="C", bx=820, by=330),
        # secondary
        Arrow("M 205 465 L 162 452", secondary=True, label="tiles", lx=183, ly=446),
        Arrow("M 417 800 L 568 800", secondary=True, label="upload", lx=492, ly=794),
        Arrow("M 760 800 L 803 800", secondary=True),
        Arrow("M 985 800 L 1028 800", secondary=True, label="MERGE", lx=1006, ly=794),
        Arrow("M 1210 800 L 1253 800", secondary=True, label="Dataform", lx=1231, ly=794),
        Arrow(f"M {RX + CW} 505 L 1058 505 L 1058 758", secondary=True, label="optional backend", lx=1052, ly=690, anchor="end"),
        Arrow(f"M {PX + PW / 2} 160 L {PX + PW / 2} 178", secondary=True),
        Arrow(f"M {PX} 228 L 1072 228", secondary=True, label="deploy", lx=1096, ly=222),
        Arrow(f"M {PX} 410 L 1072 410", secondary=True, label="identity", lx=1096, ly=403),
    ]
    steps = [("①", "user asks"), ("②", "web app calls the Urvi API"), ("③", "API hands the question to the agent"),
             ("④", "agent ↔ Gemini Flash"), ("⑤", "agent calls the analytics tools"), ("⑥", "tools read well data"),
             ("⑦", "answer + screen actions back to the browser"), ("Ⓐ–Ⓒ", "voice: audio → Live proxy ↔ Gemini Live → same tools")]
    return boxes, nodes, arrows, steps


# ----------------------------------------------------------------------------------------------- target
def target_view() -> tuple[list[Box], list[Node], list[Arrow], list[tuple[str, str]]]:
    """ONGC production in India regions (BL-10, docs/data_access_plan.md). AI runs in the cloud (RFP §3.1.3)."""
    boxes = [
        Box(190, 40, 250, 870, "ONGC data centres · on-prem (Category A stays)", "slate", "8,4"),
        Box(470, 30, 970, 900, "Google Cloud India · asia-south1 Mumbai (primary) + asia-south2 Delhi (DR) · "
            "MeitY-empanelled · VPC Service Controls · CMEK", "amber", "8,4", big=True, bottom=True),
        Box(490, 70, 945, 130, "Vertex AI · India regional endpoints", "blue", icon="vertex-ai"),
        Box(490, 230, 620, 330, "Urvi · Cloud Run asia-south1 · autoscaled", "emerald", icon="cloud-run", bottom=True),
        Box(1130, 230, 305, 340, "Security · operations", "rose"),
        Box(490, 600, 945, 245, "ONGC EDP · cloud zone (placement decided by ONGC)", "violet"),
    ]
    S = 205, 220
    nodes = [
        Node(20, 140, 150, 100, "external", "Users", ["ONGC ED · asset team", "field engineers", "browser + mic"],
             tip="ONGC users sign in with their ONGC identity. English by default; Hindi / Hinglish on request."),
        Node(20, 270, 150, 60, "external", "ONGC AD / SSO", ["identity provider"],
             tip="ONGC's directory. Identity-Aware Proxy federates with it; the same identity drives role-based access."),
        Node(S[0], 80, S[1], 56, "external", "Production / DPR", ["rates · allocation · tests"],
             tip="Daily production reports, allocation and well tests (exact system to confirm with Assam Asset)."),
        Node(S[0], 146, S[1], 56, "external", "SCADA + OSI PI", ["AVEVA PI · THP · BHP"],
             tip="OT telemetry. Raw OT data stays on-prem (Category A); only derived hourly / daily aggregates are placed "
                 "in the cloud zone. Urvi never writes back."),
        Node(S[0], 212, S[1], 56, "external", "WIS / EDS", ["well master · completion"],
             tip="Well master, construction, completion, deviation and formation tops."),
        Node(S[0], 278, S[1], 56, "external", "SAP (PM / MM / FI)", ["jobs · rigs · materials"],
             tip="Work orders, rig and material waits, cost bands (LOW / MED / HIGH only)."),
        Node(S[0], 344, S[1], 56, "external", "LIMS", ["fluids · wax · sand"], tip="Lab results for wax / sand and water chemistry."),
        Node(S[0], 410, S[1], 56, "external", "DISHA EDMS", ["reports · CBL · SOPs"],
             tip="Engineering documents: indexed for search; facts extracted by Gemini for the models."),
        Node(S[0], 500, S[1], 90, "data", "EDP on-prem zone", ["Delhi + Vadodara DCs", "Bronze / Silver / Gold", "Category A stays"],
             tip="ONGC Enterprise Data Platform, on-prem side (RFP ZV7AL26011, §3.1.2). Ingests the sources via UDEL."),
        Node(S[0], 640, S[1], 70, "external", "Pilot extract", ["Route P · masked wells", "before the EDP is live"], new=True,
             tip="Pilot bridge: 10–20 mature Assam wells, masked, exported to an India-region landing bucket."),
        Node(600, 110, 240, 70, "ai", "Gemini 3.8 Flash", ["text agent model", "India regional endpoint"], icon="gemini",
             tip="Text agent model on a Vertex AI India endpoint. Customer data is not used to train models."),
        Node(855, 110, 240, 70, "ai", "Gemini 3.8 Live", ["native audio voice", "India regional endpoint"], icon="gemini",
             tip="Voice model on an India endpoint at go-live (the demo runs in us-central1 only because Live is not yet "
                 "offered in India regions)."),
        Node(1110, 110, 150, 70, "ai", "AI Search", ["Vertex AI", "docs + SOPs"], icon="vertex-ai",
             tip="Vertex AI Search over the EDMS extract: grounded answers with citations, in an India region."),
        Node(1275, 110, 150, 70, "ai", "Training", ["Vertex AI", "Model Registry"], icon="vertex-ai",
             tip="Trains the recommendation models on EDP Gold history, versions them in Model Registry, writes nightly "
                 "scores to Gold (docs/ml_recommendation_engine.md Part B)."),
        Node(505, 270, 80, 130, "security", "IAP", ["ONGC", "SSO"], icon="security",
             tip="Identity-Aware Proxy: only signed-in, authorised ONGC users reach Urvi (web and voice)."),
        Node(600, 270, 240, 70, "backend", "ADK agent runner", ["34 tools · number guardrail", "role access"], icon="agents",
             tip="Same agent as the demo: Google ADK, the 5-level drill-down, numbers checked against tool results."),
        Node(855, 270, 240, 70, "backend", "Gemini Live proxy", ["WS /ws/live · voice tools", "screen context"],
             tip="Server-side voice bridge; runs voice tools on the server."),
        Node(600, 360, 240, 70, "backend", "Urvi API + web app", ["REST /api · /api/chat"],
             tip="The same API and web app as the demo, served from Cloud Run in Mumbai."),
        Node(855, 360, 240, 70, "backend", "Analytics & ML", ["TC-001…035 tools", "nightly model scores"],
             tip="Engineering tools and the recommendation models' nightly scores, read through the EDP adapter."),
        Node(600, 450, 240, 62, "data", "Session store", ["Memorystore · CMEK"], icon="databases",
             tip="External session state so Cloud Run can scale. Each demo still starts fresh (D-43)."),
        Node(855, 450, 240, 62, "backend", "EDP data adapter", ["DATA_BACKEND=edp · API only"],
             tip="New adapter in Urvi's data-access layer; reads the EDP consumption API (no direct database queries)."),
        Node(1145, 262, 275, 50, "security", "Cloud KMS · CMEK / EKM", ["ONGC-held keys"], icon="security",
             tip="ONGC holds the encryption keys (RFP §3.2.6 'enhanced encryption')."),
        Node(1145, 324, 275, 50, "security", "Access Approval", ["+ Access Transparency"], icon="security",
             tip="Any Google support access needs ONGC approval and is logged."),
        Node(1145, 386, 275, 50, "security", "Secret Manager", ["config · API credentials"], icon="security",
             tip="Credentials for the EDP API and configuration, versioned and audited."),
        Node(1145, 448, 275, 50, "cloud", "Logging + Monitoring", ["India sinks · 180 days"], icon="observability",
             tip="Every agent turn and tool call logged in India, kept ≥ 180 days (CERT-In), exported to ONGC SIEM."),
        Node(1145, 510, 275, 50, "cloud", "Cloud Build + Registry", ["images built in asia-south1"], icon="devops",
             tip="Builds and stores Urvi images in India; deploys new Cloud Run revisions."),
        Node(505, 640, 190, 70, "data", "UDEL ingestion", ["CDC · streams · files", "Dataflow / Data Fusion"], icon="data-analytics",
             tip="EDP Unified Data Exchange Layer, cloud side: validates, classifies and lands data placed in the cloud zone."),
        Node(715, 640, 160, 70, "data", "Bronze", ["raw, as landed"], icon="bigquery", tip="Raw layer (Cloud Storage / BigQuery, India)."),
        Node(895, 640, 160, 70, "data", "Silver", ["cleaned, typed"], icon="bigquery", tip="Cleaned, typed, de-duplicated tables."),
        Node(1075, 640, 160, 70, "data", "Gold", ["Well Health data"], icon="bigquery",
             tip="Curated 'Well Health & Opportunity' data product (RFP Annex H 1.5) + nightly recommendation scores."),
        Node(1255, 640, 170, 70, "data", "Consume API", ["OpenAPI / GraphQL"], icon="apigee",
             tip="EDP consumption layer (API gateway). Urvi reads only through here, with a scoped service identity."),
        Node(505, 750, 250, 62, "data", "Dataplex catalogue", ["lineage · classification tags"], icon="data-analytics",
             tip="Catalogue, lineage and classification labels for every dataset Urvi reads."),
        Node(775, 750, 230, 62, "data", "Cloud Storage landing", ["pilot + EDP drops"], icon="cloud-storage",
             tip="India-region landing bucket for the pilot extract and EDP file loads, CMEK-encrypted."),
    ]
    arrows = [
        # main path
        Arrow("M 95 140 L 95 18 L 480 18 L 480 220 L 545 220 L 545 268", "slate", "HTTPS + voice · ONGC SSO", 300, 12,
              badge="1", bx=140, by=18),
        Arrow("M 585 395 L 598 395", "rose", badge="2", bx=591, by=395),
        Arrow("M 720 360 L 720 342", "emerald", badge="3", bx=720, by=351),
        Arrow("M 720 270 L 720 182", "blue", "prompt + tool results", 735, 232, both=True, anchor="start", badge="4", bx=720, by=226),
        Arrow("M 840 320 L 847 320 L 847 385 L 853 385", "emerald", badge="5", bx=847, by=352),
        Arrow("M 975 430 L 975 448", "emerald", badge="6", bx=975, by=439),
        Arrow("M 1340 638 L 1340 590 L 1030 590 L 1030 514", "violet", "Well Health data product (API)", 1185, 586,
              badge="7", bx=1340, by=614),
        # voice
        Arrow("M 975 270 L 975 182", "blue", "audio", 990, 232, both=True, anchor="start", badge="B", bx=975, by=226),
        Arrow("M 975 340 L 975 358", "emerald", badge="C", bx=1000, by=349),
        # data path D1 → D4
        Arrow(f"M {S[0] + S[1] / 2} 466 L {S[0] + S[1] / 2} 498", "slate", "UDEL: CDC · OPC UA · WITSML", S[0] + S[1] / 2 + 16, 487,
              anchor="start", badge="D1", bx=S[0] + S[1] / 2, by=482),
        Arrow("M 425 515 L 455 515 L 455 675 L 503 675", "amber", "Interconnect", 459, 733, anchor="start", badge="D2", bx=455, by=600),
        Arrow("M 695 675 L 713 675", "violet", badge="D3", bx=704, by=660),
        Arrow("M 875 675 L 893 675", "violet"),
        Arrow("M 1055 675 L 1073 675", "violet"),
        Arrow("M 1235 675 L 1253 675", "violet", badge="D4", bx=1244, by=660),
        # secondary / alternatives
        Arrow("M 425 575 L 465 575 L 465 590 L 990 590 L 990 514", secondary=True, label="Route B · on-prem API (private)", lx=640, ly=584),
        Arrow("M 425 675 L 440 675 L 440 875 L 890 875 L 890 814", secondary=True, label="Route P · pilot extract", lx=680, ly=869),
        Arrow("M 820 748 L 820 712", secondary=True),
        Arrow("M 1095 395 L 1118 395 L 1118 182", secondary=True, label="docs", lx=1114, ly=300, anchor="end"),
        Arrow("M 1425 145 L 1433 145 L 1433 630 L 1155 630 L 1155 638", secondary=True, label="nightly scores", lx=1300, ly=626),
        Arrow("M 1145 287 L 1112 287", secondary=True, label="CMEK", lx=1128, ly=281),
    ]
    steps = [("①", "user signs in (IAP + ONGC SSO)"), ("②", "web app / API"), ("③", "agent"), ("④", "agent ↔ Gemini (India)"),
             ("⑤", "analytics tools"), ("⑥", "EDP data adapter"), ("⑦", "reads the Well Health product via API"),
             ("Ⓑ–Ⓒ", "voice: Live proxy ↔ Gemini Live → same tools"),
             ("D1–D4", "data: ONGC sources → EDP on-prem → Interconnect → Bronze / Silver / Gold → API")]
    return boxes, nodes, arrows, steps


CARDS_CURRENT = [
    ("Agent & voice", "cyan", ["Chat: ADK agent on Gemini 3.8 Flash, 34 tools",
                               "Voice: Gemini 3.8 Live via a server WebSocket proxy, 13 tools",
                               "Hands-off screen control in English, Hinglish and Hindi",
                               "English by default; Hindi / Hinglish on request"]),
    ("Data & ML", "violet", ["412 synthetic wells · 3 fields · 60 months",
                             "Medallion lakehouse: Bronze → Silver → Gold (BigQuery, asia-south1)",
                             "Intervention classifier + physics checks + success engine",
                             "Top 3 next best actions with P(success) and look-alike wells"]),
    ("Trust & guardrails", "rose", ["Every number comes from a tool result",
                                    "No currency: cost band + rig-days only",
                                    "No API keys: Vertex AI via the runtime service account",
                                    "All data is synthetic and labelled as such"]),
]
CARDS_TARGET = [
    ("Where the data comes from", "violet", ["ONGC sources: DPR / production, SCADA + PI, WIS / EDS, SAP, LIMS, DISHA",
                                             "Ingested once by the ONGC EDP (RFP ZV7AL26011), not by Urvi",
                                             "Urvi reads the 'Well Health & Opportunity' product via API",
                                             "Category A raw data stays on-prem; AI runs in the cloud"]),
    ("Stays in India", "amber", ["Mumbai asia-south1 primary, Delhi asia-south2 DR",
                                 "Gemini on India endpoints; no training on ONGC data",
                                 "CMEK / EKM keys held by ONGC; VPC Service Controls perimeter",
                                 "Logs in India ≥ 180 days; Access Approval for support"]),
    ("Same agent as the demo", "emerald", ["ADK agent, 34 tools, number grounding",
                                           "Voice via Gemini Live; English default",
                                           "IAP + ONGC SSO; role-based access enforced",
                                           "Routes A / B / P: docs/data_access_plan.md"]),
]


# Icon for every box that is not a Google product: real logo where the box IS that product, else a generic glyph.
ICON_FOR = {
    "Users": "g:person", "ONGC AD / SSO": "g:badge",
    "Esri imagery": "esri", "Field map": "leaflet",
    "Voice client": "g:mic", "Urvi UI": "g:browser", "Hands-off control": "g:cursor", "Answer canvas": "g:canvas",
    "Gemini Live proxy": "g:wave", "Urvi API": "g:server", "Urvi API + web app": "g:server",
    "Analytics & ML": "g:insights", "Data access layer": "g:database", "EDP data adapter": "g:plug",
    "Document search": "g:search-doc", "Field report": "g:document", "In-memory sessions": "g:memory",
    "Data generator": "g:upload", "Pilot extract": "g:upload",
    "Production / DPR": "g:database", "SCADA + OSI PI": "aveva", "WIS / EDS": "g:database",
    "SAP (PM / MM / FI)": "sap", "LIMS": "g:flask", "DISHA EDMS": "g:document", "EDP on-prem zone": "osdu",
}


def _with_icons(nodes: list[Node]) -> list[Node]:
    for n in nodes:
        if not n.icon:
            n.icon = ICON_FOR.get(n.title)
    return nodes


def diagrams() -> list[Diagram]:
    cb, cn, ca, cs = current_view()
    tb, tn, ta, ts = target_view()
    cn, tn = _with_icons(cn), _with_icons(tn)
    return [
        Diagram("current", "Urvi AI Agent · Architecture · Current (V 1.0 demo)",
                "As built and running today. The demo runs in us-central1 because Gemini Live is not yet offered in India "
                "regions; it uses only synthetic data.", cb, cn, ca, CARDS_CURRENT,
                "Urvi AI Agent on WellPulse · V 1.0 · Cloud Run wellpulse-app · official Google Cloud icons (go/cloud-icons)", cs),
        Diagram("target", "Urvi AI Agent · Architecture · Target (ONGC production, India regions)",
                "Data comes from ONGC systems through the ONGC Enterprise Data Platform; Urvi and Gemini run in Google Cloud "
                "India regions; nothing leaves India.", tb, tn, ta, CARDS_TARGET,
                "Urvi AI Agent on WellPulse · target architecture (not built) · docs/data_access_plan.md · official Google Cloud icons (go/cloud-icons)", ts),
    ]


BADGE_GLYPH = {str(i): "①②③④⑤⑥⑦⑧⑨"[i - 1] for i in range(1, 10)} | {"A": "Ⓐ", "B": "Ⓑ", "C": "Ⓒ"}


def explain_markdown() -> str:
    """docs/how_urvi_works.md from the same content as the in-app Explain panel."""
    from architecture_explain import EXPLAIN

    out = ["# How Urvi works: architecture explained", "",
           "_Generated by `frontend/scripts/build_architecture.py` from `frontend/scripts/architecture_explain.py`; "
           "the same text appears in the app (Architecture tab → **Explain**). Do not edit by hand._", ""]
    for key in ("current", "target"):
        e = EXPLAIN[key]
        out += [f"## {e['title']}", "", e["intro"], ""]
        for sec in e["sections"]:
            out += [f"### {sec['heading']}", ""]
            for para in sec.get("body", []):
                out += [para, ""]
            if "steps" in sec:
                for b, t, txt in sec["steps"]:
                    out.append(f"- **{BADGE_GLYPH.get(b, b)} {t}:** {txt}")
                out.append("")
            if "table" in sec:
                cols, rows = sec["table"]["cols"], sec["table"]["rows"]
                out += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
                out += ["| " + " | ".join(r) + " |" for r in rows]
                out.append("")
    return "\n".join(out)


def build() -> None:
    import json
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from architecture_explain import EXPLAIN

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, content in EXPLAIN.items():
        path = OUT_DIR / f"explain-{key}.json"
        path.write_text(json.dumps(content, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[architecture] wrote {path.relative_to(ROOT)}")
    doc = ROOT.parent / "docs" / "how_urvi_works.md"
    doc.write_text(explain_markdown(), encoding="utf-8")
    print(f"[architecture] wrote {doc.relative_to(ROOT.parent)}")
    for d in diagrams():
        for theme, suffix in (("dark", ""), ("light", "-light")):
            path = OUT_DIR / f"{d.slug}{suffix}.html"
            path.write_text(render(d, theme), encoding="utf-8")
            print(f"[architecture] wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB, {len(d.nodes)} components)")


if __name__ == "__main__":
    build()
