from pathlib import Path

from app.core.config import ENV_FILE, Settings


def test_settings_uses_backend_env_file_relative_to_config_module():
    expected_env_file = Path(__file__).resolve().parents[1] / '.env'

    assert ENV_FILE == expected_env_file
    assert ENV_FILE.is_absolute()
    assert Settings.model_config.get('env_file') == expected_env_file


def test_environment_variables_override_backend_env_file(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite+aiosqlite:///environment-override.db')
    monkeypatch.setenv('APP_ENV', 'testing')
    monkeypatch.setenv('SSH_ENABLE', 'false')
    monkeypatch.setenv('JWT_SECRET_KEY', 'environment-test-secret-key-with-at-least-32-characters')
    monkeypatch.setenv('GOOGLE_API_KEY', 'environment-test-google-api-key')
    monkeypatch.setenv('GOOGLE_FILE_SEARCH_STORE_NAME', 'fileSearchStores/environment-test-store')

    settings = Settings()

    assert settings.database_url == 'sqlite+aiosqlite:///environment-override.db'
    assert settings.app_env == 'testing'
