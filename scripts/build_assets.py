#!/usr/bin/env python3
"""Builds the profile artwork in assets/ from the CONTENT section below.

    pip install fonttools
    python scripts/build_assets.py

GitHub shows README images through <img>, which cannot load web fonts, so every
SVG carries its own subset of IBM Plex Sans and JetBrains Mono (SIL OFL, see
scripts/fonts/). The daily activity panel (scripts/activity.py) uses the same
tokens and the ASCII font subset this script writes to
scripts/fonts/activity-fonts.css.
"""
import base64
import io
import os
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONT_DIR = os.path.join(ROOT, "scripts", "fonts")

# ------------------------------------------------------------------ tokens
BG = "#0B0D11"      # panel ground
RAISED = "#0F1218"  # inset surfaces
LINE = "#1F2631"    # hairlines inside a panel
EDGE = "#2C3442"    # outlines that must hold against GitHub's dark page
GRID = "#151A22"
TEXT = "#EDEFF2"
SOFT = "#C3C9D2"
MUTED = "#8D96A4"   # 6.5:1 on BG
DIM = "#5D6675"     # decorative only
ACCENT = "#FF6A1F"  # signal orange, 6.8:1 on BG
INK = "#160A03"     # text on accent
BLUE, GREEN, VIOLET, RED = "#6CB8FF", "#3DDC97", "#B69CFF", "#FF5A5A"

FACES = {  # key: (family, weight, file)
    "P4": ("P", 400, "ibm-plex-sans-latin-400-normal.woff"),
    "P6": ("P", 600, "ibm-plex-sans-latin-600-normal.woff"),
    "M4": ("M", 400, "jetbrains-mono-latin-400-normal.woff"),
    "M6": ("M", 600, "jetbrains-mono-latin-600-normal.woff"),
}
FALLBACK = {
    "P": "P,'IBM Plex Sans',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif",
    "M": "M,'JetBrains Mono',ui-monospace,SFMono-Regular,Consolas,monospace",
}
REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"

# ----------------------------------------------------------------- content
NAME = "Anvar Ko‘charov"  # U+2018: Plex draws U+02BB as wide as an "o"
STATUS = "OPEN TO ROLES · TASHKENT, UZBEKISTAN"
HEADLINE = ("Software engineer for web, mobile, bots and AI.",
            "I ship the model, the backend and the app around it.")
DISCIPLINES = (("FULL-STACK WEB", "ANDROID / KOTLIN", "TELEGRAM BOTS"),
               ("AI AGENTS", "LLM APPS", "COMPUTER VISION", "ML · SPEECH"))
PIPELINE = (  # the hero's event log: one plate read crossing every layer
    ("+0.04s", "VISION", ACCENT, "plate 01A123BC read · conf 0.98"),
    ("+0.11s", "API", BLUE, "parking session #4821 opened"),
    ("+0.17s", "BOT", GREEN, "driver notified in Telegram"),
    ("+0.29s", "AGENT", VIOLET, "invoice drafted, synced to app"),
)

CAPABILITIES = (
    ("layers", "Full-stack & integrations",
     "Next.js and React on Node.js or FastAPI, with auth, payments, webhooks and third-party APIs wired in.",
     ("Next.js", "FastAPI", "PostgreSQL")),
    ("phone", "Mobile apps",
     "Native Android apps in Kotlin and Jetpack Compose, plus mobile-first web apps tested from 375 px up.",
     ("Kotlin", "Jetpack Compose", "Android")),
    ("bot", "Bots & automation",
     "Telegram bots with multi-language menus, live data feeds and scheduled jobs that run on their own.",
     ("Telegram Bot API", "Node.js", "Cron")),
    ("agents", "AI agents & LLMs",
     "Assistants and tool-calling agents on Claude, OpenAI and Gemini, with rate limits and fallbacks.",
     ("Claude API", "OpenAI", "Gemini")),
    ("vision", "Computer vision",
     "License-plate recognition for gate control, plus face and hand tracking at 30+ FPS in the browser.",
     ("YOLO", "OpenCV", "MediaPipe")),
    ("wave", "Machine learning",
     "Uzbek speech recognition research: own dataset, a CNN-CTC baseline, Wav2Vec2 and Whisper.",
     ("Python", "Wav2Vec2", "Whisper")),
)

