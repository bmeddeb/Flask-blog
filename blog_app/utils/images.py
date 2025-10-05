import logging
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


def allowed_file(filename: str, allowed_exts: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts


def process_image(image_path: Path, max_width: int, max_height: int, quality: int):
    """Resize/optimize and convert to RGB if needed; saves JPEG in place."""
    try:
        img = Image.open(image_path)
    except UnidentifiedImageError as e:
        logger.error(f"Unidentified image format: {str(e)}")
        raise ValueError(f"Unsupported image format: {str(e)}")
    except (OSError, IOError) as e:
        logger.error(f"Failed to open image: {str(e)}")
        raise ValueError(f"Failed to open image: {str(e)}")

    try:
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        img.save(image_path, "JPEG", quality=quality, optimize=True)
        return img
    except (OSError, IOError) as e:
        logger.error(f"Failed to process/save image: {str(e)}")
        raise ValueError(f"Failed to process image: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing image: {str(e)}")
        raise ValueError(f"Image processing failed: {str(e)}")


def unique_image_name(ext: str = "jpg") -> str:
    return f"{uuid.uuid4().hex}.{ext.lower()}"

def is_svg_filename(filename: str) -> bool:
    return filename.lower().endswith('.svg')
