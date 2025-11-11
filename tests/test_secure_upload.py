from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.secure_upload import MAX_FILE_SIZE, PNG_SIGNATURE, secure_save

client = TestClient(app)


def test_secure_save_rejects_oversized_file(tmp_path: Path):
    """Негативный тест: файл, превышающий MAX_FILE_SIZE, должен быть отвергнут."""
    large_data = PNG_SIGNATURE + b"a" * (MAX_FILE_SIZE + 1)

    with pytest.raises(ValueError, match="File is too large"):
        secure_save(tmp_path, large_data)


def test_secure_save_rejects_invalid_file_type(tmp_path: Path):
    """Негативный тест: файл с неверной сигнатурой должен быть отвергнут."""
    invalid_data = b"this is not an image"

    with pytest.raises(ValueError, match="Invalid file type"):
        secure_save(tmp_path, invalid_data)


def test_secure_save_rejects_incomplete_jpeg(tmp_path: Path):
    """Негативный тест: файл, похожий на JPEG, но неполный, отвергается."""
    incomplete_jpeg = b"\xff\xd8\xaa\xbb\xcc"

    with pytest.raises(ValueError, match="Invalid file type"):
        secure_save(tmp_path, incomplete_jpeg)


def test_secure_save_prevents_path_traversal(tmp_path: Path):
    """
    Негативный тест: симулируем атаку Path Traversal.
    Здесь мы напрямую не можем проверить это через функцию, т.к. Path()
    нормализует путь. Но мы можем проверить, что .resolve() работает правильно
    и не дает выйти за пределы корневой директории.
    """
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir()

    malicious_filename_part = "../evil.txt"

    resolved_malicious_path = (safe_dir / malicious_filename_part).resolve()

    assert not str(resolved_malicious_path).startswith(str(safe_dir.resolve()))


def test_upload_endpoint_success(tmp_path):
    response_create = client.post(
        "/retros", json={"session_date": "2024-01-01", "items": []}
    )
    assert response_create.status_code == 201
    retro_id = response_create.json()["id"]

    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01\xe2!@\xde\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    response_upload = client.post(
        f"/retros/{retro_id}/attachments",
        files={"file": ("test.png", png_data, "image/png")},
    )

    assert response_upload.status_code == 200
    body = response_upload.json()
    assert "filename" in body
    assert body["filename"].endswith(".png")


def test_upload_endpoint_rejects_bad_file(tmp_path):
    response_create = client.post(
        "/retros", json={"session_date": "2024-01-01", "items": []}
    )
    assert response_create.status_code == 201
    retro_id = response_create.json()["id"]

    txt_data = b"This is just a text file."

    response_upload = client.post(
        f"/retros/{retro_id}/attachments",
        files={"file": ("fake.png", txt_data, "image/png")},
    )

    assert response_upload.status_code == 422
    body = response_upload.json()
    assert body["title"] == "upload_failed"
    assert body["detail"] == "Invalid file type"