PROJECTS = (  # (file, tag, title, description, stack, linked)
    ("archai", "AI · WEB · 3D", "ArchAI Studio",
     "AI assistant for architects: code-checked floor plans, 3D models, AI renders and concept design packages.",
     ("Next.js", "three.js", "MongoDB", "Claude API"), True),
    ("anpr", "COMPUTER VISION · IOT", "ANPR Terminal",
     "License-plate recognition, gate control, parking sessions and payments for freight terminals.",
     ("YOLO", "OpenCV", "Python", "Node.js", "PostgreSQL", "React"), False),
    ("med-ai", "LLM · EDTECH", "Med AI Simulator",
     "Clinical case simulator for medical students: an AI tutor, voice input, adaptive difficulty and 3D anatomy.",
     ("Next.js", "Express", "MongoDB", "OpenAI API"), True),
    ("currency-bot", "TELEGRAM BOT", "Currency Bot",
     "Rates for 50+ currencies and precious metals, calculators, uz/en/ru menus and a daily 10:00 digest.",
     ("Node.js", "Telegram Bot API", "Scheduler"), True),
    ("uzbek-asr", "ML · SPEECH", "Uzbek Speech Recognition",
     "ASR research for Uzbek: a recorded speech dataset, a CNN-CTC baseline, and Wav2Vec2 and Whisper fine-tuning.",
     ("Python", "Wav2Vec2", "Whisper"), True),
    ("vision-detector", "COMPUTER VISION · WEB", "AI Vision Detector",
     "Real-time face and hand tracking in the browser at 30+ FPS, with no server round trips.",
     ("TensorFlow.js", "MediaPipe", "BlazeFace"), True),
)

STACK = (
    ("AI & LLM", ("Claude API", "OpenAI API", "Gemini API", "Function calling")),
    ("ML & VISION", ("Python", "YOLO", "OpenCV", "MediaPipe", "TensorFlow.js", "Wav2Vec2", "Whisper")),
    ("MOBILE", ("Kotlin", "Jetpack Compose", "Android", "Firebase")),
    ("BOTS", ("Telegram Bot API", "Webhooks", "Cron jobs")),
    ("FRONTEND", ("React", "Next.js", "TypeScript", "Tailwind CSS", "three.js")),
    ("BACKEND & DATA", ("Node.js", "NestJS", "Express", "FastAPI", "Prisma", "PostgreSQL", "MongoDB", "Redis",
                        "Supabase")),
    ("DELIVERY", ("Docker", "Git", "GitHub Actions", "Linux", "Vercel")),
)

BUTTONS = (  # (file, label, icon, icon side, primary)
    ("btn-email", "Email me", "mail", "left", True),
    ("btn-telegram", "Telegram", "send", "left", False),
    ("btn-archai", "ArchAI Studio", "arrow", "right", False),
)

