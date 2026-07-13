# sudopimp profile

## Split assets

| Use | File | Notes |
|-----|------|--------|
| **ASCII card** (README) | `assets/me.png` | Your real photo → glyphs via neofetch-profile API |
| **GitHub profile picture** | `assets/github-avatar.png` | Robot face — upload manually in settings |
| Config | `neofetch.v4.json` / `neofetch.json` | Points ASCII at `me.png` |

## Set the robot as GitHub avatar (manual)

API cannot set the avatar. Do this once:

1. Open https://github.com/settings/profile  
2. Click the avatar → upload `assets/github-avatar.png` (robot)  
3. Save  

## Commit identity (required)

```bash
git config --local user.name "sudopimp"
git config --local user.email "301054894+sudopimp@users.noreply.github.com"
gh api user --jq .login   # must print sudopimp
```
