from functools import lru_cache
from fastapi import Depends, HTTPException, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer

from src.services.user_service import UserService
from src.services.procurement_service import ProcurementService
from src.services.saree_service import SareeService
from src.services.expense_service import ExpenseService
from src.models import User, UserRole
from src.security import verify_access_token


# --- Dependency Injection ---

@lru_cache()
def get_settings():
    # In the future, this can read from a .env file or other config
    return {
        "dynamodb_endpoint_url": "http://localhost:8000"
    }


def get_user_service() -> UserService:
    """
    Dependency function to get a UserService instance.
    """
    settings = get_settings()
    return UserService(endpoint_url=settings["dynamodb_endpoint_url"])


def get_procurement_service() -> ProcurementService:
    """
    Dependency function to get a ProcurementService instance.
    """
    settings = get_settings()
    return ProcurementService(endpoint_url=settings["dynamodb_endpoint_url"])


def get_saree_service() -> SareeService:
    """
    Dependency function to get a SareeService instance.
    """
    settings = get_settings()
    return SareeService(endpoint_url=settings["dynamodb_endpoint_url"])


# In a real app, this would be in a config file
DYNAMODB_ENDPOINT_URL = "http://localhost:8000"

def get_expense_service():
    """Dependency injector for ExpenseService."""
    # In a real app, this might pull the endpoint_url from settings
    return ExpenseService(endpoint_url=DYNAMODB_ENDPOINT_URL)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_access_token(token, credentials_exception)
    email = payload.get("sub")
    if email is None:
        raise credentials_exception
    user_dict = user_service.get_user_by_email(email=email)
    if user_dict is None:
        raise credentials_exception
    return User(**user_dict)


def require_manager_role(current_user: Annotated[User, Depends(get_current_user)]):
    """Dependency that raises an exception if the user is not a manager."""
    if current_user.role != UserRole.manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user 