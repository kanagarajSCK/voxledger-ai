import pytest
from pydantic import SecretStr
from app.core.config import Settings


def test_gnani_settings_defaults():
    s = Settings(GNANI_API_KEY=SecretStr("test_key_1234567890"))
    assert s.GNANI_STT_MODEL == "prisma-v3.0"
    assert s.GNANI_TTS_MODEL == "timbre-v3.0"
    assert s.GNANI_STT_ENABLED is True
    assert s.GNANI_TTS_ENABLED is True
    assert s.has_gnani_credentials is True


def test_gnani_api_key_masked():
    s = Settings(GNANI_API_KEY=SecretStr("super_secret_gnani_key"))
    # In string/repr, secret must never be exposed
    assert "super_secret_gnani_key" not in repr(s.GNANI_API_KEY)
    assert "super_secret_gnani_key" not in str(s.GNANI_API_KEY)
    # Accessible only through get_secret_value()
    assert s.GNANI_API_KEY.get_secret_value() == "super_secret_gnani_key"


def test_gnani_placeholder_key_detection():
    s1 = Settings(GNANI_API_KEY=SecretStr("your_gnani_api_key_here"))
    assert s1.has_gnani_credentials is False

    s2 = Settings(GNANI_API_KEY=SecretStr(""))
    assert s2.has_gnani_credentials is False
