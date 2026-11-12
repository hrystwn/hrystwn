#!/usr/bin/env python3
"""Render the profile README as animated SVG cards.

Reads data/contributions.json (refreshed daily by the Action) and writes
cards/*.svg. Everything a README image is allowed to do lives in here:
inline <style> keyframes, SMIL, and Poppins subset into fonts/*.woff and
base64'd into the sheet.

    python scripts/render_readme_cards.py          # animated
    STATIC=1 python scripts/render_readme_cards.py # final frame, no motion
"""
from __future__ import annotations

import base64
import json
import os
import pathlib
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANIM = not os.environ.get("STATIC")
# STATIC writes somewhere else on purpose: a preview can never be committed over the real cards.
CARDS = ROOT / "cards" if ANIM else ROOT / "cards-preview"

PAPER = "#F2FAEB"
CARD = "#FFFFFF"
INK = "#14260D"
INK2 = "#386722"
LINE = "#B1D49A"
BRAND = "#2E501E"
ACCENT = "#745613"
TINT = "#E3F0D8"
# contribution level 0..4, pale to deep (the app's green ramp)
GRAPH = [TINT, "#C4E0B0", "#8CC269", "#509823", "#2E501E"]

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


# ---------------------------------------------------------------- fonts / css
def _face(name: str, weight: int) -> str:
    b64 = base64.b64encode((ROOT / "fonts" / name).read_bytes()).decode()
    return (
        f"@font-face{{font-family:Poppins;font-style:normal;font-weight:{weight};"
        f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
    )


FACES = _face("poppins-regular.woff", 400) + _face("poppins-bold.woff", 700)

KEYFRAMES = """
text{font-family:Poppins,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.an{animation:rise .7s cubic-bezier(.23,1,.32,1) both}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.pop{transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.23,1,.32,1) both}
@keyframes pop{from{opacity:0;transform:scale(.35)}to{opacity:1;transform:none}}
.grow{transform-box:fill-box;transform-origin:bottom;animation:grow .8s cubic-bezier(.23,1,.32,1) both}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.sway{transform-box:fill-box;transform-origin:center;animation:sway 3.4s ease-in-out infinite}
@keyframes sway{0%,100%{transform:translateX(0)}50%{transform:translateX(4px)}}
"""
if ANIM:
    NO_MOTION = "@media (prefers-reduced-motion:reduce){.an,.pop,.grow,.sway{animation:none}}"
else:
    NO_MOTION = ".an,.pop,.grow,.sway{animation:none}"


def svg(w: int, h: int, title: str, desc: str, body: str, defs: str = "", css: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
        f'<title id="t">{esc(title)}</title>\n<desc id="d">{esc(desc)}</desc>\n'
        f"<style>{FACES}{KEYFRAMES}{NO_MOTION}{css}</style>\n"
        f"<defs>{defs}</defs>\n{body}\n</svg>\n"
    )


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def delay(ms: int) -> str:
    return f' style="animation-delay:{ms}ms"' if ANIM else ' style="animation:none"'


def surface(w: int, h: int, fill: str = PAPER, rx: int = 16) -> str:
    return (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" '
        f'fill="{fill}" stroke="{LINE}"/>'
    )


def txt(x, y, s, size=13, fill=INK, weight=400, extra="", cls="") -> str:
    c = f' class="{cls}"' if cls else ""
    return (
        f'<text{c}{extra} x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}">{esc(s)}</text>'
    )


