from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app

client = TestClient(app)


def test_secret_info_endpoint_hides_secret():

    from app.config import settings

    response = client.get("/secret-info")
    assert response.status_code == 200
    body = response.json()

    assert settings.SECRET_KEY not in str(body)
    assert body == {"message": "Sensitive info processed successfully"}


def test_settings_load_from_environment_variable(monkeypatch):
    secret_value = "secret_from_env_for_test"
    monkeypatch.setenv("SECRET_KEY", secret_value)

    test_settings = Settings()

    assert test_settings.SECRET_KEY == secret_value


def test_settings_use_default_value_when_env_is_not_set(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    env_file = Path(".env")
    renamed_env_file = Path(".env.bak")

    try:
        if env_file.exists():
            env_file.rename(renamed_env_file)

        test_settings = Settings()

        assert test_settings.SECRET_KEY == "default_secret_for_local_dev"

    finally:
        if renamed_env_file.exists():
            renamed_env_file.rename(env_file)
