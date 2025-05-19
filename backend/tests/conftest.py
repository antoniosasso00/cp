import asyncio
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def client():
    """
    Fornisce un client HTTP asincrono per i test delle API FastAPI
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client 