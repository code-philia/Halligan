#!/bin/bash

set -euo pipefail

# ---- Config ----
ZIP_URL="https://huggingface.co/code-philia/halligan-models/resolve/main/models.zip?download=true"  # 🔁 Replace this
ZIP_FILE="models.zip"
ZIP_SHA256=""
TARGET_DIR="halligan/models"
CACHE_DIR=".cache/models"

# ---- Go to script directory ----
cd "$(dirname "$0")"

# ---- Download .zip ----
mkdir -p "$CACHE_DIR"

echo "Downloading $ZIP_URL (resumable)..."
if [ -f "$CACHE_DIR/$ZIP_FILE" ]; then
  echo "Found cached archive at $CACHE_DIR/$ZIP_FILE"
else
  curl -L -C - "$ZIP_URL" -o "$CACHE_DIR/$ZIP_FILE"
fi

# Optional checksum
if [ -n "$ZIP_SHA256" ]; then
  echo "$ZIP_SHA256  $CACHE_DIR/$ZIP_FILE" | shasum -a 256 -c -
fi

cp "$CACHE_DIR/$ZIP_FILE" "$ZIP_FILE"

# ---- Unzip (creates /models) ----
echo "Unzipping $ZIP_FILE..."
unzip -q -o "$ZIP_FILE"

# ---- Replace target directory ----
echo "Replacing $TARGET_DIR..."
# Backup existing __init__.py if it exists
if [ -f "$TARGET_DIR/__init__.py" ]; then
    echo "Backing up existing __init__.py..."
    cp "$TARGET_DIR/__init__.py" /tmp/models_init_backup.py || true
fi

rm -rf "$TARGET_DIR"
mkdir -p "$(dirname "$TARGET_DIR")"
mv models "$TARGET_DIR"

# Restore __init__.py if the downloaded models don't have one, or merge exports
if [ ! -f "$TARGET_DIR/__init__.py" ]; then
    echo "Creating __init__.py for models module..."
    if [ -f /tmp/models_init_backup.py ]; then
        cp /tmp/models_init_backup.py "$TARGET_DIR/__init__.py"
    else
        cat > "$TARGET_DIR/__init__.py" << 'EOF'
"""
Halligan models module.

This module provides CLIP, Segmenter (FastSAM), and Detector (DINOv2) models
for visual CAPTCHA solving.

Models are downloaded from Hugging Face via get_models.sh script.
"""

import os

# Try multiple import strategies to handle different model file structures
_import_errors = []

# Strategy 1: Try relative imports (most common)
try:
    from .clip import CLIP
    from .segmenter import Segmenter
    from .detector import Detector
except ImportError as e1:
    _import_errors.append(f"Relative import failed: {e1}")
    # Strategy 2: Try absolute imports from same directory
    try:
        from clip import CLIP
        from segmenter import Segmenter
        from detector import Detector
    except ImportError as e2:
        _import_errors.append(f"Absolute import failed: {e2}")
        # Strategy 3: Try alternative naming (lowercase/uppercase variations)
        try:
            from .CLIP import CLIP
            from .Segmenter import Segmenter
            from .Detector import Detector
        except ImportError as e3:
            _import_errors.append(f"Alternative import failed: {e3}")
            # All import strategies failed
            models_dir = os.path.dirname(__file__)
            models_files = os.listdir(models_dir) if os.path.exists(models_dir) else []
            raise ImportError(
                "halligan.models components (CLIP/Segmenter/Detector) are not available. "
                f"Models directory: {models_dir}, Files: {models_files}. "
                f"Import errors: {'; '.join(_import_errors)}. "
                "Please run 'bash get_models.sh' to download the models from Hugging Face."
            ) from e3

__all__ = ["CLIP", "Segmenter", "Detector"]
EOF
    fi
elif [ -f /tmp/models_init_backup.py ]; then
    # If both exist, check if the downloaded one exports the required classes
    if ! grep -q "from.*import.*CLIP" "$TARGET_DIR/__init__.py" && ! grep -q "^CLIP" "$TARGET_DIR/__init__.py"; then
        echo "Merging __init__.py exports..."
        # Append exports from backup if not present
        if grep -q "from.*import.*CLIP\|^CLIP" /tmp/models_init_backup.py; then
            echo "" >> "$TARGET_DIR/__init__.py"
            echo "# Additional exports" >> "$TARGET_DIR/__init__.py"
            grep -E "^(from|import|__all__)" /tmp/models_init_backup.py >> "$TARGET_DIR/__init__.py" || true
        fi
    fi
fi

# ---- Clean up ----
rm -f "$ZIP_FILE"

echo "✅ Update complete."
