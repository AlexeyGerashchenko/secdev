import pytest
from fastapi.testclient import TestClient

from app.main import _RETROS_DB, app

client = TestClient(app)


def setup_function():
    _RETROS_DB.clear()


def test_create_retro_success():
    retro_data = {
        "session_date": "2024-08-15",
        "items": [
            {
                "what_went_well": "Fast delivery",
                "to_improve": "API documentation",
                "actions": "Update Swagger docs",
            }
        ],
    }

    response = client.post("/retros", json=retro_data)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    assert body["session_date"] == "2024-08-15"
    assert len(body["items"]) == 1

    assert len(_RETROS_DB) == 1
    assert _RETROS_DB[0].id == body["id"]


def test_create_retro_future_date_error():
    """Тест проверяет ошибку валидации в НОВОМ формате RFC 7807."""
    response = client.post(
        "/retros",
        json={
            "session_date": "2999-01-01",
            "items": [],
        },
    )
    assert response.status_code == 422
    body = response.json()
    # Проверяем новый формат
    assert body["title"] == "Validation Error"
    assert body["status"] == 422
    assert "Session date cannot be in the future" in body["detail"]


def test_get_retros_empty():
    response = client.get("/retros")
    assert response.status_code == 200
    assert response.json() == []


def test_get_single_retro_not_found():
    """Тест проверяет ошибку 404 в НОВОМ формате RFC 7807."""
    response = client.get("/retros/999")
    assert response.status_code == 404
    body = response.json()
    # Проверяем новый формат
    assert body["title"] == "not_found"
    assert body["status"] == 404
    assert "Retro with id=999 not found" in body["detail"]


def test_full_crud_cycle():
    response = client.post("/retros", json={"session_date": "2024-01-10", "items": []})
    assert response.status_code == 201
    created_retro = response.json()
    retro_id = created_retro["id"]

    response = client.get(f"/retros/{retro_id}")
    assert response.status_code == 200
    assert response.json()["session_date"] == "2024-01-10"

    response = client.get("/retros")
    assert response.status_code == 200
    assert len(response.json()) == 1

    update_data = {
        "session_date": "2024-01-11",
        "items": [{"what_went_well": "a", "to_improve": "b", "actions": "c"}],
    }
    response = client.put(f"/retros/{retro_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["session_date"] == "2024-01-11"
    assert len(response.json()["items"]) == 1

    response = client.delete(f"/retros/{retro_id}")
    assert response.status_code == 204

    response = client.get(f"/retros/{retro_id}")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "field, value, error_part",
    [
        ("what_went_well", "", "String should have at least 1 character"),
        ("to_improve", "a" * 3000, "String should have at most 2048 characters"),
        ("actions", " ", "String should have at least 1 character"),
    ],
)
def test_create_retro_fails_on_invalid_string_length(field, value, error_part):
    """Негативный тест: проверяет отказ при некорректной длине строки."""
    retro_data = {
        "session_date": "2024-08-15",
        "items": [
            {
                "what_went_well": "Good sprint",
                "to_improve": "Docs",
                "actions": "Write docs",
            }
        ],
    }
    retro_data["items"][0][field] = value

    response = client.post("/retros", json=retro_data)

    assert response.status_code == 422
    assert error_part in response.text


def test_create_retro_fails_on_too_many_items():
    """Негативный тест: проверяет отказ при слишком большом количестве items."""
    too_many_items = [{"what_went_well": "a", "to_improve": "b", "actions": "c"}] * 21

    retro_data = {
        "session_date": "2024-08-15",
        "items": too_many_items,
    }
    response = client.post("/retros", json=retro_data)

    assert response.status_code == 422
    assert "List should have at most 20 items" in response.text


def test_create_retro_fails_on_extra_field():
    """Негативный тест: проверяет отказ при наличии лишнего поля в запросе."""
    retro_data = {
        "session_date": "2024-08-15",
        "items": [],
        "unexpected_field": "this should be rejected",
    }
    response = client.post("/retros", json=retro_data)

    assert response.status_code == 422
    assert "Extra inputs are not permitted" in response.text
