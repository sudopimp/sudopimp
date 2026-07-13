#!/usr/bin/env python3
"""Generate sudopimp profile card — production contract (SOTA presentation).

Contract (do not drift):
  - Pure-glyph ASCII portrait (ascii-image-converter --color --complex)
  - Face/torso on void (rembg cutout by default)
  - Greyscale UI text only (no rainbow keys, no cyan rainbow, no palette strip)
  - Outputs: card-dark.png, card-light.png, ascii-art.txt

Requires:
  - ascii-image-converter v1.13.1+ in PATH
  - pillow, rembg, onnxruntime (see requirements.txt)

Usage:
  python scripts/generate.py
  python scripts/generate.py --photo /path/to/private.jpg
  python scripts/generate.py --no-rembg   # face.png already cut out
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
AIC_MIN_VERSION = "1.13.1"

# --- UI palette: greys / whites only (sober presentation) ---
UI_DARK = {
    "card_bg": (13, 17, 23),
    "stroke": (48, 54, 61),
    "key": (139, 148, 158),
    "value": (230, 237, 243),
    "title": (201, 209, 217),
    "dim": (110, 118, 129),
    "line": (72, 79, 88),
    "link": (201, 209, 217),
}
UI_LIGHT = {
    "card_bg": (255, 255, 255),
    "stroke": (208, 215, 222),
    "key": (87, 96, 106),
    "value": (31, 35, 40),
    "title": (36, 41, 47),
    "dim": (110, 118, 129),
    "line": (175, 184, 193),
    "link": (31, 35, 40),
}

VOID = (13, 17, 23)


def check_aic() -> str:
    aic = shutil.which("ascii-image-converter")
    if not aic:
        sys.exit(
            "ascii-image-converter not found. Install v"
            f"{AIC_MIN_VERSION}+ — see GENERATOR.md"
        )
    out = subprocess.check_output([aic, "--version"], text=True).strip()
    return out


def prep_face(
    src: Path,
    dst: Path,
    *,
    size: int = 720,
    use_rembg: bool = True,
) -> Path:
    """Crop / cut out face+torso onto void. Writes RGB PNG at dst."""
    raw = Image.open(src).convert("RGBA")

    if use_rembg:
        try:
            from rembg import remove
        except ImportError:
            sys.exit("rembg not installed. pip install -r requirements.txt")
        cut = remove(raw)
    else:
        cut = raw

    bbox = cut.getbbox()
    if bbox:
        cut = cut.crop(bbox)

    s = max(cut.size)
    sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sq.paste(cut, ((s - cut.size[0]) // 2, (s - cut.size[1]) // 2), cut)
    m = max(1, int(s * 0.03))
    sq = sq.crop((m, m, s - m, s - m)).resize((size, size), Image.Resampling.LANCZOS)

    rgb = Image.new("RGB", sq.size, VOID)
    rgb.paste(sq.convert("RGB"), mask=sq.split()[-1])
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    rgb = ImageEnhance.Color(rgb).enhance(1.1)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.25)

    alpha = sq.split()[-1]
    circle = Image.new("L", rgb.size, 0)
    ImageDraw.Draw(circle).ellipse([6, 6, size - 7, size - 7], fill=255)
    circle = circle.filter(ImageFilter.GaussianBlur(1.0))
    alpha = Image.composite(alpha, Image.new("L", rgb.size, 0), circle)

    out = Image.new("RGB", rgb.size, VOID)
    out.paste(rgb, mask=alpha)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, "PNG", optimize=True)
    return dst


def run_aic(face: Path, out_dir: Path, dims: str = "68,36") -> tuple[Path, Path]:
    """Pure-glyph colored ASCII via ascii-image-converter."""
    aic = shutil.which("ascii-image-converter")
    assert aic
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("*"):
        if p.is_file():
            p.unlink()
    subprocess.check_call(
        [
            aic,
            str(face),
            "--color",
            "--complex",
            "-d",
            dims,
            "--save-img",
            str(out_dir),
            "--only-save",
            "--save-bg",
            "13,17,23,100",
        ]
    )
    subprocess.check_call(
        [
            aic,
            str(face),
            "--complex",
            "-d",
            dims,
            "--save-txt",
            str(out_dir),
            "--only-save",
        ]
    )
    png = next(out_dir.glob("*ascii*.png"))
    txt = next(out_dir.glob("*ascii*.txt"))
    return png, txt


def assert_pure_ascii(text: str) -> None:
    """Raise if text contains block graphics or braille (not pure ASCII art)."""
    for ch in text:
        o = ord(ch)
        if 0x2580 <= o <= 0x259F:
            raise ValueError(f"block character U+{o:04X} in ascii-art")
        if 0x2800 <= o <= 0x28FF:
            raise ValueError(f"braille U+{o:04X} in ascii-art")
        if o > 126 and ch not in "\n\r\t":
            # allow nothing beyond printable ASCII in dump
            raise ValueError(f"non-ASCII U+{o:04X} in ascii-art")


def uptime() -> str:
    created = datetime(2026, 7, 7, tzinfo=timezone.utc)
    d = datetime.now(timezone.utc) - created
    y, r = divmod(d.days, 365)
    m, days = divmod(r, 30)
    return f"{y} years, {m} months, {days} days"


def font(sz: int = 14) -> ImageFont.ImageFont:
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def info_rows() -> list:
    return [
        ("title", "sudopimp@github", None),
        ("field", "Name", "Fernando Lazzarin"),
        ("field", "Location", "Mendoza, Argentina"),
        ("field", "Created", "2026-07-07"),
        ("field", "Uptime", uptime()),
        ("field", "Company", ">_WAITDEAD"),
        ("blank",),
        ("field", "Languages", "Rust, Python"),
        ("field", "CLI", "Claude Code"),
        ("field", "Focus", "Humanoid robotics, AI agents"),
        ("blank",),
        ("field", "Hobbies.Music", "Singing, Lyrics, Producing"),
        ("field", "Hobbies.Games", "Videogames"),
        ("blank",),
        ("title", "Contact", None),
        ("field", "Email", "fernando@waitdead.com"),
        ("field", "GitHub", "github.com/sudopimp"),
        ("field", "X", "@sudopimp"),
        ("field", "LinkedIn", "in/fernando-lazzarin-a10013345"),
    ]


def build_card(ascii_png: Path, dark: bool = True) -> Image.Image:
    """Compose pure-ASCII portrait + greyscale neofetch-style fields (no palette)."""
    art = Image.open(ascii_png).convert("RGBA")
    px = art.load()
    w, h = art.size
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if abs(r - VOID[0]) + abs(g - VOID[1]) + abs(b - VOID[2]) > 20:
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    if maxx > minx:
        art = art.crop(
            (max(0, minx - 1), max(0, miny - 1), min(w, maxx + 2), min(h, maxy + 2))
        )

    CHAR_W, LINE_H, PAD, GAP, INFO_COLS = 8.4, 17.5, 28, 40, 52
    INFO_W = INFO_COLS * CHAR_W
    ART_H = 400
    ART_W = max(1, int(art.size[0] * (ART_H / max(1, art.size[1]))))
    art = art.resize((ART_W, ART_H), Image.Resampling.LANCZOS)

    rows = info_rows()
    n_lines = sum(1 for r in rows if r[0] != "blank")
    n_blank = sum(1 for r in rows if r[0] == "blank")
    info_h = n_lines * LINE_H + n_blank * LINE_H * 0.4
    card_w = int(PAD * 2 + ART_W + GAP + INFO_W)
    card_h = int(PAD * 2 + max(ART_H, info_h) + 6)

    ui = UI_DARK if dark else UI_LIGHT
    card = Image.new("RGB", (card_w, card_h), ui["card_bg"])
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle(
        [0.5, 0.5, card_w - 1.5, card_h - 1.5],
        radius=12,
        outline=ui["stroke"],
        width=1,
    )

    ax = PAD
    ay = PAD + max(0, int((info_h - ART_H) / 2))
    if not dark:
        card.paste(
            Image.new("RGB", (ART_W + 12, ART_H + 12), VOID),
            (ax - 6, ay - 6),
        )
    base = Image.new("RGBA", art.size, (*VOID, 255))
    base = Image.alpha_composite(base, art)
    card.paste(base.convert("RGB"), (ax, ay))

    # NO palette strip — sober presentation

    f = font(14)

    def tw(s: str) -> int:
        b = draw.textbbox((0, 0), s, font=f)
        return b[2] - b[0]

    ix = PAD + ART_W + GAP
    iy = PAD + max(0, (ART_H - info_h) / 2) + 2 if ART_H > info_h else PAD + 2

    for row in rows:
        if row[0] == "blank":
            iy += LINE_H * 0.35
            continue
        if row[0] == "title":
            title = row[1]
            draw.text((ix, iy), title, fill=ui["title"], font=f)
            dash = " " + "-" * max(6, INFO_COLS - len(title) - 1)
            draw.text((ix + tw(title), iy), dash, fill=ui["line"], font=f)
            iy += LINE_H
            continue
        key, value = row[1], row[2]
        left = f". {key}: "
        dots = "." * max(3, INFO_COLS - (len(left) + 1 + len(value)))
        x = ix
        draw.text((x, iy), ". ", fill=ui["dim"], font=f)
        x += tw(". ")
        draw.text((x, iy), key, fill=ui["key"], font=f)
        x += tw(key)
        draw.text((x, iy), ": ", fill=ui["dim"], font=f)
        x += tw(": ")
        draw.text((x, iy), dots, fill=ui["line"], font=f)
        x += tw(dots)
        vc = ui["link"] if key in ("Email", "GitHub", "X", "LinkedIn") else ui["value"]
        draw.text((x, iy), " " + value, fill=vc, font=f)
        iy += LINE_H

    return card


def ui_colors_are_sober(ui: dict) -> bool:
    """Return True if all UI colors are near-greyscale (low chroma)."""
    for k, rgb in ui.items():
        if k in ("card_bg", "stroke"):
            continue
        r, g, b = rgb
        if max(r, g, b) - min(r, g, b) > 24:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate sudopimp presentation card")
    ap.add_argument(
        "--photo",
        type=Path,
        default=None,
        help="Input photo (default: assets/source/face.png or private path)",
    )
    ap.add_argument(
        "--no-rembg",
        action="store_true",
        help="Skip rembg (use when face.png is already cut out)",
    )
    ap.add_argument("--dims", default="68,36", help="ASCII grid width,height chars")
    args = ap.parse_args(argv)

    ver = check_aic()
    print(f"ascii-image-converter {ver}")

    assert ui_colors_are_sober(UI_DARK), "UI_DARK not sober"
    assert ui_colors_are_sober(UI_LIGHT), "UI_LIGHT not sober"

    default_face = ROOT / "assets" / "source" / "face.png"
    photo = args.photo if args.photo else default_face
    if not photo.exists():
        sys.exit(f"photo not found: {photo}")

    face_out = ROOT / "assets" / "source" / "face.png"
    # If user passes a private photo, write cutout to face.png for aic
    # If default face already cut and --no-rembg, skip
    if args.no_rembg and photo.resolve() == face_out.resolve():
        print("using existing cutout face.png (--no-rembg)")
        face_path = face_out
    else:
        print(f"cutout from {photo} → face.png (rembg={not args.no_rembg})")
        face_path = prep_face(photo, face_out, use_rembg=not args.no_rembg)

    ship = ROOT / ".build" / "ascii"
    png, txt = run_aic(face_path, ship, dims=args.dims)

    text = txt.read_text(encoding="utf-8", errors="replace")
    assert_pure_ascii(text)
    shutil.copy(txt, ROOT / "ascii-art.txt")

    build_card(png, dark=True).save(ROOT / "card-dark.png", "PNG", optimize=True)
    build_card(png, dark=False).save(ROOT / "card-light.png", "PNG", optimize=True)
    print("Wrote card-dark.png card-light.png ascii-art.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
