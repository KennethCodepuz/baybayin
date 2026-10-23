"""Local-only authorization for developer reference material."""

import os
import secrets

from fastapi import Header, HTTPException, status


def require_reference_token(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv('BAYBAYIN_REFERENCE_TOKEN')
    if not token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Reference-library access is not configured')
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Reference-library authorization is required')
    if not secrets.compare_digest(authorization.removeprefix('Bearer '), token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Reference-library authorization was rejected')
