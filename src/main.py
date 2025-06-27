from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from src.routers import users, procurement, sarees, expenses
from src.routers import auth
from src.dependencies import get_user_service
from src.security import create_access_token, verify_password
from src.services.user_service import UserService

app = FastAPI(
    title="Couture Bookkeeping API",
    description="API for managing bookkeeping for a Mysore silk saree business.",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(procurement.router)
app.include_router(sarees.router)
app.include_router(expenses.router)

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user = user_service.get_user_by_email(email=form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Welcome to the Couture Bookkeeping API!"} 