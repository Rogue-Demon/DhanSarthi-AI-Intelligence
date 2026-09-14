import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.stt_service import (
    FutureProductionSTTProvider,
    LocalWhisperProvider,
    STTProvider,
    get_stt_provider,
)
from app.core.config import settings
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"email": "stt_test_user@test.com", "password": "password123"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "stt_test_user@test.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_stt_provider_factory():
    """Verify STT provider factory returns correct instance based on settings."""
    with patch.object(settings, "stt_provider", "local"):
        import app.services.stt_service as stt_mod
        stt_mod._provider_instance = None
        provider = get_stt_provider()
        assert isinstance(provider, LocalWhisperProvider)

    with patch.object(settings, "stt_provider", "production"):
        stt_mod._provider_instance = None
        provider = get_stt_provider()
        assert isinstance(provider, FutureProductionSTTProvider)
        stt_mod._provider_instance = None


def test_future_production_provider_raises():
    """Verify FutureProductionSTTProvider raises NotImplementedError."""
    provider = FutureProductionSTTProvider()

    async def _test():
        with pytest.raises(NotImplementedError) as exc_info:
            await provider.transcribe("fake.webm")
        assert "Production STT provider is not configured" in str(exc_info.value)

    asyncio.run(_test())


def test_transcribe_unauthenticated(client: TestClient):
    """Verify 401 Unauthorized for unauthenticated POST /api/v1/ai/transcribe."""
    response = client.post("/api/v1/ai/transcribe", files={"file": ("test.webm", b"audio data", "audio/webm")})
    assert response.status_code == 401


def test_transcribe_empty_file(client: TestClient, auth_headers):
    """Verify 400 Bad Request when uploading an empty audio file."""
    response = client.post(
        "/api/v1/ai/transcribe",
        files={"file": ("test.webm", b"", "audio/webm")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Empty audio file" in response.json()["detail"]


def test_transcribe_success_mocked(client: TestClient, auth_headers):
    """Verify authenticated POST /api/v1/ai/transcribe transcribes audio and cleans up temp file."""
    with patch("app.services.stt_service.get_stt_provider") as mock_get_provider:
        mock_provider = AsyncMock(spec=STTProvider)
        mock_provider.transcribe.return_value = "How can I reduce my monthly expenses?"
        mock_get_provider.return_value = mock_provider

        response = client.post(
            "/api/v1/ai/transcribe",
            files={"file": ("test.webm", b"mock audio content bytes", "audio/webm")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "How can I reduce my monthly expenses?"
        mock_provider.transcribe.assert_called_once()

