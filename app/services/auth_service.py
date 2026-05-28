"""
User types password "mypass123"
        ↓
We hash it into "$2b$12$xK9..."  (bcrypt)
        ↓
We store the hash, never the real password
        ↓
On login, we hash their input and compare hashes

"""

import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(plain_password:str)->str:
    """takes a plain password and returns a hashed version using bcrypt. 
    We store the hash, not the real password."""

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password:str, hashed_password:str)->bool:
    """takes a plain password and a hashed password, hashes the plain password and compares it to the hashed version. 
    Returns True if they match, False otherwise."""

    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
        )

def create_access_token(data: dict) -> str:
    """
    creates a JWT access token with the given data and an expiration time.
    The token is signed with a secret key and algorithm defined in the config.

    """
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str):
    """
    Decodes a JWT access token and returns the payload if valid, or None if invalid.
    The token is verified using the secret key and algorithm defined in the config.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None