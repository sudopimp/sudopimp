# Card generator

## Presentation contract

| Surface | Rule |
|---------|------|
| Portrait | Pure-glyph ASCII (not pixels / half-blocks / braille) |
| Subject | Face + torso on void (background removed) |
| Text UI | Greyscale only — no rainbow keys, no palette-dot strip |
| README | Card image only |

## PII / likeness policy (intentional)

`assets/source/face.png` is the **public cutout** used to regenerate the card.
Publishing a likeness on a profile repo is **intentional** for this presentation card.

- Prefer regenerating from a **private** photo path that is never committed:
  `python scripts/generate.py --photo ~/private/fernando.jpg`
- The cutout written to `assets/source/face.png` may be committed so CI/others can
  rebuild without the private original.
- Do not commit uncropped full-resolution originals beyond the cutout.

Robot profile picture asset (GitHub Settings → avatar):

`assets/source/robot-avatar.png`

## Install (pinned)

```bash
# ascii-image-converter v1.13.1 (Linux amd64)
curl -sL https://github.com/TheZoraiz/ascii-image-converter/releases/download/v1.13.1/ascii-image-converter_Linux_amd64_64bit.tar.gz | tar -xz
install -m 755 ascii-image-converter_Linux_amd64_64bit/ascii-image-converter ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
ascii-image-converter --version   # expect v1.13.1

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate

```bash
export PATH="$HOME/.local/bin:$PATH"
python scripts/generate.py
# already-cut face.png:
python scripts/generate.py --no-rembg
```

Writes: `card-dark.png`, `card-light.png`, `ascii-art.txt`

## Tests

```bash
python -m unittest tests/test_generate_contract.py -v
```

## Commit identity

```bash
git config --local user.name "sudopimp"
git config --local user.email "301054894+sudopimp@users.noreply.github.com"
```

## GitHub profile sidebar (manual if API lacks `user` scope)

If `gh api -X PATCH /user` returns 404 / needs `user` scope:

1. https://github.com/settings/profile
2. **Name:** Fernando Lazzarin  
3. **Bio:** Building humanoid robotics & agent systems · Rust · Python · Claude Code · Robotrola  
4. **Company:** `>_WAITDEAD`  
5. **Location:** Mendoza, Argentina  
6. **URL:** https://robotrola.com  
7. **X username:** sudopimp  
8. **Profile picture:** upload `assets/source/robot-avatar.png`
