"""
Logo Service — QR Generator SC
Handles logo loading from local files and URLs with caching and validation.
"""

import hashlib
import io
from pathlib import Path
from typing import Optional, Tuple
from urllib.error import URLError
from urllib.request import urlopen

from PIL import Image

SUPPORTED_FORMATS = ("PNG", "JPG", "JPEG", "WEBP")
MAX_URL_TIMEOUT = 10  # seconds
CACHE_DIR = Path.home() / ".qr_generator_sc_logo_cache"
MAX_LOGO_DIMENSION = 2048
MIN_LOGO_DIMENSION = 8


class LogoService:
    """Handles logo loading, validation, and caching."""

    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────

    def load_from_file(self, filepath: str) -> Optional[Image.Image]:
        """
        Load logo from local file.
        Returns PIL Image or None on error.
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return None

            img = Image.open(path)
            # Validate format
            if img.format.upper() not in SUPPORTED_FORMATS:
                return None

            # Convert to RGBA for transparency support
            img = img.convert("RGBA")
            return img
        except Exception:
            return None

    def load_from_url(self, url: str) -> Optional[Image.Image]:
        """
        Load logo from URL with caching.
        Returns PIL Image or None on error.
        """
        try:
            # Check cache first
            cache_key = hashlib.md5(url.encode()).hexdigest()
            cache_file = CACHE_DIR / f"{cache_key}.png"

            if cache_file.exists():
                try:
                    img = Image.open(cache_file)
                    img = img.convert("RGBA")
                    return img
                except Exception:
                    cache_file.unlink(missing_ok=True)

            # Download from URL con User-Agent
            from urllib.request import Request

            req = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            with urlopen(req, timeout=MAX_URL_TIMEOUT) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                if "image" not in content_type:
                    return None

                img_data = response.read()
                if not img_data:
                    return None

                img = Image.open(io.BytesIO(img_data))

                if img.format and img.format.upper() not in SUPPORTED_FORMATS:
                    return None

                img = img.convert("RGBA")
                cache_file.write_bytes(img_data)
                return img

        except (URLError, TimeoutError, Exception):
            return None

    def validate_image(self, img: Image.Image) -> bool:
        """Check if image is valid for logo use."""
        if not img:
            return False
        if img.size[0] < MIN_LOGO_DIMENSION or img.size[1] < MIN_LOGO_DIMENSION:
            return False
        if img.size[0] > MAX_LOGO_DIMENSION or img.size[1] > MAX_LOGO_DIMENSION:
            return False
        return True

    def resize_logo(
        self,
        img: Image.Image,
        qr_size: int,
        logo_size_percent: float,
    ) -> Optional[Image.Image]:
        """
        Resize logo to target size maintaining aspect ratio.
        logo_size_percent: 10, 15, 20, 25
        """
        try:
            # Calculate target size based on QR size
            target_size = int(qr_size * (logo_size_percent / 100))
            target_size = max(target_size, MIN_LOGO_DIMENSION)

            # Maintain aspect ratio
            img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

            # Create square canvas if needed
            if img.width != img.height:
                size = max(img.width, img.height)
                canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
                offset = ((size - img.width) // 2, (size - img.height) // 2)
                canvas.paste(img, offset, img)
                return canvas

            return img
        except Exception:
            return None

    def apply_opacity(self, img: Image.Image, opacity: float) -> Image.Image:
        """Apply opacity to logo (0.0 to 1.0)."""
        try:
            # Clamp opacity
            opacity = max(0.0, min(1.0, opacity))

            # Get alpha channel
            alpha = (
                img.split()[3]
                if len(img.split()) == 4
                else Image.new("L", img.size, 255)
            )

            # Apply opacity
            alpha = alpha.point(lambda p: int(p * opacity))

            # Create new image with modified alpha
            result = img.copy()
            result.putalpha(alpha)
            return result
        except Exception:
            return img

    def clear_cache(self) -> None:
        """Clear all cached logos."""
        try:
            for cache_file in CACHE_DIR.glob("*.png"):
                cache_file.unlink()
        except Exception:
            pass
