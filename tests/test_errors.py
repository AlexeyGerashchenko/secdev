from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_error_format():
    """Проверяет формат ошибки 404 Not Found на соответствие RFC 7807."""
    response = client.get("/items/999")

    assert response.status_code == 404
    body = response.json()

    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body

    assert body["status"] == 404
    assert body["title"] == "not_found"
    assert "item not found" in body["detail"]


def test_validation_error_format_on_retro():
    """Проверяет формат ошибки 422 Unprocessable Entity на эндпоинте ретро."""
    response = client.post(
        "/retros",
        json={
            "session_date": "2999-01-01",
            "items": [],
        },
    )

    assert response.status_code == 422
    body = response.json()

    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body

    assert body["status"] == 422
    assert body["title"] == "Validation Error"
    assert "Session date cannot be in the future" in body["detail"]
