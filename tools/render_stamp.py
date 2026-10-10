"""Animate the approved vector cover as a rubber-stamp impression.

Optional artwork tool: requires Pillow, Node.js and the Sharp package.
Pass --sharp-module /path/to/node_modules/sharp when Sharp is installed elsewhere.
No browser, network or image-generation service is used by this renderer.
"""

import argparse
import base64
from io import BytesIO
import json
from pathlib import Path
import subprocess

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", default="node")
    parser.add_argument("--sharp-module", default="sharp")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = (root / "assets/receipt.svg").read_text(encoding="utf-8")
    marker = 'transform="translate(835 120) rotate(-6 175 100)"'
    if source.count(marker) != 1:
        raise SystemExit("Cover stamp group changed; review its animation coordinates.")

    variants, durations = [], []

    def add(y=0, scale_x=1, scale_y=1, angle=-6, opacity=1, duration=40):
        transform = (
            f'transform="translate(835 {120 + y:.3f}) rotate({angle:.3f} 175 100) '
            f'translate(179 98) scale({scale_x:.4f} {scale_y:.4f}) translate(-179 -98)" '
            f'opacity="{opacity:.4f}"'
        )
        variants.append(source.replace(marker, transform))
        durations.append(duration)

    add(opacity=0, duration=450)
    # Accelerate toward the page; the final impact is deliberately brief.
    for i in range(13):
        t = i / 12
        fall = t * t
        scale = 1.16 - .16 * fall
        add(y=-105 * (1 - fall), scale_x=scale, scale_y=scale,
            angle=-12 + 6 * fall, opacity=.22 + .78 * t)
    add(y=5, scale_x=1.035, scale_y=.965, duration=45)
    add(y=3, scale_x=1.02, scale_y=.982, duration=45)
    add(y=-2, scale_x=.998, scale_y=1.008, duration=50)
    add(duration=4400)
    # Quiet hold, then clear the impression before the next stamp.
    for opacity in (.75, .5, .25, 0):
        add(opacity=opacity, duration=50)

    renderer = """
const fs = require('fs');
const sharp = require(process.argv[1]);
const svgs = JSON.parse(fs.readFileSync(0, 'utf8'));
(async () => {
  const frames = [];
  for (const svg of svgs) frames.push((await sharp(Buffer.from(svg)).png().toBuffer()).toString('base64'));
  process.stdout.write(JSON.stringify(frames));
})().catch(e => {console.error(e.message); process.exit(1)});
"""
    result = subprocess.run([args.node, "-e", renderer, args.sharp_module],
                            input=json.dumps(variants), capture_output=True,
                            text=True, check=True)
    frames = [Image.open(BytesIO(base64.b64decode(frame))).convert("RGB")
              for frame in json.loads(result.stdout)]
    # One shared palette keeps static typography stable between frames.
    palette = frames[17].quantize(colors=128)
    encoded = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    destination = root / "assets/receipt-stamp.gif"
    encoded[0].save(destination, save_all=True, append_images=encoded[1:],
                    duration=durations, loop=0, disposal=1, optimize=True)
    frames[17].save(root / "assets/receipt-stamp.png", optimize=True)
    print(f"Rendered {len(frames)} frames; {destination.stat().st_size} bytes.")


if __name__ == "__main__":
    main()
