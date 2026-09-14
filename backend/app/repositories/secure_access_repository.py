"""Repository for SecureAccessToken persistence and queries."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.secure_access_token import SecureAccessToken
from app.repositories.base import BaseRepository


class SecureAccessRepository(BaseRepository[SecureAccessToken]):
    """Repository managing SecureAccessToken database operations."""

    def __init__(self, db: Session) -> None:
        super().__init__(SecureAccessToken, db)

    def get_by_token(self, token: str) -> SecureAccessToken | None:
        """Retrieve a SecureAccessToken by its opaque token string."""
        stmt = select(self.model).where(self.model.token == token)
        return self._db.execute(stmt).scalar_one_or_none()

    def increment_failed_attempts(self, record: SecureAccessToken) -> None:
        """Increment failed PIN attempts and apply lockout if threshold reached."""
        record.failed_attempts += 1
        if record.failed_attempts >= 5:
            from datetime import timedelta
            record.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        self._db.commit()

    def reset_failed_attempts(self, record: SecureAccessToken) -> None:
        """Reset failed attempts and remove lockout on successful authentication."""
        record.failed_attempts = 0
        record.locked_until = None
        self._db.commit()
