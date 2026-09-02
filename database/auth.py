"""
Authentication module.

Design choices, deliberately kept dependency-free (no external auth library
needed — everything here uses Python's standard library only):

- Passwords are never stored in plain text. Each password is hashed with
  PBKDF2-HMAC-SHA256 (100,000 iterations) plus a unique random salt per
  user, using hashlib from the standard library.
- After login, the client gets an opaque random session token (not the
  password, not a predictable ID). The token is looked up server-side on
  every request that needs identity — the client never has enough
  information to forge one.
- Sessions expire after 12 hours so a leaked token doesn't stay valid forever.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta

PBKDF2_ITERATIONS = 100_000
SESSION_LIFETIME_HOURS = 12


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split("$")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return secrets.compare_digest(derived.hex(), hash_hex)


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def create_session(db, user_type: str, user_id: int) -> str:
    from models import Session
    token = generate_token()
    db.add(Session(token=token, user_type=user_type, user_id=user_id))
    db.commit()
    return token


def get_session(db, token: str):
    from models import Session
    session = db.query(Session).filter(Session.token == token).first()
    if not session:
        return None
    if datetime.utcnow() - session.created_at > timedelta(hours=SESSION_LIFETIME_HOURS):
        db.delete(session)
        db.commit()
        return None
    return session


def revoke_session(db, token: str):
    from models import Session
    db.query(Session).filter(Session.token == token).delete()
    db.commit()
