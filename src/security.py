from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.models import User
from src.services.user_service import UserService

# --- Configuration ---
SECRET_KEY = "a_very_secret_key_that_should_be_in_a_config_file"  # Replace with a real secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)


# --- JWT Token Handling ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception) -> dict:
    """Verifies a JWT access token and returns the payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(UserService)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_access_token(token, credentials_exception)
    email_from_payload = payload.get("sub")
    if email_from_payload is None:
        raise credentials_exception
    email: str = email_from_payload

    user = user_service.get_user_by_email(email=email)
    if user is None:
        raise credentials_exception
    return User(**user) 