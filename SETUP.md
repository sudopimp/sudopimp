# Pure ASCII profile card

## What this is

**Real ASCII characters** (`@ # $ % M W *` …) colored from Fernando’s photo.

Not pixel blocks. Not half-block mosaics.

Tool: [ascii-image-converter](https://github.com/TheZoraiz/ascii-image-converter)  
`~/.local/bin/ascii-image-converter`

## Regenerate

```bash
export PATH="$HOME/.local/bin:$PATH"
# prep face → assets/ascii-lab/face.png then:
ascii-image-converter assets/ascii-lab/face.png --color --complex -d 100,55 \
  --save-img assets/ascii-lab/ship --only-save --save-bg 11,18,32,100
# then rebuild card (agent script / PIL compositor)
```

## Files

| File | Role |
|------|------|
| `profile-card-dark-pureascii.png` | README card |
| `ascii-art.txt` | Plain glyph dump (proof of ASCII) |
| `assets/github-avatar.png` | Robot for GitHub profile photo |

## Author

```bash
git config --local user.name "sudopimp"
git config --local user.email "301054894+sudopimp@users.noreply.github.com"
```