# 24-unit line icons, drawn for this profile
ICONS = {
    "layers": ('<path d="M12 2.5 2.5 7.5 12 12.5l9.5-5L12 2.5Z"/>', '<path d="m2.5 12 9.5 5 9.5-5"/>',
               '<path d="m2.5 16.5 9.5 5 9.5-5"/>'),
    "phone": ('<rect x="6" y="2" width="12" height="20" rx="2.5"/>', '<path d="M10.5 18h3"/>'),
    "bot": ('<rect x="4" y="8" width="16" height="12" rx="3"/>', '<path d="M12 8V5"/>',
            '<circle cx="12" cy="3.5" r="1.2"/>', '<path d="M9.5 13.5v1.5M14.5 13.5v1.5M2 12.5v3.5M22 12.5v3.5"/>'),
    "agents": ('<circle cx="5.5" cy="6" r="2.5"/>', '<circle cx="18.5" cy="6" r="2.5"/>',
               '<circle cx="12" cy="18" r="2.5"/>', '<path d="M8 6h8M6.8 8.3l3.9 7.4M17.2 8.3l-3.9 7.4"/>'),
    "vision": ('<path d="M3 8V5.5A2.5 2.5 0 0 1 5.5 3H8M16 3h2.5A2.5 2.5 0 0 1 21 5.5V8M21 16v2.5'
               'a2.5 2.5 0 0 1-2.5 2.5H16M8 21H5.5A2.5 2.5 0 0 1 3 18.5V16"/>', '<circle cx="12" cy="12" r="3.5"/>'),
    "wave": ('<path d="M4 10v4M8 7v10M12 4v16M16 8v8M20 10.5v3"/>',),
    "mail": ('<rect x="3" y="5" width="18" height="14" rx="2.5"/>', '<path d="m3.5 7 8.5 6 8.5-6"/>'),
    "send": ('<path d="M21.5 2.5 2.5 10l7 3 12-10.5Z"/>', '<path d="m9.5 13 2.5 8 9.5-18.5"/>'),
    "arrow": ('<path d="M7 17 17 7M8.5 7H17v8.5"/>',),
}


# ------------------------------------------------------------------ engine
_metrics = {}


