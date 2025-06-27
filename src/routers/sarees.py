from typing import List
from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_saree_service
from src.models import Saree
from src.services.saree_service import SareeService

router = APIRouter(
    prefix="/sarees",
    tags=["sarees"],
)


@router.get("/", response_model=List[Saree])
def list_sarees(saree_service: SareeService = Depends(get_saree_service)):
    """
    Retrieve a list of all available sarees.
    """
    return saree_service.list_sarees()


@router.get("/{saree_id}", response_model=Saree)
def get_saree(saree_id: str, saree_service: SareeService = Depends(get_saree_service)):
    """
    Retrieve details for a single saree by its ID.
    """
    saree = saree_service.get_saree_by_id(saree_id)
    if not saree:
        raise HTTPException(status_code=404, detail="Saree not found")
    return saree 