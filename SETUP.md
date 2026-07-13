# sudopimp profile card

## Generate (local)

```bash
cd github-profile
pip install pillow cairosvg
python scripts/generate_card.py --mode blocks --cols 80 --stamp myrun
```

| Mode | What |
|------|------|
| `blocks` (default quality) | Half-block truecolor — face is readable |
| `ascii` | Classic `@#%` glyphs — abstract for photos |

## Assets

| File | Role |
|------|------|
| `profile-card-dark.png` / `light` | README card |
| `assets/me.png` | Processed portrait used by the generator |
| `assets/github-avatar.png` | **Robot** — upload as GitHub profile photo |
| `scripts/generate_card.py` | Source of truth |

## Commits must be sudopimp

```bash
git config --local user.name "sudopimp"
git config --local user.email "301054894+sudopimp@users.noreply.github.com"
gh api user --jq .login   # sudopimp
```
