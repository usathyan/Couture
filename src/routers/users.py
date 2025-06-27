import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from src.dependencies import get_user_service, get_current_user
from src.models import User, UserCreate
from src.security import create_access_token, hash_password, verify_password, verify_access_token
from src.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: UserService = Depends(get_user_service),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_access_token(token, credentials_exception)
    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    user_dict = user_service.get_user_by_email(email=email)
    if user_dict is None:
        raise credentials_exception
    return User(**user_dict)


@router.post("/register", response_model=User)
def register_user(
    user_in: UserCreate, user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user.
    """
    user_dict = user_service.get_user_by_email(email=user_in.email)
    if user_dict:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pass = hash_password(user_in.password)
    new_user_id = str(uuid.uuid4())
    
    user_data = user_in.model_dump()
    user_data.pop("password")
    user_data.update(id=new_user_id, hashed_password=hashed_pass)

    # Ensure the role is converted to its string value for DynamoDB
    user_data["role"] = user_in.role.value

    created_user = user_service.create_user(user_data=user_data)
    return User(**created_user)


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Fetch the details of the currently authenticated user.
    """
    return current_user 