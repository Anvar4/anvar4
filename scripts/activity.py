#!/usr/bin/env python3
"""Draws assets/activity.svg from live GitHub data. Run daily by
.github/workflows/activity.yml, so the README never depends on a third-party
stats service. On any API error the previous image stays in place."""
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime

LOGIN = os.environ.get("STATS_LOGIN", "Anvar4")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "activity.svg")
# ASCII subsets of IBM Plex Sans and JetBrains Mono, written by build_assets.py
FONT_CSS = os.path.join(HERE, "fonts", "activity-fonts.css")

# same tokens as build_assets.py
GROUND, EDGE = "#0B0D11", "#2C3442"
ACCENT, TEXT, SOFT, MUTED = "#FF6A1F", "#EDEFF2", "#C3C9D2", "#8D96A4"
LEVELS = ["#161B22", "#4A220C", "#8A3812", "#D45218", "#FF7A35"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}",
                 "Content-Type": "application/json", "User-Agent": "profile-activity"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        payload = json.load(res)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def streaks(days, today):
    """Longest run overall, and the run still alive today. A quiet today does
    not end the current streak, because the day is not over yet."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    current = 0
    for d in reversed(days):
        if d["contributionCount"]:
            current += 1
        elif d["date"] != today:
            break
    return current, longest


def languages(user, top=6):
    sizes, colors = Counter(), {}
    for repo in user["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            sizes[e["node"]["name"]] += e["size"]
            colors[e["node"]["name"]] = e["node"]["color"] or MUTED
    total = sum(sizes.values()) or 1
    return [(n, s / total, colors[n]) for n, s in sizes.most_common(top)]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def t(x, y, s, size, fill=TEXT, face="P4", anchor="start", ls=0):
    spacing = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x}" y="{y}" class="{face}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}"{spacing}>{esc(str(s))}</text>')


def font_css():
    try:
        with open(FONT_CSS, encoding="utf-8") as fh:
            return fh.read()
    except OSError:  # system fonts still render; the panel just looks plainer
        return ""


def render(user, today=None):
    today = today or date.today().isoformat()
    col = user["contributionsCollection"]
    cal = col["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    current, longest = streaks(days, today)
    W, M = 1280, 48
    stats = [(f"{cal['totalContributions']:,}", "CONTRIBUTIONS · 12 MO"),
             (f"{sum(1 for d in days if d['contributionCount'])}", "ACTIVE DAYS"),
             (f"{current}", "CURRENT STREAK"),
             (f"{longest}", "LONGEST STREAK"),
             (f"{user['repositories']['totalCount']}", "REPOSITORIES")]
    b = []
    colw = (W - 2 * M) / len(stats)
    for i, (v, label) in enumerate(stats):
        x = round(M + i * colw)
        b.append(t(x, 96, v, 54, TEXT, "P6", ls=-1))
        b.append(t(x, 126, label, 13, ACCENT if i == 0 else MUTED, "M4", ls=1.2))

    # contribution calendar, quantised against the busiest day
    peak = max((d["contributionCount"] for d in days), default=0) or 1
    n = len(weeks)
    pitch = (W - 2 * M + 4) / max(n, 1)
    size = pitch - 4
    top = 164
    months, last = [], None
    for i, w in enumerate(weeks):
        for j, d in enumerate(w["contributionDays"]):
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            c = d["contributionCount"]
            lvl = 0 if not c else min(4, 1 + int(3.999 * c / peak))
            b.append(f'<rect x="{M + i * pitch:.1f}" y="{top + 22 + dt.isoweekday() % 7 * pitch:.1f}" '
                     f'width="{size:.1f}" height="{size:.1f}" rx="3" fill="{LEVELS[lvl]}"/>')
        m = datetime.strptime(w["contributionDays"][0]["date"], "%Y-%m-%d")
        if m.month != last and i < n - 2:
            months.append(t(round(M + i * pitch), top + 10, m.strftime("%b").upper(), 12, MUTED, "M4", ls=1))
            last = m.month
    b.extend(months)
    y = top + 22 + 7 * pitch + 22

    # language share
    langs = languages(user)
    if langs:
        share = sum(p for _, p, _ in langs) or 1
        x, bar = M, W - 2 * M
        for name, p, color in langs:
            w_ = bar * p / share
            b.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w_ - 3, 1):.1f}" height="12" rx="3" fill="{color}"/>')
            x += w_
        lw = bar / len(langs)
        for i, (name, p, color) in enumerate(langs):
            lx = round(M + i * lw)
            b.append(f'<circle cx="{lx + 6}" cy="{y + 40}" r="6" fill="{color}"/>')
            b.append(t(lx + 20, y + 46, f"{name} {p * 100:.0f}%", 16, SOFT))
        y += 56
    H = round(y + 26)
    alt = (f"GitHub activity: {cal['totalContributions']} contributions in the last 12 months, "
           f"current streak {current} days, longest streak {longest} days.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-label="{esc(alt)}"><title>{esc(alt)}</title><style>{font_css()}</style>'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="{GROUND}" stroke="{EDGE}"/>'
            f'{"".join(b)}</svg>')


if __name__ == "__main__":
    try:
        svg = render(fetch())
    except Exception as exc:  # keep the last good image on the profile
        print(f"Activity not updated: {exc}", file=sys.stderr)
        sys.exit(1)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("Wrote", os.path.normpath(OUT))
