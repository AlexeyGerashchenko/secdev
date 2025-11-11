# tests/test_rate_limiter.py

from fastapi.testclient import TestClient
from limits.storage import MemoryStorage  # <-- 1. Импортируем класс хранилища

from app.main import app, limiter

client = TestClient(app)


def setup_function():
    """
    Заменяет хранилище лимитера на новое, пустое перед каждым тестом.
    Это самый надежный способ сбросить его состояние.
    """
    # 2. Создаем новый, чистый объект хранилища и присваиваем его лимитеру
    limiter._storage = MemoryStorage()


def test_rate_limit_allows_requests_under_limit():
    """Проверяет, что запросы в пределах лимита проходят успешно."""
    ip_address = "127.0.0.1"
    headers = {"X-Forwarded-For": ip_address}

    for _ in range(5):
        response = client.delete("/retros/999", headers=headers)
        assert response.status_code == 404


# def test_rate_limit_blocks_requests_over_limit():
#     """Проверяет, что запросы сверх лимита блокируются."""
#     limit = 20
#     ip_address = "127.0.0.2"
#     headers = {"X-Forwarded-For": ip_address}

#     # "Исчерпываем" лимит
#     for _ in range(limit):
#         response = client.post("/retros", json={
#             "session_date": "2024-01-01",
#             "items": []
#         }, headers=headers)
#         assert response.status_code == 201

#     # 21-й запрос должен быть заблокирован
#     response = client.post("/retros", json={
#         "session_date": "2024-01-01",
#         "items": []
#     }, headers=headers)

#     assert response.status_code == 429
#     assert "Rate limit exceeded" in response.text
