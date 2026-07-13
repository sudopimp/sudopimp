#!/usr/bin/env python3
"""Generate sudopimp profile card (pure ASCII + neofetch layout).

Requires:
  - ascii-image-converter  (https://github.com/TheZoraiz/ascii-image-converter)
  - pillow                 (pip install pillow)

Usage:
  python scripts/generate.py
  python scripts/generate.py --photo assets/source/face.png

Outputs:
  card-dark.png  card-light.png  ascii-art.txt
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def prep_face(src: Path, dst: Path, size: int = 720) -> None:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    side = int(min(w, h) * 0.74)
    cx, cy = w // 2, int(h * 0.40)
    x0 = max(0, min(w - side, cx - side // 2))
    y0 = max(0, min(h - side, cy - side // 2))
    face = im.crop((x0, y0, x0 + side, y0 + side)).resize((size, size), Image.Resampling.LANCZOS)
    face = ImageOps.autocontrast(face, cutoff=0.8)
    face = ImageEnhance.Contrast(face).enhance(1.35)
    face = ImageEnhance.Color(face).enhance(1.2)
    face = ImageEnhance.Sharpness(face).enhance(1.7)
    dst.parent.mkdir(parents=True, exist_ok=True)
    face.save(dst)


def run_aic(face: Path, out_dir: Path) -> tuple[Path, Path]:
    aic = shutil.which("ascii-image-converter")
    if not aic:
        sys.exit("ascii-image-converter not found. Install from https://github.com/TheZoraiz/ascii-image-converter")
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("*"):
        p.unlink()
    subprocess.check_call(
        [
            aic,
            str(face),
            "--color",
            "--complex",
            "-d",
            "72,40",
            "--save-img",
            str(out_dir),
            "--only-save",
            "--save-bg",
            "13,17,23,100",
        ]
    )
    subprocess.check_call(
        [aic, str(face), "--complex", "-d", "72,40", "--save-txt", str(out_dir), "--only-save"]
    )
    png = next(out_dir.glob("*ascii*.png"))
    txt = next(out_dir.glob("*ascii*.txt"))
    return png, txt


def font(sz: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def uptime() -> str:
    created = datetime(2026, 7, 7, tzinfo=timezone.utc)
    d = datetime.now(timezone.utc) - created
    y, r = divmod(d.days, 365)
    m, days = divmod(r, 30)
    return f"{y} years, {m} months, {days} days"


def build_card(ascii_png: Path, dark: bool = True) -> Image.Image:
    art = Image.open(ascii_png).convert("RGBA")
    bg = (13, 17, 23)
    px = art.load()
    w, h = art.size
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 25:
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    art = art.crop((max(0, minx - 2), max(0, miny - 2), min(w, maxx + 3), min(h, maxy + 3)))

    CHAR_W, LINE_H, PAD, GAP, INFO_COLS = 8.4, 18.0, 24, 36, 54
    INFO_W = INFO_COLS * CHAR_W
    ART_H = 420
    ART_W = int(art.size[0] * (ART_H / art.size[1]))
    art = art.resize((ART_W, ART_H), Image.Resampling.LANCZOS)
    PAL_H = 22

    rows = [
        ("title", "sudopimp@github", None, "#e3b341"),
        ("field", "Name", "Fernando Lazzarin", "#e3b341"),
        ("field", "Location", "Mendoza, Argentina", "#f0883e"),
        ("field", "Created", "2026-07-07", "#3fb950"),
        ("field", "Uptime", uptime(), "#58a6ff"),
        ("field", "Company", ">_WAITDEAD", "#d2a8ff"),
        ("blank",),
        ("field", "Languages", "Rust, Python", "#e3b341"),
        ("field", "CLI", "Claude Code", "#f0883e"),
        ("field", "Focus", "Humanoid robotics, AI agents", "#3fb950"),
        ("blank",),
        ("field", "Hobbies.Music", "Singing, Lyrics, Producing", "#58a6ff"),
        ("field", "Hobbies.Games", "Videogames", "#d2a8ff"),
        ("blank",),
        ("title", "Contact", None, "#e3b341"),
        ("field", "Email", "fernando@waitdead.com", "#e3b341"),
        ("field", "GitHub", "github.com/sudopimp", "#f0883e"),
        ("field", "X", "@sudopimp", "#3fb950"),
        ("field", "LinkedIn", "linkedin.com/in/fernando-lazzarin", "#58a6ff"),
    ]
    n_lines = sum(1 for r in rows if r[0] != "blank")
    n_blank = sum(1 for r in rows if r[0] == "blank")
    info_h = n_lines * LINE_H + n_blank * LINE_H * 0.45
    card_w = int(PAD * 2 + ART_W + GAP + INFO_W)
    card_h = int(PAD * 2 + max(ART_H + PAL_H + 12, info_h) + 8)

    if dark:
        card_bg, stroke, dim, tline = (13, 17, 23), (48, 54, 61), (139, 148, 158), (110, 118, 129)
        val_default, val_link = (165, 214, 255), (88, 166, 255)
    else:
        card_bg, stroke, dim, tline = (255, 255, 255), (208, 215, 222), (87, 96, 106), (175, 184, 193)
        val_default, val_link = (9, 105, 218), (9, 105, 218)

    card = Image.new("RGB", (card_w, card_h), card_bg)
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle([0.5, 0.5, card_w - 1.5, card_h - 1.5], radius=12, outline=stroke, width=1)

    ax = PAD
    ay = PAD
    if not dark:
        card.paste(Image.new("RGB", (ART_W + 16, ART_H + PAL_H + 24), (13, 17, 23)), (ax - 8, ay - 8))
    base = Image.new("RGBA", art.size, (13, 17, 23, 255))
    base = Image.alpha_composite(base, art)
    card.paste(base.convert("RGB"), (ax, ay))

    pal = [
        (248, 81, 73),
        (240, 136, 62),
        (227, 179, 65),
        (63, 185, 80),
        (88, 166, 255),
        (210, 168, 255),
        (240, 246, 252),
        (110, 118, 129),
    ]
    sw = 14
    py = ay + ART_H + 10
    px0 = ax + max(0, (ART_W - len(pal) * int(sw * 1.45)) // 2)
    for i, c in enumerate(pal):
        x = px0 + i * int(sw * 1.45)
        draw.rounded_rectangle([x, py, x + sw, py + sw], radius=3, fill=c)

    f = font(14)

    def tw(s: str) -> int:
        b = draw.textbbox((0, 0), s, font=f)
        return b[2] - b[0]

    def hx(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        rgb = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
        if not dark:
            return tuple(max(0, int(c * 0.78)) for c in rgb)
        return rgb

    ix = PAD + ART_W + GAP
    block_h = ART_H + PAL_H + 12
    iy = PAD + max(0, (block_h - info_h) / 2) + LINE_H * 0.15

    for row in rows:
        if row[0] == "blank":
            iy += LINE_H * 0.4
            continue
        if row[0] == "title":
            title = row[1]
            draw.text((ix, iy), title, fill=hx(row[3]), font=f)
            draw.text((ix + tw(title), iy), " " + "-" * max(8, INFO_COLS - len(title) - 1), fill=tline, font=f)
            iy += LINE_H
            continue
        key, value, kcol = row[1], row[2], row[3]
        left = f". {key}: "
        dots = "." * max(3, INFO_COLS - (len(left) + 1 + len(value)))
        x = ix
        draw.text((x, iy), ". ", fill=dim, font=f)
        x += tw(". ")
        draw.text((x, iy), key, fill=hx(kcol), font=f)
        x += tw(key)
        draw.text((x, iy), ": ", fill=dim, font=f)
        x += tw(": ")
        draw.text((x, iy), dots, fill=tline, font=f)
        x += tw(dots)
        vc = val_link if key in ("Email", "GitHub", "X", "LinkedIn") else val_default
        draw.text((x, iy), " " + value, fill=vc, font=f)
        iy += LINE_H
    return card


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate sudopimp neofetch ASCII card")
    ap.add_argument("--photo", type=Path, default=ROOT / "assets" / "source" / "face.png")
    args = ap.parse_args()
    face = ROOT / "assets" / "source" / "face.png"
    prep_face(args.photo if args.photo.exists() else face, face)
    ship = ROOT / ".build" / "ascii"
    png, txt = run_aic(face, ship)
    shutil.copy(txt, ROOT / "ascii-art.txt")
    build_card(png, dark=True).save(ROOT / "card-dark.png", "PNG", optimize=True)
    build_card(png, dark=False).save(ROOT / "card-light.png", "PNG", optimize=True)
    print("Wrote card-dark.png card-light.png ascii-art.txt")


if __name__ == "__main__":
    main()
