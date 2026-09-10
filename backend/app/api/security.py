"""
Shared API-key security scheme.

Declaring this with fastapi.security (instead of reading the header
manually in middleware) makes FastAPI itself aware that certain routes
require an X-API-Key header - it shows up in the auto-generated OpenAPI
schema, which is what makes Swagger UI display an "Authorize" button
and let you supply the key once, directly in the browser, rather than
the key only working from a script or Invoke-RestMethod call that sets
the header itself.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY = "devmate-local-key"

# auto_error=False: if the header is missing, APIKeyHeader hands back
# None instead of raising its own generic 403 - that lets require_api_key
# below raise a 401 with a clearer, DevMate-specific message instead.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Security(_api_key_header)) -> str:
    if key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header",
        )
    return key