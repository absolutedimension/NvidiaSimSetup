import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .config import settings
from .models import MagicToken, Student


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_magic_token(db: Session, email: str) -> str:
    """Create a single-use magic token, store its hash, return the raw token."""
    raw = secrets.token_urlsafe(32)
    mt = MagicToken(
        token_hash=_hash(raw),
        email=email.lower().strip(),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.MAGIC_TTL_MIN),
    )
    db.add(mt)
    db.commit()
    return raw


def consume_magic_token(db: Session, raw: str) -> str | None:
    """Validate + burn a token. Returns the email if valid, else None."""
    mt = db.query(MagicToken).filter_by(token_hash=_hash(raw)).first()
    if not mt or mt.used_at is not None or mt.expires_at < datetime.utcnow():
        return None
    mt.used_at = datetime.utcnow()
    db.commit()
    return mt.email


def get_or_create_student(db: Session, email: str) -> Student:
    email = email.lower().strip()
    s = db.query(Student).filter_by(email=email).first()
    if not s:
        s = Student(email=email, is_admin=(email in settings.ADMIN_EMAILS))
        db.add(s)
        db.commit()
        db.refresh(s)
    return s
