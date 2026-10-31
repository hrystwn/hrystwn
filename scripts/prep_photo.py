import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

src = Path(sys.argv[1])
out = Path(__file__).resolve().parent.parent / "source-prepped.png"

img = Image.open(src).convert("RGBA")
session = new_session("u2net")
cut = remove(img, session=session)

arr = np.array(cut)
alpha = arr[..., 3].astype(np.float32) / 255.0
gray = cv2.cvtColor(arr[..., :3].astype(np.uint8), cv2.COLOR_RGB2GRAY)
boost = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(8, 8)).apply(gray)
composite = boost.astype(np.float32) * alpha + 255.0 * (1.0 - alpha)
result = np.clip(composite, 0, 255).astype(np.uint8)

Image.fromarray(result, mode="L").save(out)
print(f"wrote {out} {result.shape[1]}x{result.shape[0]}")
