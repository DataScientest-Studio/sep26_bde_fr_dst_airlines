import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from src.api.config import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Vérifie la présence et la validité de l'API Key dans le header X-API-Key."""
    if not api_key or not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide ou manquante (Header 'X-API-Key' requis).",
        )
    return api_key
