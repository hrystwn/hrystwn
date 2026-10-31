from pathlib import Path

from PIL import Image

COLS, ROWS = 90, 48
RAMP = " .`:-=+*cs#%\\@"  # bright -> dark
FONT = 6.6
LINE_H = 7.2
CHAR_W = FONT * 0.6
ART_W = COLS * CHAR_W
ART_H = ROWS * LINE_H
ART_X = 12
ART_Y = 52
W = 380
H = round(ART_Y + ART_H + 16)
ROW_MS = 40
WIPE_MS = 300

root = Path(__file__).resolve().parent.parent
gray = Image.open(root / "source-prepped.png").convert("L").resize((COLS, ROWS), Image.Resampling.LANCZOS)
px = gray.load()

rows = []
for y in range(ROWS):
    rows.append("".join(RAMP[round((1 - px[x, y] / 255) * (len(RAMP) - 1))] for x in range(COLS)))

clips = []
groups = []
cursors = []
for i, row in enumerate(rows):
    top = ART_Y + i * LINE_H
    baseline = top + FONT * 0.92
    begin = i * ROW_MS / 1000
    clips.append(
        f'    <clipPath id="clip{i}"><rect x="{ART_X}" y="{top - 1:.2f}" width="0" height="{LINE_H + 2:.2f}">'
        f'<animate attributeName="width" from="0" to="{ART_W:.2f}" begin="{begin:.3f}s" dur="{WIPE_MS / 1000}s" fill="freeze"/>'
        f"</rect></clipPath>"
    )
    groups.append(
        f'  <g clip-path="url(#clip{i})"><text class="a" x="{ART_X}" y="{baseline:.2f}" xml:space="preserve">{row}</text></g>'
    )
    cursors.append(
        f'  <rect x="{ART_X}" y="{top:.2f}" width="4" height="{LINE_H - 1:.2f}" fill="#c9d1d9" opacity="0">'
        f'<animate attributeName="x" from="{ART_X}" to="{ART_X + ART_W - 4:.2f}" begin="{begin:.3f}s" dur="{WIPE_MS / 1000}s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.02;0.9;1" begin="{begin:.3f}s" dur="{WIPE_MS / 1000}s" fill="freeze"/>'
        f"</rect>"
    )

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
  <title id="title">Hery Setiawan — ASCII portrait</title>
  <desc id="desc">Monochrome ASCII portrait of Hery Setiawan, printed row by row.</desc>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
    .a {{ fill: #8b949e; font-size: {FONT}px; }}
  </style>
  <defs>
{chr(10).join(clips)}
  </defs>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
  <circle cx="20" cy="20" r="5" fill="#ff5f56"/>
  <circle cx="36" cy="20" r="5" fill="#ffbd2e"/>
  <circle cx="52" cy="20" r="5" fill="#27c93f"/>
  <text x="68" y="25" fill="#8b949e" font-size="12">hrystwn@github: ~/portrait</text>
  <line x1="1" y1="38" x2="{W - 1}" y2="38" stroke="#30363d"/>
{chr(10).join(groups)}
{chr(10).join(cursors)}
</svg>
"""

(root / "ascii-portrait.svg").write_text(svg, encoding="utf-8")
print(f"wrote {root / 'ascii-portrait.svg'} · {COLS}x{ROWS} · {W}x{H}")
