#!/bin/bash

set -euo pipefail

# ---- Config ----
ZIP_URL="https://huggingface.co/code-philia/halligan-models/resolve/main/models.zip?download=true"  # 🔁 Replace this
ZIP_FILE="models.zip"
TARGET_DIR="halligan/models"

# ---- Go to script directory ----
cd "$(dirname "$0")"

# ---- Download .zip ----
echo "Downloading $ZIP_URL..."
curl -L "$ZIP_URL" -o "$ZIP_FILE"

# ---- Unzip (creates /models) ----
echo "Unzipping $ZIP_FILE..."
unzip -q "$ZIP_FILE"

# ---- Replace target directory ----
echo "Replacing $TARGET_DIR..."
rm -rf "$TARGET_DIR"
mv models "$TARGET_DIR"

# ---- Clean up ----
rm -f "$ZIP_FILE"

echo "✅ Update complete."