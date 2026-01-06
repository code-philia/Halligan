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
    from .detector import Detector
    from .segmenter import Segmenter
except ImportError as e1:
    _import_errors.append(f"Relative import failed: {e1}")
    # Strategy 2: Try absolute imports from same directory
    try:
        from clip import CLIP
        from detector import Detector
        from segmenter import Segmenter
    except ImportError as e2:
        _import_errors.append(f"Absolute import failed: {e2}")
        # Strategy 3: Try alternative naming (lowercase/uppercase variations)
        try:
            from .CLIP import CLIP
            from .Detector import Detector
            from .Segmenter import Segmenter
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
