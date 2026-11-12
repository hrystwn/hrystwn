"""Turn source-prepped.png into the 90x48 ASCII grid the cards print.

    python scripts/prep_photo.py photo.jpg   # once, needs rembg + opencv
    python scripts/make_ascii_svg.py         # writes data/portrait.txt
"""
from pathlib import Path

from PIL import Image

COLS, ROWS = 90, 48
RAMP = " .`:-=+*cs#%\\@"  # bright -> dark

root = Path(__file__).resolve().parent.parent
gray = Image.open(root / "source-prepped.png").convert("L").resize((COLS, ROWS), Image.Resampling.LANCZOS)
px = gray.load()

rows = [
    "".join(RAMP[round((1 - px[x, y] / 255) * (len(RAMP) - 1))] for x in range(COLS))
    for y in range(ROWS)
]
(root / "data" / "portrait.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
print(f"wrote data/portrait.txt - {COLS}x{ROWS}")
