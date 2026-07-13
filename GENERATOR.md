# Card generator

## Install

```bash
# ascii-image-converter (Linux amd64 example)
curl -sL https://github.com/TheZoraiz/ascii-image-converter/releases/latest/download/ascii-image-converter_Linux_amd64_64bit.tar.gz | tar -xz
install -m 755 ascii-image-converter_Linux_amd64_64bit/ascii-image-converter ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"

pip install pillow
```

## Generate

```bash
# optional: replace assets/source/face.png with your photo
python scripts/generate.py
```

Writes `card-dark.png`, `card-light.png`, and `ascii-art.txt`.

## Profile photo (robot)

Upload `assets/source/robot-avatar.png` at https://github.com/settings/profile

## Commit identity

```bash
git config --local user.name "sudopimp"
git config --local user.email "301054894+sudopimp@users.noreply.github.com"
```
