"""Render README artwork from the runnable synthetic demo. Requires Pillow.

Optional maintainer tool; not required to use skills or run repository checks.
Usage: python tools/render_demo.py --font /path/to/bold.ttf --mono /path/to/mono.ttf
The GIF plays once. The PNG is its final, static frame.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, required=True, help="local bold TrueType font")
    parser.add_argument("--mono", type=Path, required=True, help="local monospace TrueType font")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "examples/false_green.py"), "--json"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    if not (data["synthetic"] and data["verifier"]["exit_code"] == 1
            and data["summarizer"]["exit_code"] == 0
            and data["verdict"]["state"] == "FAIL"):
        raise SystemExit("Demo no longer matches this visual narrative; review before rendering.")

    # Publish only synthetic output and portable provenance, never local argv paths.
    evidence = {
        "source": "examples/false_green.py",
        "source_sha256": hashlib.sha256((root / "examples/false_green.py").read_bytes()).hexdigest(),
        "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "synthetic": True,
        "label": data["label"],
        "verifier": {k: data["verifier"][k] for k in ("output", "exit_code")},
        "summarizer": {k: data["summarizer"][k] for k in ("output", "exit_code")},
        "verdict": {k: data["verdict"][k] for k in ("state", "exit_code", "reason")},
        "demo_exit_meaning": data["demo_exit_meaning"],
        "note": "Local interpreter paths omitted. Run the source with --json for full argv.",
    }

    bg, panel, line = "#111713", "#1b241e", "#37473b"
    white, muted, red, green = "#f2efe7", "#b4c0b5", "#ff8068", "#c4ef8b"
    fonts = {
        "large": ImageFont.truetype(str(args.font), 53),
        "medium": ImageFont.truetype(str(args.font), 32),
        "small": ImageFont.truetype(str(args.mono), 20),
        "mono": ImageFont.truetype(str(args.mono), 23),
        "label": ImageFont.truetype(str(args.font), 19),
    }

    def frame(stage, progress=1.0):
        im = Image.new("RGB", (1200, 660), bg)
        d = ImageDraw.Draw(im)
        d.text((44, 27), "GRIT / EVIDENCE LAB", fill=muted, font=fonts["label"])
        d.text((884, 27), "SYNTHETIC DEMO", fill=muted, font=fonts["label"])
        heading = ("A green exit. A failed check.", "Follow the result upstream.",
                   "The receipt tells the truth.")[stage]
        d.text((42, 69), heading, fill=white, font=fonts["large"])
        d.line((44, 148, 1156, 148), fill=line, width=2)
        d.rounded_rectangle((44, 180, 1156, 371), radius=12, fill=panel)
        d.text((68, 199), "01  THE VERIFIER", fill=muted, font=fonts["label"])
        output = data["verifier"]["output"].strip()
        visible = output[:max(1, int(len(output) * progress))] if stage == 0 else output
        d.text((68, 244), visible, fill=white, font=fonts["mono"])
        d.text((68, 299), "own exit", fill=muted, font=fonts["small"])
        d.text((207, 288), str(data["verifier"]["exit_code"]), fill=red, font=fonts["medium"])
        d.text((553, 299), "output passed to summarizer", fill=muted, font=fonts["small"])
        d.line((1021, 309, 1112, 309), fill=muted, width=2)
        d.polygon(((1112, 309), (1101, 303), (1101, 315)), fill=muted)
        d.rounded_rectangle((44, 393, 577, 561), radius=12, fill=panel)
        d.rounded_rectangle((599, 393, 1156, 561), radius=12, fill=panel,
                            outline=green if stage == 2 else line, width=2)
        d.text((68, 414), "02  THE OUTPUT CONSUMER", fill=muted, font=fonts["label"])
        d.text((623, 414), "03  THE COMPLETION RECEIPT", fill=muted, font=fonts["label"])
        if stage >= 1:
            d.text((68, 453), f"exit {data['summarizer']['exit_code']}", fill=green, font=fonts["medium"])
            d.text((68, 508), "It displayed output. That's all.", fill=muted, font=fonts["small"])
        else:
            d.text((68, 463), "Waiting for the output...", fill=muted, font=fonts["small"])
        if stage == 2:
            d.text((623, 453), data["verdict"]["state"], fill=red, font=fonts["medium"])
            d.text((623, 508), "Verifier exit: 1. Not verified.", fill=white, font=fonts["small"])
        else:
            d.text((623, 463), "Trace the command's own exit.", fill=muted, font=fonts["small"])
        d.text((44, 600), "RUN IT: python examples/false_green.py", fill=muted, font=fonts["small"])
        for index in range(3):
            x = 1005 + index * 52
            d.rounded_rectangle((x, 607, x + 38, 612), radius=2,
                                fill=green if index <= stage else line)
        return im

    frames = [frame(0, p / 12) for p in range(1, 13)]
    durations = [65] * 11 + [1700]
    frames.extend([frame(1), frame(2)])
    durations.extend([2300, 3000])
    palette = frames[-1].quantize(colors=128)
    frames = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
    assets = root / "assets"
    assets.mkdir(exist_ok=True)
    frames[0].save(assets / "false-green.gif", save_all=True, append_images=frames[1:],
                   duration=durations, disposal=1, optimize=True)
    frame(2).save(assets / "false-green.png", optimize=True)
    (assets / "demo-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    for name in ("false-green.gif", "false-green.png", "demo-evidence.json"):
        print(f"{name}: {(assets / name).stat().st_size} bytes")


if __name__ == "__main__":
    main()
