#!/usr/bin/env bash

set -e

APP_NAME="vpn-client"
APPIMAGE_NAME="VPN_Client"

echo "[1/7] Cleaning old artifacts..."

rm -rf build
rm -rf dist
rm -rf AppDir
rm -f *.spec

echo "[2/7] Generating PyInstaller spec..."

pyi-makespec \
    --onefile \
    --windowed \
    --name "${APP_NAME}" \
    src/desktop/main.py

echo "[3/7] Fixing spec..."

sed -i "s/pathex=\[\]/pathex=\['src'\]/" "${APP_NAME}.spec"

echo "[4/7] Building executable..."

pyinstaller "${APP_NAME}.spec" --clean

echo "[5/7] Creating AppDir..."

mkdir -p AppDir/usr/bin

cp dist/${APP_NAME} AppDir/usr/bin/
cp docs/vpn-client.png AppDir/

cat > AppDir/${APP_NAME}.desktop << EOF
[Desktop Entry]
Type=Application
Name=VPN Client
Exec=${APP_NAME}
Icon=vpn-client
Categories=Network;
Terminal=false
EOF

cat > AppDir/AppRun << EOF
#!/bin/bash
exec "\$APPDIR/usr/bin/${APP_NAME}" "\$@"
EOF

chmod +x AppDir/AppRun
chmod +x AppDir/usr/bin/${APP_NAME}

echo "[6/7] Building AppImage..."

appimagetool AppDir

echo "[7/7] Done."

echo
echo "Created:"
ls -lh *.AppImage
