import uuid
from pathlib import Path
from typing import Union

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"

ALLOWED_MIME_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
}


def sniff_mime_type(data: bytes) -> Union[str, None]:
    """Определяет MIME-тип по сигнатуре файла (magic bytes)."""
    if data.startswith(PNG_SIGNATURE):
        return "image/png"
    if data.startswith(JPEG_SOI) and data.endswith(JPEG_EOI):
        return "image/jpeg"
    return None


def secure_save(upload_dir: Path, data: bytes) -> Path:
    """
    Безопасно сохраняет файл, выполняя все необходимые проверки.
    Возвращает путь к сохраненному файлу.
    """
    if len(data) > MAX_FILE_SIZE:
        raise ValueError("File is too large")

    mime_type = sniff_mime_type(data)
    if not mime_type or mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Invalid file type")

    try:
        resolved_root = upload_dir.resolve(strict=True)
    except FileNotFoundError:
        raise ValueError("Upload directory does not exist")

    ext = ALLOWED_MIME_TYPES[mime_type]
    secure_filename = f"{uuid.uuid4()}{ext}"
    file_path = (resolved_root / secure_filename).resolve()

    if not str(file_path).startswith(str(resolved_root)):
        raise ValueError("Path traversal attempt detected")

    if any(p.is_symlink() for p in file_path.parents):
        raise ValueError("Saving through symlinks is forbidden")

    file_path.write_bytes(data)
    return file_path
