#!/usr/bin/env python3
"""Generate true ASCII (character) neofetch profile cards for sudopimp.

Not a pixel mosaic — luminance is mapped to ASCII glyphs (like neofetch /
jeantimex/neofetch-profile). Outputs dark/light SVG + PNG.

Requires: pillow, cairosvg
  pip install pillow cairosvg

Usage:
  python scripts/generate_neofetch.py
  python scripts/generate_neofetch.py --cols 48 --rows 28
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "assets" / "source-robot.png"
if not DEFAULT_SRC.exists():
    DEFAULT_SRC = ROOT / "assets" / "github-avatar.png"

# Light → dense charset (neofetch-profile style family)
ASCII_CHARS = " `.-\':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "title": "#e8c468",
        "line": "#6b5a45",
        "key": [
            "#e8c468",
            "#f0883e",
            "#3fb950",
            "#58a6ff",
            "#d2a8ff",
            "#f0883e",
            "#3fb950",
            "#58a6ff",
            "#e8c468",
            "#d2a8ff",
        ],
        "value": "#e6edf3",
        "muted": "#8b7355",
        "link": "#58a6ff",
        "dim": "#484f58",
        "stroke": "#30363d",
        "shadow": "#010409",
    },
    "light": {
        "bg": "#ffffff",
        "title": "#9a6700",
        "line": "#bf8700",
        "key": [
            "#9a6700",
            "#bc4c00",
            "#1a7f37",
            "#0969da",
            "#8250df",
            "#bc4c00",
            "#1a7f37",
            "#0969da",
            "#9a6700",
            "#8250df",
        ],
        "value": "#1f2328",
        "muted": "#8c959f",
        "link": "#0969da",
        "dim": "#afb8c1",
        "stroke": "#d0d7de",
        "shadow": "#d0d7de",
    },
}


def esc(s) -> str:
    return html.escape(str(s))


def rgb_hex(c) -> str:
    return f"#{int(c[0]):02x}{int(c[1]):02x}{int(c[2]):02x}"


def prep_for_ascii(path: Path, size: int = 480) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r < 12 and g < 12 and b < 12:
                px[x, y] = (0, 0, 0, 0)
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    w, h = im.size
    m = int(min(w, h) * 0.05)
    im = im.crop((m, int(m * 0.6), w - m, h - m))
    s = max(im.size)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.paste(im, ((s - im.size[0]) // 2, (s - im.size[1]) // 2), im)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse([2, 2, s - 3, s - 3], fill=255)
    rgb = Image.new("RGB", (s, s), (13, 17, 23))
    rgb.paste(canvas.convert("RGB"), mask=canvas.split()[-1])
    rgb = ImageOps.autocontrast(rgb, cutoff=1)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.55)
    rgb = ImageEnhance.Color(rgb).enhance(1.15)
    rgb = ImageEnhance.Sharpness(rgb).enhance(2.0)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=2))
    out = rgb.convert("RGBA")
    out.putalpha(mask)
    return out.resize((size, size), Image.Resampling.LANCZOS)


def image_to_ascii(
    im: Image.Image,
    cols: int = 48,
    rows: int = 28,
    colored: bool = True,
    contrast: float = 1.4,
) -> list:
    """Map each sample pixel to one ASCII character (+ optional color)."""
    charset = ASCII_CHARS
    bg = Image.new("RGBA", im.size, (13, 17, 23, 255))
    composed = Image.alpha_composite(bg, im.convert("RGBA"))
    small = composed.convert("RGB").resize((cols, rows), Image.Resampling.LANCZOS)
    alpha = im.split()[-1].resize((cols, rows), Image.Resampling.BILINEAR)
    arr = small.load()
    ap = alpha.load()

    total, n = 0.0, 0
    for y in range(rows):
        for x in range(cols):
            if ap[x, y] < 128:
                continue
            r, g, b = arr[x, y]
            total += 0.299 * r + 0.587 * g + 0.114 * b
            n += 1
    avg = total / n if n else 128
    should_invert = avg < 100

    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            if ap[x, y] < 100:
                row.append((" ", None))
                continue
            r, g, b = arr[x, y]
            if r < 22 and g < 26 and b < 32:
                row.append((" ", None))
                continue
            luma = 0.299 * r + 0.587 * g + 0.114 * b
            adj = (luma - 128) * contrast + 128
            adj = max(0, min(255, adj))
            if should_invert:
                adj = 255 - adj
            dens = 255 - adj  # dark features → denser glyphs
            idx = int(dens / 255 * (len(charset) - 1))
            ch = charset[idx]
            row.append((ch, rgb_hex((r, g, b)) if colored else None))
        lines.append(row)
    return lines


def uptime_str() -> str:
    created = datetime(2026, 7, 7, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    d = now - created
    years, rem = divmod(d.days, 365)
    months, days = divmod(rem, 30)
    return f"{years} years, {months} months, {days} days"


def info_rows() -> list:
    return [
        ("section", "sudopimp@github"),
        ("field", "Name", "Fernando Lazzarin"),
        ("field", "Location", "Mendoza, Argentina"),
        ("field", "Created", "2026-07-07"),
        ("field", "Uptime", uptime_str()),
        ("field", "Company", ">_WAITDEAD"),
        ("blank",),
        ("field", "Languages", "Rust, Python"),
        ("field", "CLI", "Claude Code"),
        ("field", "Focus", "Humanoid robotics, AI agents"),
        ("blank",),
        ("field", "Hobbies.Music", "Singing, Lyrics, Producing"),
        ("field", "Hobbies.Games", "Videogames"),
        ("blank",),
        ("section", "Contact"),
        ("field", "Email", "fernando@waitdead.com"),
        ("field", "GitHub", "github.com/sudopimp"),
        ("field", "X", "@sudopimp"),
        ("field", "LinkedIn", "linkedin.com/in/fernando-lazzarin"),
    ]


def build_svg(theme_name: str, ascii_lines: list, info: list) -> tuple[str, int, int]:
    t = THEMES[theme_name]
    font_size = 13
    char_w = 7.4
    line_h = 14.8
    pad = 20
    gap = 28

    rows = len(ascii_lines)
    cols = len(ascii_lines[0]) if rows else 0
    art_w = cols * char_w
    art_h = rows * line_h

    def flen(k, v):
        return 2 + len(k) + 2 + 3 + 1 + len(v)

    max_info = 50
    for item in info:
        if item[0] == "field":
            max_info = max(max_info, flen(item[1], item[2]) + 2)
        if item[0] == "section":
            max_info = max(max_info, len(item[1]) + 22)
    mono_w = 7.9
    info_w = max_info * mono_w
    info_lh = 16.2

    n_lines = sum(1 for i in info if i[0] != "blank")
    n_blank = sum(1 for i in info if i[0] == "blank")
    info_h = n_lines * info_lh + n_blank * info_lh * 0.45 + 6

    content_h = max(art_h, info_h)
    width = int(pad * 2 + art_w + gap + info_w + 4)
    height = int(pad * 2 + content_h + 4)

    ax0 = pad
    ay0 = pad + line_h * 0.85 + max(0, (content_h - art_h) / 2)

    art_texts = []
    for yi, row in enumerate(ascii_lines):
        y = ay0 + yi * line_h
        parts = []
        i = 0
        while i < len(row):
            ch, col = row[i]
            j = i + 1
            while j < len(row) and row[j][1] == col:
                j += 1
            text = "".join(row[k][0] for k in range(i, j))
            fill = col if col else t["bg"]
            parts.append((text, fill if not all(c == " " for c in text) else t["bg"]))
            i = j
        tspans = []
        for idx, (text, fill) in enumerate(parts):
            if idx == 0:
                tspans.append(
                    f'<tspan x="{ax0:.1f}" y="{y:.1f}" fill="{fill}">{esc(text)}</tspan>'
                )
            else:
                tspans.append(f'<tspan fill="{fill}">{esc(text)}</tspan>')
        art_texts.append(
            f'<text font-size="{font_size}" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace">'
            + "".join(tspans)
            + "</text>"
        )

    ix0 = pad + art_w + gap
    iy = (
        pad + (content_h - info_h) / 2 + info_lh * 0.85
        if content_h > info_h
        else pad + info_lh
    )
    info_texts = []
    key_i = 0
    for item in info:
        if item[0] == "blank":
            iy += info_lh * 0.45
            continue
        if item[0] == "section":
            title = item[1]
            dash = "-" * max(14, max_info - len(title) - 2)
            info_texts.append(
                f'<text x="{ix0:.1f}" y="{iy:.1f}" font-size="{font_size}" '
                f'font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace">'
                f'<tspan fill="{t["title"]}" font-weight="700">{esc(title)}</tspan>'
                f'<tspan fill="{t["line"]}"> {esc(dash)}</tspan></text>'
            )
            iy += info_lh
            key_i = 0
            continue
        _, key, value = item
        kc = t["key"][key_i % len(t["key"])]
        key_i += 1
        prefix, colon = ". ", ": "
        fixed = len(prefix) + len(key) + len(colon) + len(value)
        dots = "." * max(3, max_info - fixed)
        vc = t["link"] if key in ("GitHub", "LinkedIn", "Email", "X") else t["value"]
        info_texts.append(
            f'<text x="{ix0:.1f}" y="{iy:.1f}" font-size="{font_size}" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace">'
            f'<tspan fill="{t["dim"]}">{esc(prefix)}</tspan>'
            f'<tspan fill="{kc}">{esc(key)}</tspan>'
            f'<tspan fill="{t["dim"]}">{esc(colon)}</tspan>'
            f'<tspan fill="{t["muted"]}">{esc(dots)}</tspan>'
            f'<tspan fill="{vc}"> {esc(value)}</tspan></text>'
        )
        iy += info_lh

    pal = ["#f85149", "#f0883e", "#e8c468", "#3fb950", "#58a6ff", "#d2a8ff", "#e6edf3", "#8b949e"]
    if theme_name == "light":
        pal = ["#cf222e", "#bc4c00", "#9a6700", "#1a7f37", "#0969da", "#8250df", "#1f2328", "#656d76"]
    sw = 11
    pal_y = ay0 + art_h - line_h * 0.2 + 8
    height = int(max(height, pal_y + 28 + pad))
    pal_x0 = ax0 + max(0, (art_w - len(pal) * sw * 1.35) / 2)
    pal_rects = [
        f'<rect x="{pal_x0 + i * sw * 1.35:.1f}" y="{pal_y:.1f}" width="{sw}" height="{sw}" rx="2" fill="{c}"/>'
        for i, c in enumerate(pal)
    ]

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="sudopimp@github neofetch ASCII">
  <title>sudopimp@github — Fernando Lazzarin (ASCII neofetch)</title>
  <defs>
    <filter id="soft" x="-3%" y="-3%" width="106%" height="106%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="{t["shadow"]}" flood-opacity="0.35"/>
    </filter>
    <clipPath id="r"><rect width="{width}" height="{height}" rx="12" ry="12"/></clipPath>
  </defs>
  <g clip-path="url(#r)" filter="url(#soft)">
    <rect width="{width}" height="{height}" fill="{t["bg"]}"/>
    <rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="12" ry="12" fill="none" stroke="{t["stroke"]}" stroke-width="1"/>
    <g id="ascii">{"".join(art_texts)}</g>
    <g id="palette">{"".join(pal_rects)}</g>
    <g id="info">{"".join(info_texts)}</g>
  </g>
</svg>
'''
    return svg, width, height


def write_neofetch_json(out: Path) -> None:
    cfg = {
        "image": "https://raw.githubusercontent.com/sudopimp/sudopimp/main/assets/robot-ascii.png",
        "coloredImage": True,
        "removeBackground": False,
        "imageScale": 1.25,
        "imageOffsetY": "-4%",
        "backgroundColor": "#ffffff, #0d1117",
        "separatorColor": "#c9a66b, #8b7355",
        "sections": [
            {
                "title": "sudopimp@github",
                "titleColor": {"text": "#b8860b, #e8c468", "line": "#8b7355, #6b5a45"},
                "fields": [
                    {
                        "key": "Name",
                        "value": "Fernando Lazzarin",
                        "keyColor": "#c9892a, #e8c468",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "Location",
                        "value": "Mendoza, Argentina",
                        "keyColor": "#c45c26, #f0883e",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "Created",
                        "value": "2026-07-07",
                        "keyColor": "#2da44e, #3fb950",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "Uptime",
                        "value": "{{uptime}}",
                        "keyColor": "#0969da, #58a6ff",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "Company",
                        "value": ">_WAITDEAD",
                        "keyColor": "#8250df, #d2a8ff",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                ],
            },
            {
                "fields": [
                    {
                        "key": "Languages",
                        "value": "Rust, Python",
                        "keyColor": "#c9892a, #e8c468",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "CLI",
                        "value": "Claude Code",
                        "keyColor": "#c45c26, #f0883e",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "Focus",
                        "value": "Humanoid robotics, AI agents",
                        "keyColor": "#2da44e, #3fb950",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                ],
            },
            {
                "fields": [
                    {
                        "key": "Hobbies.Music",
                        "value": "Singing, Lyrics, Producing",
                        "keyColor": "#0969da, #58a6ff",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "Hobbies.Games",
                        "value": "Videogames",
                        "keyColor": "#8250df, #d2a8ff",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                ],
            },
            {
                "title": "- Contact",
                "titleColor": {"text": "#b8860b, #e8c468", "line": "#8b7355, #6b5a45"},
                "fields": [
                    {
                        "key": "Email",
                        "value": "fernando@waitdead.com",
                        "keyColor": "#c9892a, #e8c468",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "GitHub",
                        "value": "https://github.com/sudopimp",
                        "keyColor": "#c45c26, #f0883e",
                        "valueColor": "#0969da, #58a6ff",
                    },
                    {
                        "key": "X",
                        "value": "sudopimp",
                        "keyColor": "#2da44e, #3fb950",
                        "valueColor": "#1f2328, #e6edf3",
                    },
                    {
                        "key": "LinkedIn",
                        "value": "fernando-lazzarin",
                        "keyColor": "#0969da, #58a6ff",
                        "valueColor": "#0969da, #58a6ff",
                    },
                ],
            },
        ],
        "stats": {"enabled": False},
    }
    (out / "neofetch.json").write_text(json.dumps(cfg, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate true ASCII neofetch cards")
    parser.add_argument("--source", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--cols", type=int, default=48)
    parser.add_argument("--rows", type=int, default=28)
    parser.add_argument("--out", type=Path, default=ROOT)
    args = parser.parse_args()

    try:
        import cairosvg
    except ImportError as e:
        raise SystemExit("cairosvg required: pip install cairosvg") from e

    im = prep_for_ascii(args.source, 480)
    (args.out / "assets").mkdir(exist_ok=True)
    im.save(args.out / "assets" / "robot-ascii.png", "PNG", optimize=True)

    lines = image_to_ascii(im, cols=args.cols, rows=args.rows, colored=True)
    plain = "\n".join("".join(c for c, _ in row) for row in lines)
    (args.out / "ascii-art.txt").write_text(plain + "\n")

    info = info_rows()
    for theme in ("dark", "light"):
        svg, w, h = build_svg(theme, lines, info)
        svg_path = args.out / f"neofetch-{theme}.svg"
        png_path = args.out / f"neofetch-{theme}.png"
        svg_path.write_text(svg, encoding="utf-8")
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1200)
        print(f"{theme}: {w}x{h} ASCII {args.cols}x{args.rows} -> {png_path.name}")

    write_neofetch_json(args.out)
    print("wrote neofetch.json + ascii-art.txt")


if __name__ == "__main__":
    main()
