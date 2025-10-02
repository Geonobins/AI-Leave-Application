from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
import secrets
from app.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    # Extract salt and hash
    try:
        if ':' in hashed_password:
            salt, stored_hash = hashed_password.split(':')
            password_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        else:
            # Legacy support - direct hash comparison
            password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            return password_hash == hashed_password
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password with salt"""
    try:
        # Generate a random salt
        salt = secrets.token_hex(16)
        # Create hash with salt
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        # Return salt:hash format
        return f"{salt}:{password_hash}"
    except Exception as e:
        print(f"Password hashing error: {e}")
        # Fallback to simple hash
        return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None