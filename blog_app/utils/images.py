import uuid
from pathlib import Path
from PIL import Image


def allowed_file(filename: str, allowed_exts: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts


def process_image(image_path: Path, max_width: int, max_height: int, quality: int):
    """Resize/optimize and convert to RGB if needed; saves JPEG in place."""
    img = Image.open(image_path)

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


def unique_image_name() -> str:
    return f"{uuid.uuid4().hex}.jpg"