def advance(face, s, size, ls=0.0):
    """Rendered width of s in px, from the font's own advance widths."""
    if face not in _metrics:
        f = TTFont(os.path.join(FONT_DIR, FACES[face][2]))
        _metrics[face] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[face]
    units = sum(hmtx[cmap[ord(c)]][0] if ord(c) in cmap else upm // 2 for c in s)
    return units * size / upm + ls * len(s)


def font_face(face, chars):
    fam, weight, name = FACES[face]
    font = TTFont(os.path.join(FONT_DIR, name))
    opts = subset.Options()
    opts.layout_features = ["kern"]
    opts.hinting = False
    sub = subset.Subsetter(opts)
    sub.populate(unicodes={ord(c) for c in chars} | {0x20})
    sub.subset(font)
    font.flavor = "woff"
    buf = io.BytesIO()
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return (f"@font-face{{font-family:{fam};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{data}) format('woff')}}")


def face_classes(faces):
    return "".join(f".{k}{{font-family:{FALLBACK[FACES[k][0]]};font-weight:{FACES[k][1]}}}" for k in faces)


def attr(s):
    return escape(s, {'"': "&quot;"})


class Svg:
    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.parts, self.defs, self.css, self.chars = [], [], [], {}

    def add(self, *xml):
        self.parts.extend(xml)

    def text(self, x, y, s, face="P4", size=18, fill=TEXT, anchor=None, ls=None, cls=None):
        self.chars.setdefault(face, set()).update(s)
        a = [f'x="{x:g}"', f'y="{y:g}"', f'class="{face}{" " + cls if cls else ""}"',
             f'font-size="{size:g}"', f'fill="{fill}"']
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if ls:
            a.append(f'letter-spacing="{ls:g}"')
        return f'<text {" ".join(a)}>{escape(s)}</text>'

    def render(self):
        css = [font_face(f, c) for f, c in sorted(self.chars.items())]
        css += [face_classes(sorted(self.chars)), *self.css, REDUCED_MOTION]
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{attr(self.label)}">'
                f'<title>{escape(self.label)}</title><style>{"".join(css)}</style>'
                f'<defs>{"".join(self.defs)}</defs>{"".join(self.parts)}</svg>')

    def save(self, rel):
        path = os.path.join(ASSETS, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(self.render())
        print(f"{rel:32} {os.path.getsize(path) / 1024:6.1f} KB")


def icon(name, x, y, size, color, sw=1.75):
    s = size / 24
    return (f'<g transform="translate({x:g} {y:g}) scale({s:g})" fill="none" stroke="{color}" '
            f'stroke-width="{sw / s:g}" stroke-linecap="round" stroke-linejoin="round">'
            f'{"".join(ICONS[name])}</g>')


def chip(svg, x, y, label, face="M4", size=13, h=30, pad=12, color=SOFT, stroke=LINE,
         fill="none", ls=0, dot=None):
    """Draws a tag; returns (xml, width)."""
    w = advance(face, label, size, ls) + 2 * pad + (14 if dot else 0)
    tx = x + pad + (14 if dot else 0)
    xml = (f'<rect x="{x + .5:g}" y="{y + .5:g}" width="{w - 1:g}" height="{h - 1:g}" rx="7" '
           f'fill="{fill}" stroke="{stroke}"/>')
    if dot:
        xml += f'<circle cx="{x + pad + 3:g}" cy="{y + h / 2:g}" r="3" fill="{dot}"/>'
    xml += svg.text(tx, y + h / 2 + size * .36, label, face, size, color, ls=ls or None)
    return xml, w


def chip_row(svg, x, y, labels, max_w, gap=8, **kw):
    out, cx = [], x
    for label in labels:
        xml, w = chip(svg, cx, y, label, **kw)
        if cx + w > x + max_w:
            raise ValueError(f"chips overflow at {label!r}")
        out.append(xml)
        cx += w + gap
    return "".join(out)


def wrap(s, face, size, width):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and advance(face, trial, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def fits(label, face, size, width, ls=0):
    w = advance(face, label, size, ls)
    if w > width:
        raise ValueError(f"{label!r} is {w:.0f}px, room for {width}px")


# ------------------------------------------------------------------ pieces
def hero():
    W, H = 1280, 440
    s = Svg(W, H, f"{NAME}. {HEADLINE[0]} {HEADLINE[1]} Illustration: a gate camera reads a "
                  "license plate, then the API, a Telegram bot and an AI agent each act on it.")
    fx, fy, fw, fh = 712, 48, 504, 208  # camera frame
    s.defs += [
        f'<clipPath id="panel"><rect width="{W}" height="{H}" rx="24"/></clipPath>',
        f'<clipPath id="frame"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="14"/></clipPath>',
        f'<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M32 0H0V32" fill="none" stroke="{GRID}"/></pattern>',
        '<radialGradient id="fade" cx="78%" cy="45%" r="62%"><stop offset="0" stop-color="#fff"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>',
        f'<mask id="gridmask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>',
        f'<radialGradient id="glow" cx="76%" cy="38%" r="42%"><stop offset="0" stop-color="{ACCENT}" '
        f'stop-opacity=".10"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>',
        f'<linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>'
        f'<stop offset=".8" stop-color="{ACCENT}" stop-opacity=".18"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity=".85"/></linearGradient>',
    ]
    cycle, rows = "9s", []
    for i, start in enumerate((30, 40, 50, 60), 1):
        rows.append(f".l{i}{{animation:l{i} {cycle} ease-out infinite}}"
                    f"@keyframes l{i}{{0%,{start}%{{opacity:0;transform:translateY(6px)}}"
                    f"{start + 4}%,93%{{opacity:1;transform:translateY(0)}}98%,100%{{opacity:0}}}}")
    s.css += [
        ".ring{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 2.4s ease-out infinite}"
        "@keyframes ring{0%{opacity:.8;transform:scale(1)}100%{opacity:0;transform:scale(2.8)}}",
        ".live{animation:blink 1.6s steps(1) infinite}@keyframes blink{50%{opacity:.25}}",
        f".scan{{opacity:0;animation:scan {cycle} linear infinite}}"
        "@keyframes scan{0%{opacity:0;transform:translateX(0)}3%,19%{opacity:1}"
        f"22%,100%{{opacity:0;transform:translateX({fw + 80}px)}}}}",
        f".box{{transform-box:fill-box;transform-origin:center;animation:box {cycle} cubic-bezier(.2,.7,.2,1) infinite}}"
        "@keyframes box{0%,17%{opacity:0;transform:scale(1.25)}23%,93%{opacity:1;transform:scale(1)}"
        "98%,100%{opacity:0;transform:scale(1)}}",
        f".tag{{animation:tag {cycle} infinite}}@keyframes tag{{0%,23%{{opacity:0}}27%,93%{{opacity:1}}98%,100%{{opacity:0}}}}",
        *rows,
    ]

    s.add(f'<g clip-path="url(#panel)"><rect width="{W}" height="{H}" fill="{BG}"/>'
          f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gridmask)"/>'
          f'<rect width="{W}" height="{H}" fill="url(#glow)"/></g>',
          f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="23.5" fill="none" stroke="{LINE}"/>')

    # left column
    x0, col = 64, 620
    s.add(f'<circle class="ring" cx="{x0 + 6}" cy="84" r="5" fill="none" stroke="{GREEN}" stroke-width="1.5"/>',
          f'<circle cx="{x0 + 6}" cy="84" r="4.5" fill="{GREEN}"/>',
          s.text(x0 + 24, 89, STATUS, "M4", 15, MUTED, ls=1.2))
    fits(NAME, "P6", 72, col, -1.4)
    s.add(s.text(x0 - 3, 172, NAME, "P6", 72, TEXT, ls=-1.4))
    for i, (line, color) in enumerate(zip(HEADLINE, (SOFT, MUTED))):
        fits(line, "P4", 25, col)
        s.add(s.text(x0, 222 + i * 36, line, "P4", 25, color))
    for i, labels in enumerate(DISCIPLINES):
        s.add(chip_row(s, x0, 298 + i * 44, labels, col, gap=10, face="M4", size=14, h=34,
                       color=SOFT, stroke=EDGE, ls=1, dot=ACCENT))

    # camera frame: a truck front, cropped by the lens
    s.add(f'<rect x="{fx + .5}" y="{fy + .5}" width="{fw - 1}" height="{fh - 1}" rx="13.5" '
          f'fill="{RAISED}" stroke="{LINE}"/>')
    body = "#2A3340"
    px, py, pw, ph = 860, 168, 208, 46  # plate
    s.add(f'<g clip-path="url(#frame)">'
          f'<rect x="760" y="104" width="64" height="20" rx="10" fill="#10141A" stroke="{body}"/>'
          f'<rect x="1104" y="104" width="64" height="20" rx="10" fill="#10141A" stroke="{body}"/>'
          f'<rect x="844" y="88" width="240" height="190" rx="16" fill="#0D1015" stroke="{body}"/>'
          f'<path d="M866 108h196M866 124h196M866 140h196" stroke="#171C24" stroke-width="7" stroke-linecap="round"/>'
          f'<path d="M732 246h464" stroke="{body}"/>'
          f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="5" fill="#F2F3EF"/>'
          f'<rect x="{px + 3}" y="{py + 3}" width="{pw - 6}" height="{ph - 6}" rx="3" fill="none" '
          f'stroke="#1B1F25" stroke-width="1.2"/>'
          f'<path d="M{px + 46} {py + 8}V{py + ph - 8}" stroke="#1B1F25" stroke-width="1.2"/>'
          + s.text(px + 24, py + 32, "01", "M6", 24, "#101318", anchor="middle")
          + s.text(px + 56, py + 32, "A 123 BC", "M6", 24, "#101318")
          + f'<rect x="{px + pw - 25}" y="{py + 9}" width="15" height="11" fill="#fff" stroke="#C8CCD2" stroke-width=".5"/>'
          f'<rect x="{px + pw - 25}" y="{py + 9}" width="15" height="3.4" fill="#0099B5"/>'
          f'<rect x="{px + pw - 25}" y="{py + 16.6}" width="15" height="3.4" fill="#1EB53A"/>'
          f'<path d="M{px + pw - 25} {py + 12.8}h15M{px + pw - 25} {py + 15.8}h15" stroke="#CE1126" stroke-width=".7"/>'
          + s.text(px + pw - 17.5, py + 35, "UZ", "M6", 9, "#101318", anchor="middle")
          + f'<g class="scan"><rect x="{fx - 80}" y="{fy}" width="80" height="{fh}" fill="url(#scan)"/></g>'
          '</g>')
    s.add(s.text(fx + 18, fy + 26, "CAM 03 · GATE B", "M4", 12, DIM, ls=1.2))
    live_w = advance("M6", "LIVE", 12, 1.2)
    s.add(f'<circle class="live" cx="{fx + fw - 18 - live_w - 10:g}" cy="{fy + 22}" r="4" fill="{RED}"/>',
          s.text(fx + fw - 18, fy + 26, "LIVE", "M6", 12, SOFT, anchor="end", ls=1.2))

    # detection
    bx0, by0, bx1, by1, L = px - 12, py - 12, px + pw + 12, py + ph + 12, 16
    corners = (f"M{bx0} {by0 + L}V{by0}H{bx0 + L}M{bx1 - L} {by0}H{bx1}V{by0 + L}"
               f"M{bx1} {by1 - L}V{by1}H{bx1 - L}M{bx0 + L} {by1}H{bx0}V{by1 - L}")
    s.add(f'<g class="box"><rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" '
          f'fill="{ACCENT}" fill-opacity=".06"/><path d="{corners}" fill="none" stroke="{ACCENT}" '
          f'stroke-width="2.5"/></g>')
    label = "PLATE · 0.98"
    lw = advance("M6", label, 12, .8) + 16
    s.add(f'<g class="tag"><rect x="{bx0}" y="{by0 - 26}" width="{lw:g}" height="22" rx="4" fill="{ACCENT}"/>'
          + s.text(bx0 + 8, by0 - 10.5, label, "M6", 12, INK, ls=.8) + '</g>')

    # event log
    ly = fy + fh + 16
    s.add(f'<rect x="{fx + .5}" y="{ly + .5}" width="{fw - 1}" height="143" rx="13.5" fill="{RAISED}" stroke="{LINE}"/>')
    for i, (t, tag, color, msg) in enumerate(PIPELINE, 1):
        cy = ly + 27 + (i - 1) * 30
        fits(msg, "M4", 15, fx + fw - 18 - (fx + 158))
        s.add(f'<g class="l{i}">'
              + s.text(fx + 18, cy + 4.5, t, "M4", 12, DIM)
              + f'<rect x="{fx + 74}" y="{cy - 11}" width="70" height="22" rx="4" fill="{color}" fill-opacity=".14"/>'
              + s.text(fx + 109, cy + 4, tag, "M6", 11, color, anchor="middle", ls=.8)
              + s.text(fx + 158, cy + 5.5, msg, "M4", 15, SOFT)
              + '</g>')
    s.save("hero.svg")


def capabilities():
    cols, tw, th, gap = 3, 416, 300, 16
    W, H = cols * tw + (cols - 1) * gap, 2 * th + gap
    s = Svg(W, H, "What I build: " + "; ".join(f"{t}: {d}" for _, t, d, _ in CAPABILITIES))
    s.css.append(".t{animation:up .7s cubic-bezier(.2,.7,.2,1) both}"
                 "@keyframes up{from{opacity:0;transform:translateY(14px)}}")
    for i, (ic, title, desc, tags) in enumerate(CAPABILITIES):
        x, y = (i % cols) * (tw + gap), (i // cols) * (th + gap)
        body = [f'<rect x="{x + .5}" y="{y + .5}" width="{tw - 1}" height="{th - 1}" rx="17.5" '
                f'fill="{BG}" stroke="{EDGE}"/>',
                s.text(x + 32, y + 52, f"{i + 1:02d}", "M6", 14, ACCENT, ls=1),
                icon(ic, x + tw - 32 - 30, y + 30, 30, SOFT)]
        fits(title, "P6", 28, tw - 64)
        body.append(s.text(x + 32, y + 116, title, "P6", 28, TEXT, ls=-.3))
        lines = wrap(desc, "P4", 19, tw - 64)
        if len(lines) > 4:
            raise ValueError(f"{title}: description runs to {len(lines)} lines")
        body += [s.text(x + 32, y + 154 + j * 27, ln, "P4", 19, MUTED) for j, ln in enumerate(lines)]
        body.append(chip_row(s, x + 32, y + th - 32 - 32, tags, tw - 64, size=14, h=32))
        s.add(f'<g class="t" style="animation-delay:{i * .08:.2f}s">{"".join(body)}</g>')
    s.save("capabilities.svg")


def project_card(slug, tag, title, desc, tags, linked):
    W, H = 600, 260
    s = Svg(W, H, f"{title}. {desc} Built with {', '.join(tags)}.")
    s.add(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="{BG}" stroke="{EDGE}"/>',
          s.text(32, 50, tag, "M6", 13, ACCENT, ls=1.2))
    if linked:
        s.add(icon("arrow", W - 32 - 22, 32, 22, MUTED))
    fits(title, "P6", 30, W - 64)
    s.add(s.text(32, 98, title, "P6", 30, TEXT, ls=-.3))
    lines = wrap(desc, "P4", 19, W - 64)
    if len(lines) > 3:
        raise ValueError(f"{title}: description runs to {len(lines)} lines")
    s.add(*[s.text(32, 138 + j * 27, ln, "P4", 19, MUTED) for j, ln in enumerate(lines)])
    s.add(chip_row(s, 32, H - 32 - 32, tags, W - 64, size=14, h=32))
    s.save(f"projects/{slug}.svg")


def stack():
    W, top, row = 1280, 28, 58
    H = top * 2 + row * len(STACK)
    s = Svg(W, H, "Stack. " + " ".join(f"{k}: {', '.join(v)}." for k, v in STACK))
    s.add(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="{BG}" stroke="{EDGE}"/>')
    for i, (label, items) in enumerate(STACK):
        y = top + i * row
        if i:
            s.add(f'<path d="M32 {y}H{W - 32}" stroke="{LINE}"/>')
        s.add(s.text(40, y + row / 2 + 5.5, label, "M6", 15, ACCENT, ls=1.2),
              chip_row(s, 260, y + (row - 36) / 2, items, W - 260 - 40, gap=10, face="P4", size=17,
                       h=36, pad=14, color=SOFT, stroke=LINE, fill=RAISED))
    s.save("stack.svg")


def button(slug, label, ic, side, primary):
    H, pad, isz, gap, size = 48, 20, 20, 10, 17
    W = round(pad * 2 + isz + gap + advance("P6", label, size))
    fg = INK if primary else TEXT
    s = Svg(W, H, label)
    s.add(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="11.5" '
          f'fill="{ACCENT if primary else BG}" stroke="{ACCENT if primary else EDGE}"/>')
    ix, tx = (pad, pad + isz + gap) if side == "left" else (W - pad - isz, pad)
    s.add(icon(ic, ix, (H - isz) / 2, isz, fg, 2), s.text(tx, H / 2 + 6, label, "P6", size, fg))
    s.save(f"{slug}.svg")


def activity_fonts():
    ascii_ = {chr(c) for c in range(0x20, 0x7F)} | {"·"}
    css = "".join(font_face(f, ascii_) for f in ("P4", "P6", "M4")) + face_classes(("P4", "P6", "M4"))
    path = os.path.join(FONT_DIR, "activity-fonts.css")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(css)
    print(f"{'scripts/fonts/activity-fonts.css':32} {os.path.getsize(path) / 1024:6.1f} KB")


if __name__ == "__main__":
    hero()
    capabilities()
    for p in PROJECTS:
        project_card(*p)
    stack()
    for b in BUTTONS:
        button(*b)
    activity_fonts()
