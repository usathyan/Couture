from typing import Annotated
from fastapi import APIRouter, Depends, status

from src.dependencies import get_procurement_service, get_current_user
from src.models import User, ProcurementCreate, Saree
from src.routers.users import get_current_user
from src.services.procurement_service import ProcurementService

router = APIRouter(
    prefix="/procurements",
    tags=["procurements"],
    responses={404: {"description": "Not found"}},
)


@router.get("/hello")
def test_procurement_auth():
    """
    A test endpoint to verify that authentication is working for this router.
    """
    return {"message": "You are an authenticated user. Welcome to Procurements!"}


@router.post("/", response_model=Saree, status_code=status.HTTP_201_CREATED)
def create_procurement(
    procurement_in: ProcurementCreate,
    procurement_service: Annotated[ProcurementService, Depends(get_procurement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Records the procurement of a new saree.
    This is a protected endpoint and requires authentication.
    """
    created_saree = procurement_service.process_procurement(
        procurement_data=procurement_in, user_id=current_user.id
    )
    return created_saree 