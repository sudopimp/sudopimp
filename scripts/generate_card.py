#!/usr/bin/env python3
"""
sudopimp GitHub profile card generator

LEFT  : true-color terminal art of the portrait (ASCII glyphs or half-blocks)
RIGHT : cyan / white / grey UI only (neofetch-style fields)

Modes
-----
  ascii   – one glyph per cell, colored by source pixel (classic neofetch)
  blocks  – ▀ half-blocks with FG/BG colors (2× vertical detail, still terminal)

Default is *blocks* for face readability; use --mode ascii for pure glyphs.

Usage
-----
  python scripts/generate_card.py
  python scripts/generate_card.py --mode ascii --cols 72
  python scripts/generate_card.py --source assets/me.png --stamp v9
"""

from __future__ import annotations

import argparse
import html
import math
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]

# Density ramp (light → dark). Used for classic ASCII.
ASCII_CHARS = (
    " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
)

# UI palette — cyan / white / grey ONLY
UI = {
    "dark": {
        "bg": "#0b1220",
        "stroke": "#1e293b",
        "cyan": "#22d3ee",
        "cyan_soft": "#67e8f9",
        "white": "#e2e8f0",
        "grey": "#64748b",
        "line": "#334155",
        "shadow": "#020617",
    },
    "light": {
        "bg": "#f8fafc",
        "stroke": "#e2e8f0",
        "cyan": "#0e7490",
        "cyan_soft": "#0891b2",
        "white": "#0f172a",
        "grey": "#64748b",
        "line": "#cbd5e1",
        "shadow": "#94a3b8",
    },
}


def esc(s: str) -> str:
    return html.escape(str(s))


def rgb_hex(c) -> str:
    r, g, b = (max(0, min(255, int(v))) for v in c[:3])
    return f"#{r:02x}{g:02x}{b:02x}"


