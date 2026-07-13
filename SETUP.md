# sudopimp profile — true ASCII neofetch

Live: https://github.com/sudopimp  
Repo: https://github.com/sudopimp/sudopimp

## What “ASCII” means here

Each cell on the left is a **real text character** (`@`, `#`, `M`, `.`, etc.) chosen from image brightness — same idea as [neofetch](https://github.com/dylanaraps/neofetch) / [jeantimex/neofetch-profile](https://github.com/jeantimex/neofetch-profile).

This is **not** a pixel/rect mosaic.

| File | Role |
|------|------|
| `neofetch-dark.png` / `neofetch-light.png` | Cards on the profile README |
| `ascii-art.txt` | Plain mono dump of the glyph grid |
| `assets/robot-ascii.png` | Source face for conversion + optional Vercel API |
| `neofetch.json` | Config for `neofetch-profile.vercel.app` (optional) |
| `scripts/generate_neofetch.py` | Rebuild cards |

## Regenerate

```bash
pip install pillow cairosvg
python scripts/generate_neofetch.py
# denser glyphs:
python scripts/generate_neofetch.py --cols 56 --rows 32
```

## Optional: live Vercel ASCII API

```
https://neofetch-profile.vercel.app/api?username=sudopimp&theme=github-dark&config=https%3A%2F%2Fraw.githubusercontent.com%2Fsudopimp%2Fsudopimp%2Fmain%2Fneofetch.json
```

## Profile photo

Upload `assets/github-avatar.png` at https://github.com/settings/profile
