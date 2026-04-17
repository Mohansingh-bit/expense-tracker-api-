import bcrypt
from flask import jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)
from extensions import db
from models import User


def hash_password(plain: str) -> str:
    """Hash a plain text password using bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def generate_tokens(user_id: int) -> dict:
    """Generate both access and refresh tokens for a user."""
    return {
        "access_token": create_access_token(identity=str(user_id)),
        "refresh_token": create_refresh_token(identity=str(user_id))
    }


def get_current_user():
    """
    Get the currently authenticated user from JWT identity.
    Returns User object or None.
    Call this inside a @jwt_required() route.
    """
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))