def prep_portrait(path: Path, size: int = 800) -> Image.Image:
    """Tight face crop, contrast for structure, keep natural color."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = int(min(w, h) * 0.82)
    cx, cy = w // 2, int(h * 0.38)
    x0 = max(0, min(w - side, cx - side // 2))
    y0 = max(0, min(h - side, cy - side // 2))
    face = im.crop((x0, y0, x0 + side, y0 + side))
    face = face.resize((size, size), Image.Resampling.LANCZOS)

    # Edge-preserving denoise-ish blur then unsharp → cleaner glyph regions
    face = face.filter(ImageFilter.MedianFilter(size=3))
    face = ImageOps.autocontrast(face, cutoff=0.5)
    face = ImageEnhance.Contrast(face).enhance(1.2)
    face = ImageEnhance.Color(face).enhance(1.15)
    face = ImageEnhance.Sharpness(face).enhance(1.55)
    face = face.filter(ImageFilter.UnsharpMask(radius=1.1, percent=130, threshold=2))

    # Circular on card-dark navy
    bg = (11, 18, 32)
    out = Image.new("RGB", (size, size), bg)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([2, 2, size - 3, size - 3], fill=255)
    out.paste(face, (0, 0), mask)
    return out


def sample_grid(im: Image.Image, cols: int, rows: int) -> list[list[tuple[int, int, int]]]:
    small = im.resize((cols, rows), Image.Resampling.LANCZOS)
    px = small.load()
    return [[px[x, y] for x in range(cols)] for y in range(rows)]


def luma(c) -> float:
    r, g, b = c[:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def is_bg(c, bg=(11, 18, 32), tol=42) -> bool:
    return abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2]) < tol


def ascii_cells(
    im: Image.Image, cols: int, rows: int, gamma: float = 0.9
) -> list[list[tuple[str, str | None]]]:
    """
    Classic ASCII: one character per cell.
    Correct terminal aspect: rows ≈ cols * char_aspect (≈0.50–0.55).
    """
    grid = sample_grid(im, cols, rows)
    out = []
    n = len(ASCII_CHARS) - 1
    for y in range(rows):
        row = []
        for x in range(cols):
            c = grid[y][x]
            if is_bg(c):
                row.append((" ", None))
                continue
            t = max(0.0, min(1.0, luma(c) / 255.0))
            t = t**gamma
            # dark → denser glyph
            idx = int((1.0 - t) * n)
            ch = ASCII_CHARS[idx]
            # slight sat boost for dark cards
            r, g, b = c[:3]
            avg = (r + g + b) / 3
            sat = 1.12
            r = avg + (r - avg) * sat
            g = avg + (g - avg) * sat
            b = avg + (b - avg) * sat
            row.append((ch, rgb_hex((r + 4, g + 3, b + 2))))
        out.append(row)
    return out


def block_cells(
    im: Image.Image, cols: int, rows: int
) -> list[list[tuple[str, str | None, str | None]]]:
    """
    Half-block cells: character ▀ with top color (fg) and bottom color (bg).
    Sample height = rows*2 so each terminal row covers two image rows.
    Returns (char, fg_hex|None, bg_hex|None).
    """
    sample_h = rows * 2
    grid = sample_grid(im, cols, sample_h)
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            top = grid[y * 2][x]
            bot = grid[y * 2 + 1][x]
            t_bg, b_bg = is_bg(top), is_bg(bot)
            if t_bg and b_bg:
                row.append((" ", None, None))
            elif t_bg and not b_bg:
                row.append(("▄", rgb_hex(bot), None))  # lower half only
            elif not t_bg and b_bg:
                row.append(("▀", rgb_hex(top), None))  # upper half only
            else:
                row.append(("▀", rgb_hex(top), rgb_hex(bot)))
        out.append(row)
    return out


def uptime_str() -> str:
    created = datetime(2026, 7, 7, tzinfo=timezone.utc)
    d = datetime.now(timezone.utc) - created
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
        ("field", "Email", "fernando@waitdead.com", True),
        ("field", "GitHub", "github.com/sudopimp", True),
        ("field", "X", "@sudopimp", True),
        ("field", "LinkedIn", "linkedin.com/in/fernando-lazzarin", True),
    ]


def build_svg(
    theme: str,
    art,  # ascii: (ch, color) or blocks: (ch, fg, bg)
    mode: str,
    cols: int,
    rows: int,
) -> tuple[str, int, int]:
    t = UI[theme]
    font_size = 13
    # Mono metrics: width/height ratio ~0.55–0.6 for Consolas-like
    char_w = 7.4
    line_h = 14.8
    pad, gap = 22, 30

    art_w = cols * char_w
    art_h = rows * line_h

    max_info = 52
    info_w = max_info * 7.9
    info_lh = 16.3
    info = info_rows()
    n_lines = sum(1 for i in info if i[0] != "blank")
    n_blank = sum(1 for i in info if i[0] == "blank")
    info_h = n_lines * info_lh + n_blank * info_lh * 0.45 + 8

    content_h = max(art_h, info_h)
    width = int(pad * 2 + art_w + gap + info_w)
    height = int(pad * 2 + content_h + 14)

    ax0 = pad
    ay0 = pad + line_h * 0.85 + max(0, (content_h - art_h) / 2)

    # --- portrait ---
    art_nodes = []
    if mode == "blocks":
        # For half-blocks: rects for dual colors + optional ▀ (rects render sharper in SVG)
        # Using rects sized to char cells is equivalent to half-block terminal rendering.
        cell_h = line_h
        half = cell_h / 2
        for yi, row in enumerate(art):
            for xi, cell in enumerate(row):
                ch, fg, bg = cell
                if ch == " " and fg is None:
                    continue
                x = ax0 + xi * char_w
                y = ay0 - line_h * 0.75 + yi * line_h  # align with text baseline-ish
                # full cell area
                if bg and fg:
                    art_nodes.append(
                        f'<rect x="{x:.2f}" y="{y:.2f}" width="{char_w+0.05:.2f}" height="{half+0.05:.2f}" fill="{fg}"/>'
                    )
                    art_nodes.append(
                        f'<rect x="{x:.2f}" y="{y+half:.2f}" width="{char_w+0.05:.2f}" height="{half+0.05:.2f}" fill="{bg}"/>'
                    )
                elif fg and ch == "▀":
                    art_nodes.append(
                        f'<rect x="{x:.2f}" y="{y:.2f}" width="{char_w+0.05:.2f}" height="{half+0.05:.2f}" fill="{fg}"/>'
                    )
                elif fg and ch == "▄":
                    art_nodes.append(
                        f'<rect x="{x:.2f}" y="{y+half:.2f}" width="{char_w+0.05:.2f}" height="{half+0.05:.2f}" fill="{fg}"/>'
                    )
                elif fg:
                    art_nodes.append(
                        f'<rect x="{x:.2f}" y="{y:.2f}" width="{char_w+0.05:.2f}" height="{cell_h+0.05:.2f}" fill="{fg}"/>'
                    )
    else:
        # Classic ASCII text runs grouped by color
        for yi, row in enumerate(art):
            y = ay0 + yi * line_h
            parts = []
            i = 0
            while i < len(row):
                ch, col = row[i]
                j = i + 1
                while j < len(row) and row[j][1] == col:
                    j += 1
                text = "".join(row[k][0] for k in range(i, j))
                parts.append((text, col if col else t["bg"]))
                i = j
            tspans = []
            for idx, (text, fill) in enumerate(parts):
                if idx == 0:
                    tspans.append(
                        f'<tspan x="{ax0:.1f}" y="{y:.1f}" fill="{fill}">{esc(text)}</tspan>'
                    )
                else:
                    tspans.append(f'<tspan fill="{fill}">{esc(text)}</tspan>')
            art_nodes.append(
                f'<text font-size="{font_size}" '
                f'font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace">'
                + "".join(tspans)
                + "</text>"
            )

    # --- info panel ---
    ix0 = pad + art_w + gap
    iy = (
        pad + (content_h - info_h) / 2 + info_lh * 0.85
        if content_h > info_h
        else pad + info_lh
    )
    info_nodes = []
    for item in info:
        if item[0] == "blank":
            iy += info_lh * 0.45
            continue
        if item[0] == "section":
            title = item[1]
            dash = "-" * max(14, max_info - len(title) - 2)
            info_nodes.append(
                f'<text x="{ix0:.1f}" y="{iy:.1f}" font-size="{font_size}" '
                f'font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace">'
                f'<tspan fill="{t["cyan"]}" font-weight="700">{esc(title)}</tspan>'
                f'<tspan fill="{t["line"]}"> {esc(dash)}</tspan></text>'
            )
            iy += info_lh
            continue
        key, value = item[1], item[2]
        is_link = len(item) > 3 and item[3]
        prefix, colon = ". ", ": "
        fixed = len(prefix) + len(key) + len(colon) + len(value)
        dots = "." * max(3, max_info - fixed)
        vc = t["cyan_soft"] if is_link else t["white"]
        info_nodes.append(
            f'<text x="{ix0:.1f}" y="{iy:.1f}" font-size="{font_size}" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace">'
            f'<tspan fill="{t["grey"]}">{esc(prefix)}</tspan>'
            f'<tspan fill="{t["cyan"]}">{esc(key)}</tspan>'
            f'<tspan fill="{t["grey"]}">{esc(colon)}</tspan>'
            f'<tspan fill="{t["line"]}">{esc(dots)}</tspan>'
            f'<tspan fill="{vc}"> {esc(value)}</tspan></text>'
        )
        iy += info_lh

    # palette strip (UI colors only)
    if theme == "dark":
        pal = ["#1e293b", "#334155", "#64748b", "#94a3b8", "#67e8f9", "#22d3ee", "#e2e8f0", "#f8fafc"]
    else:
        pal = ["#e2e8f0", "#cbd5e1", "#94a3b8", "#64748b", "#0e7490", "#0891b2", "#164e63", "#0f172a"]
    sw = 11
    pal_y = ay0 + art_h - (line_h * 0.2 if mode == "ascii" else 0) + 10
    if mode == "blocks":
        pal_y = ay0 - line_h * 0.75 + rows * line_h + 10
    height = int(max(height, pal_y + 28 + pad))
    pal_x0 = ax0 + max(0, (art_w - len(pal) * sw * 1.35) / 2)
    pal_nodes = [
        f'<rect x="{pal_x0 + i * sw * 1.35:.1f}" y="{pal_y:.1f}" width="{sw}" height="{sw}" rx="2" fill="{c}"/>'
        for i, c in enumerate(pal)
    ]

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="sudopimp@github">
  <title>sudopimp@github — Fernando Lazzarin</title>
  <defs>
    <filter id="soft" x="-3%" y="-3%" width="106%" height="106%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="{t["shadow"]}" flood-opacity="0.4"/>
    </filter>
    <clipPath id="round"><rect width="{width}" height="{height}" rx="12" ry="12"/></clipPath>
  </defs>
  <g clip-path="url(#round)" filter="url(#soft)">
    <rect width="{width}" height="{height}" fill="{t["bg"]}"/>
    <rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="12" ry="12" fill="none" stroke="{t["stroke"]}" stroke-width="1"/>
    <g id="portrait">{"".join(art_nodes)}</g>
    <g id="palette">{"".join(pal_nodes)}</g>
    <g id="info">{"".join(info_nodes)}</g>
  </g>
</svg>
'''
    return svg, width, height


def qa_svg(svg: str, mode: str) -> None:
    import re

    info = re.search(r'<g id="info">(.*?)</g>', svg, re.S)
    assert info, "missing info group"
    fills = set(re.findall(r'fill="(#[0-9a-fA-F]{6})"', info.group(1)))
    # only cyan/white/grey family
    for f in fills:
        r, g, b = int(f[1:3], 16), int(f[3:5], 16), int(f[5:7], 16)
        # allow cyan (g and b high, r low-mid), greys (r≈g≈b), white/near-white
        is_grey = abs(r - g) < 25 and abs(g - b) < 25 and abs(r - b) < 25
        is_cyan = b >= r + 20 and g >= r  # cyan/teal
        is_dark_line = max(r, g, b) < 80
        assert is_grey or is_cyan or is_dark_line, f"UI forbidden color {f}"
    assert "Fernando" in svg and "WAITDEAD" in svg
    print(f"  QA ok mode={mode} ui_fills={sorted(fills)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Portrait image (default: assets/me.png or session photo)",
    )
    ap.add_argument("--mode", choices=("blocks", "ascii", "both"), default="both")
    ap.add_argument("--cols", type=int, default=0, help="Override columns")
    ap.add_argument("--stamp", default="", help="Output filename stamp")
    ap.add_argument("--out", type=Path, default=ROOT)
    args = ap.parse_args()

    # Resolve source photo
    candidates = [
        args.source,
        ROOT / "assets" / "fernando-source.png",
        Path(
            "/home/fer/.grok/sessions/%2Fhome%2Ffer%2FDownloads%2Fsudopimp-robotrola%2Frobotrola-web/019f5ca9-c2b9-7350-acd3-bfed01ff9b51/assets/image-7dda9438-13e6-4b75-97b3-591080cea66e.png"
        ),
        ROOT / "assets" / "me.png",
    ]
    source = next(p for p in candidates if p and p.exists())
    print("source:", source)

    try:
        import cairosvg
    except ImportError as e:
        raise SystemExit("pip install cairosvg") from e

    portrait = prep_portrait(source, 900)
    (args.out / "assets").mkdir(exist_ok=True)
    portrait.save(args.out / "assets" / "me.png", "PNG", optimize=True)

    stamp = args.stamp or datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    modes = ["blocks", "ascii"] if args.mode == "both" else [args.mode]

    for mode in modes:
        if mode == "ascii":
            # Correct aspect: rows ≈ cols * 0.52
            cols = args.cols or 78
            rows = max(20, int(round(cols * 0.52)))
            art = ascii_cells(portrait, cols, rows)
            plain = "\n".join("".join(ch for ch, _ in row) for row in art)
            (args.out / "ascii-art.txt").write_text(plain + "\n")
        else:
            # Half-blocks: visual square → cols wide, rows ≈ cols * 0.52
            cols = args.cols or 64
            rows = max(18, int(round(cols * 0.52)))
            art = block_cells(portrait, cols, rows)

        print(f"mode={mode} grid={cols}x{rows}")

        for theme in ("dark", "light"):
            svg, w, h = build_svg(theme, art, mode, cols, rows)
            qa_svg(svg, f"{mode}/{theme}")
            name = f"card-{mode}-{theme}-{stamp}"
            svg_path = args.out / f"{name}.svg"
            png_path = args.out / f"{name}.png"
            svg_path.write_text(svg, encoding="utf-8")
            cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1400)
            print(f"  wrote {png_path.name} ({w}x{h} → png {png_path.stat().st_size} bytes)")

        # Also write canonical names for the chosen primary mode later
        if mode == "blocks":
            for theme in ("dark", "light"):
                src_png = args.out / f"card-{mode}-{theme}-{stamp}.png"
                # preview path
                if theme == "dark":
                    import shutil

                    shutil.copy(src_png, args.out / "preview-verify.png")

    # Write pointer file for README helper
    (args.out / ".card_stamp").write_text(stamp + "\n")
    print("stamp:", stamp)
    print("Open preview-verify.png and inspect before push.")


if __name__ == "__main__":
    main()