# ---------------------------------------------------------------- hero
def hero(name: str, portrait: list[str], site: dict) -> str:
    w, h = 860, 460
    art_x, art_y = 456, 90
    font, line_h, char_w = 8.3, 7.2, 3.96
    art_w, art_h = len(portrait[0]) * char_w, len(portrait) * line_h

    clips, rows, cursors = [], [], []
    for i, row in enumerate(portrait):
        top = art_y + i * line_h
        base = top + font * 0.92
        begin = (350 + i * 18) / 1000
        if ANIM:
            clips.append(
                f'<clipPath id="c{i}"><rect x="{art_x}" y="{top - 1:.1f}" width="0" height="{line_h + 2:.1f}">'
                f'<animate attributeName="width" from="0" to="{art_w:.1f}" begin="{begin:.3f}s" '
                f'dur=".24s" fill="freeze"/></rect></clipPath>'
            )
            rows.append(
                f'<g clip-path="url(#c{i})"><text class="a" x="{art_x}" y="{base:.1f}" xml:space="preserve" '
                f'textLength="{art_w:.1f}" lengthAdjust="spacingAndGlyphs">{esc(row)}</text></g>'
            )
            cursors.append(
                f'<rect x="{art_x}" y="{top:.1f}" width="4" height="{line_h - 1:.1f}" fill="{INK}" opacity="0">'
                f'<animate attributeName="x" from="{art_x}" to="{art_x + art_w - 4:.1f}" begin="{begin:.3f}s" '
                f'dur=".24s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="0;.35;.35;0" keyTimes="0;.02;.9;1" '
                f'begin="{begin:.3f}s" dur=".24s" fill="freeze"/></rect>'
            )
        else:
            rows.append(
                f'<text class="a" x="{art_x}" y="{base:.1f}" xml:space="preserve" '
                f'textLength="{art_w:.1f}" lengthAdjust="spacingAndGlyphs">{esc(row)}</text>'
            )

    shine = (
        f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{INK}"/><stop offset=".44" stop-color="{INK}"/>'
        f'<stop offset=".5" stop-color="{BRAND}"/><stop offset=".56" stop-color="{INK}"/>'
        f'<stop offset="1" stop-color="{INK}"/>'
        + (
            f'<animateTransform attributeName="gradientTransform" type="translate" '
            f'from="-.45 0" to=".45 0" begin="1.8s" dur="4.5s" repeatCount="indefinite"/>'
            if ANIM
            else ""
        )
        + "</linearGradient>"
    )

    body = [
        surface(w, h),
        txt(56, 88, "SOLO FOUNDER · TENANG", 11, INK2, 700, ' letter-spacing="2.4"', "an"),
        f'<text class="an"{delay(120)} x="56" y="158" fill="url(#shine)" font-size="64" font-weight="700">Hery</text>',
        f'<text class="an"{delay(220)} x="56" y="226" fill="url(#shine)" font-size="64" font-weight="700">Setiawan</text>',
        f'<line class="an"{delay(320)} x1="56" y1="252" x2="392" y2="252" stroke="{LINE}"/>',
        txt(56, 288, "I build Tenang, a private mental wellness app.", 15, INK, 400, "", "an"),
        txt(56, 312, "Moods, journals and self-checks that stay", 15, INK, 400, "", "an"),
        txt(56, 336, "encrypted on the device.", 15, INK, 400, "", "an"),
        f'<circle class="an"{delay(560)} cx="61" cy="373" r="4" fill="{BRAND}"/>',
        txt(76, 378, "Tenang is live on the App Store" if site.get("appStore")
            else "Tenang is in private beta on TestFlight", 12.5, INK2, 400, "", "an"),
        txt(56, 412, "TypeScript · React Native · Expo · Supabase", 11.5, INK2, 400, ' letter-spacing=".3"'),
        '<g fill="' + INK + '" opacity=".92">' + "".join(rows) + "</g>",
        "".join(cursors),
    ]
    return svg(
        w,
        h,
        "Hery Setiawan — solo founder of Tenang",
        "Paper card: Hery Setiawan, solo founder of Tenang, a private mental wellness app. "
        "An ASCII portrait prints in row by row on the right.",
        "\n".join(body),
        defs="".join(clips) + shine,
        css=f".a{{font-family:{MONO};font-size:{font}px;white-space:pre}}",
    )


