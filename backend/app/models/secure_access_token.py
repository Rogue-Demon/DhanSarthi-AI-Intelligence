"""SecureAccessToken model — opaque token + PIN for Secure Financial Intelligence access."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, pk_column


class SecureAccessToken(Base, TimestampMixin):
    """Opaque secure access token for the Financial Intelligence page.

    Each token maps to exactly one User.  The PIN is stored as a bcrypt
    hash using the same ``hash_password`` / ``verify_password`` utilities
    as the main auth system.

    Security properties
    -------------------
    - Token is a 64-character hex string (``secrets.token_hex(32)``).
    - PIN is bcrypt-hashed — never stored or returned as plaintext.
    - ``failed_attempts`` triggers a temporary lockout after 5 failures.
    - ``locked_until`` enforces a 15-minute cooldown after lockout.
    - ``expires_at`` provides automatic token expiration.

    This model does NOT store any financial data.
    """

    __tablename__ = "secure_access_tokens"

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<SecureAccessToken id={self.id} user_id={self.user_id}>"
