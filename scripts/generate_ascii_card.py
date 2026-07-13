#!/usr/bin/env python3
"""Generate pure-glyph colored ASCII profile card (NOT pixel blocks).

Requires: ascii-image-converter in PATH (~/.local/bin), pillow, cairosvg optional.

  python scripts/generate_ascii_card.py
  python scripts/generate_ascii_card.py --photo path/to/face.png
"""
from __future__ import annotations
import argparse, subprocess, shutil
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps, ImageFilter

ROOT = Path(__file__).resolve().parents[1]

def prep(photo: Path, out: Path) -> Path:
    im = Image.open(photo).convert("RGB")
    w, h = im.size
    side = int(min(w, h) * 0.72)
    cx, cy = w // 2, int(h * 0.40)
    x0 = max(0, min(w - side, cx - side // 2))
    y0 = max(0, min(h - side, cy - side // 2))
    face = im.crop((x0, y0, x0 + side, y0 + side)).resize((800, 800), Image.Resampling.LANCZOS)
    face = ImageOps.autocontrast(face, cutoff=1.0)
    face = ImageEnhance.Contrast(face).enhance(1.4)
    face = ImageEnhance.Color(face).enhance(1.25)
    face = ImageEnhance.Sharpness(face).enhance(1.9)
    face = face.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=2))
    out.parent.mkdir(parents=True, exist_ok=True)
    face.save(out)
    return out

def run_aic(face: Path, ship: Path):
    ship.mkdir(parents=True, exist_ok=True)
    aic = shutil.which("ascii-image-converter")
    if not aic:
        raise SystemExit("ascii-image-converter not found in PATH")
    subprocess.check_call([
        aic, str(face), "--color", "--complex", "-d", "100,55",
        "--save-img", str(ship), "--only-save", "--save-bg", "11,18,32,100",
    ])
    subprocess.check_call([
        aic, str(face), "--complex", "-d", "100,55",
        "--save-txt", str(ship), "--only-save",
    ])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", type=Path, default=None)
    args = ap.parse_args()
    photo = args.photo
    if not photo:
        cands = [
            ROOT / "assets" / "fernando-source.png",
            Path.home() / ".grok/sessions",
        ]
        # fall back
        photo = ROOT / "assets" / "ascii-lab" / "face.png"
    face = prep(photo if photo.exists() else ROOT/"assets/ascii-lab/face.png",
                ROOT/"assets/ascii-lab/face.png")
    ship = ROOT / "assets" / "ascii-lab" / "ship"
    run_aic(face, ship)
    print("Wrote pure ASCII under", ship)
    print("Compose card with existing compositor logic or re-run agent pipeline")

if __name__ == "__main__":
    main()