# ---------------------------------------------------------------- graph
def graph(days: list[dict], total: int) -> str:
    w, h, cell, gap = 860, 196, 9, 3
    pitch = cell + gap
    gx, gy = 56, 66

    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    cols = (last - start).days // 7 + 1

    cells = []
    for day in days:
        d = date.fromisoformat(day["date"])
        col, row = (d - start).days // 7, (d - start).days % 7
        lvl = min(max(int(day["level"]), 0), 4)
        dly = (col + row) * 9
        cells.append(
            f'<rect class="pop"{delay(dly)} x="{gx + col * pitch}" y="{gy + row * pitch}" '
            f'width="{cell}" height="{cell}" rx="2" fill="{GRAPH[lvl]}"/>'
        )

    months = []
    for day in days:
        d = date.fromisoformat(day["date"])
        if d.day == 1:
            col = (d - start).days // 7
            months.append(txt(gx + col * pitch, gy - 10, d.strftime("%b"), 10, INK2))
    weekdays = [txt(gx - 10, gy + r * pitch + 8, label, 9.5, INK2, 400, ' text-anchor="end"')
                for r, label in ((1, "Mon"), (3, "Wed"), (5, "Fri"))]

    legend = "".join(
        f'<rect x="{712 + i * pitch}" y="{gy + 7 * pitch + 10}" width="{cell}" height="{cell}" '
        f'rx="2" fill="{GRAPH[i]}"/>'
        for i in range(5)
    )
    body = [
        surface(w, h),
        txt(40, 38, "PUBLIC CONTRIBUTION GRAPH · LAST 12 MONTHS", 11, INK2, 700, ' letter-spacing="2"', "an"),
        txt(820, 38, f"{total} this year", 11.5, INK2, 400, ' text-anchor="end"', "an"),
        f'<g class="an"{delay(120)}>{"".join(months)}{"".join(weekdays)}</g>',
        *cells,
        legend,
        txt(712, gy + 7 * pitch + 8, "less", 9, INK2, 400, ' text-anchor="end"'),
        txt(712 + 5 * pitch + 2, gy + 7 * pitch + 8, "more", 9, INK2),
    ]
    return svg(
        w, h, "Contribution graph", "Contribution squares for the last twelve months, popping in left to right.",
        "\n".join(body),
    )


# ---------------------------------------------------------------- activity
def activity(days: list[dict], stats: dict, total: int) -> str:
    w, h = 860, 260
    months: dict[tuple[int, int], int] = {}
    for day in days:
        d = date.fromisoformat(day["date"])
        key = (d.year, d.month)
        months[key] = months.get(key, 0) + int(day["count"])
    recent = sorted(months)[-12:]
    peak = max(months[k] for k in recent) or 1
    best = max(recent, key=lambda k: months[k])

    base_y, max_h, bar_w = 196, 118, 16
    bars = []
    for i, key in enumerate(recent):
        value = months[key]
        height = round(value / peak * max_h, 1) if value else 2
        x = 44 + i * 34
        fill = BRAND if key == best else "#8CC269"
        bars.append(
            f'<rect class="grow"{delay(150 + i * 45)} x="{x}" y="{base_y - height}" width="{bar_w}" '
            f'height="{height}" rx="3" fill="{fill}"/>'
        )
        bars.append(txt(x + bar_w / 2, base_y + 18, date(key[0], key[1], 1).strftime("%b"),
                        9.5, BRAND if key == best else INK2, 400, ' text-anchor="middle"'))
    label = txt(44 + recent.index(best) * 34 + bar_w / 2, base_y - months[best] / peak * max_h - 10,
                str(months[best]), 12, BRAND, 700, ' text-anchor="middle"', "an")

    streak = stats["currentStreak"]
    longest = stats["longestStreak"]
    busiest = stats["bestDay"]
    busy_d = date.fromisoformat(busiest["date"])
    busy_date = f"{busy_d.strftime('%b')} {busy_d.day}"

    counter = count_up(total, 520, 118, 46)
    body = [
        surface(w, h),
        txt(40, 38, "PUBLIC CONTRIBUTIONS PER MONTH", 11, INK2, 700, ' letter-spacing="2"', "an"),
        f'<line x1="40" y1="{base_y}" x2="440" y2="{base_y}" stroke="{LINE}"/>',
        *bars,
        label,
        f'<line x1="480" y1="52" x2="480" y2="212" stroke="{LINE}"/>',
        counter,
        txt(520, 146, "public contributions in the last year", 11.5, INK2, 400, "", "an"),
        txt(520, 184, f"{streak}-day current streak", 13, INK, 400, "", "an"),
        txt(520, 208, f"longest {longest} · busiest {busiest['count']} on {busy_date}", 13, INK, 400, "", "an"),
    ]
    return svg(
        w, h, "Contributions per month",
        "Monthly contribution bars with streak, longest run and busiest day.",
        "\n".join(body),
    )


def count_up(total: int, x: int, y: int, size: int) -> str:
    """SMIL can't change text, so the count-up is one text node per frame."""
    if not ANIM:
        return txt(x, y, str(total), size, INK, 700)
    frames = 17
    out = []
    for i in range(frames):
        value = round(total * i / frames)
        begin = 0.45 + i * 0.045
        out.append(
            f'<text x="{x}" y="{y}" fill="{INK}" font-size="{size}" font-weight="700" opacity="0">'
            f'{value}<animate attributeName="opacity" values="0;1;0" keyTimes="0;.5;1" '
            f'begin="{begin:.3f}s" dur=".09s" fill="remove"/></text>'
        )
    out.append(
        f'<text x="{x}" y="{y}" fill="{INK}" font-size="{size}" font-weight="700" opacity="0">{total}'
        f'<set attributeName="opacity" to="1" begin="{0.45 + frames * 0.045:.3f}s"/></text>'
    )
    return "".join(out)


# ---------------------------------------------------------------- tiles
TILES = [
    ("01", "Tenang", "A private mental wellness app.", None),
    ("02", "Code", "Open-source tools and experiments.", "github.com/hrystwn"),
    ("03", "Writing", "Notes on privacy, shipping and product.", None),
]


def tile(index: int, site: dict) -> str:
    w, h = 280, 196
    num, title, line1, line2 = TILES[index]
    if index == 0:
        line2 = "App Store · iOS + Android" if site.get("appStore") else "Private beta · TestFlight"
    elif index == 2:
        line2 = f"{site['posts']} posts" if site.get("posts") else "tenangmail.com/blog"
    sweep = (
        f'<rect x="0" y="0" width="70" height="{h}" fill="url(#sw)" opacity=".55">'
        f'<animateTransform attributeName="transform" type="translate" from="-90 0" to="{w + 40} 0" '
        f'begin="{2.6 + index * 0.2:.1f}s" dur="5.5s" repeatCount="indefinite"/></rect>'
        if ANIM else ""
    )
    ring = (
        f'<circle cx="0" cy="{h}" r="10" fill="none" stroke="{BRAND}" stroke-width="1.5" opacity="0">'
        f'<animate attributeName="r" values="10;150" begin="{1 + index * 0.15:.2f}s" dur="4.5s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values=".35;0" begin="{1 + index * 0.15:.2f}s" dur="4.5s" repeatCount="indefinite"/>'
        "</circle>"
        if ANIM else ""
    )
    body = [
        surface(w, h, CARD, 14),
        sweep,
        ring,
        txt(24, 46, num, 11, ACCENT, 700, ' letter-spacing="2"'),
        txt(24, 96, title, 23, INK, 700),
        txt(24, 126, line1, 11.5, INK2),
        txt(24, 146, line2, 11.5, INK2),
        f'<g class="sway"{delay(900 + index * 120)}><path d="M228 168h20m0 0-6-6m6 6-6 6" '
        f'fill="none" stroke="{BRAND}" stroke-width="1.6" stroke-linecap="round"/></g>',
    ]
    payload = "\n".join(body)
    if ANIM:
        payload = f'<g class="an">{payload}</g>'
    return svg(
        w, h, title, f"{title} — {line1} {line2}", payload,
        defs=f'<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="{TINT}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="{TINT}"/><stop offset="1" stop-color="{TINT}" stop-opacity="0"/></linearGradient>',
    )


# ---------------------------------------------------------------- work cards
def work_card(name: str, kind: str, blurb: str, meta: str, i: int) -> str:
    w, h = 416, 154
    body = [
        surface(w, h, CARD, 14),
        txt(26, 40, kind, 10.5, ACCENT, 700, ' letter-spacing="1.8"'),
        txt(26, 76, name, 21, INK, 700),
        txt(26, 104, blurb, 11.5, INK2),
        txt(26, 128, meta, 11, INK2),
    ]
    payload = "\n".join(f'<g class="an"{delay(180 + i * 140)}>{line}</g>' for line in body)
    return svg(w, h, name, f"{kind}: {name}. {blurb} {meta}", payload)


# ---------------------------------------------------------------- build
# Written next to the cards every run so a preview can never point at the wrong
# directory. Layout mirrors a GitHub README column: 860 max, everything fluid.
PREVIEW = """<!doctype html>
<html><head><meta charset="utf-8"><title>README preview</title><style>
body{{margin:0;background:#fff;padding:16px}}
.wrap{{max-width:860px;margin:0 auto}}
img{{display:block;width:100%;margin-bottom:12px}}
.row{{display:flex;gap:6px;align-items:flex-start;margin-bottom:12px}}
.row img{{margin:0}}
</style></head><body><div class="wrap">
<img src="{dir}/hero.svg">
<img src="{dir}/graph.svg">
<img src="{dir}/activity.svg">
<div class="row">
<img src="{dir}/tile-tenang.svg"><img src="{dir}/tile-code.svg"><img src="{dir}/tile-writing.svg">
</div>
<div class="row">
<img src="{dir}/work-tenang.svg"><img src="{dir}/work-ai-job-search.svg">
</div>
</div></body></html>
"""


def main() -> None:
    data = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))
    days, total, stats = data["days"], data["total"], data["stats"]
    portrait = (ROOT / "data" / "portrait.txt").read_text(encoding="utf-8").splitlines()
    assert len(portrait) == 48 and all(len(r) == 90 for r in portrait), "portrait.txt must be 90x48"
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8")) \
        if (ROOT / "data" / "site.json").exists() else {}

    CARDS.mkdir(exist_ok=True)
    out = {
        "hero.svg": hero(data["username"], portrait, site),
        "graph.svg": graph(days, total),
        "activity.svg": activity(days, stats, total),
        "tile-tenang.svg": tile(0, site),
        "tile-code.svg": tile(1, site),
        "tile-writing.svg": tile(2, site),
        "work-tenang.svg": work_card(
            "Tenang", "BUILDING", "Private, unhurried mental wellness.", "tenangmail.com · iOS + Android", 0),
        "work-ai-job-search.svg": work_card(
            "ai-job-search", "OPEN SOURCE", "A job search that runs on your machine.", "TypeScript · Claude Code", 1),
    }
    for name, content in out.items():
        (CARDS / name).write_text(content, encoding="utf-8")
    (ROOT / "preview.html").write_text(PREVIEW.format(dir=CARDS.name), encoding="utf-8")
    mode = "animated" if ANIM else "static"
    print(f"wrote {len(out)} cards ({mode}) to {CARDS.name}/ + preview.html - {total} contributions, {len(days)} days")


if __name__ == "__main__":
    main()
