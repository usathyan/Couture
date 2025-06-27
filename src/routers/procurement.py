from typing import Annotated, List
from fastapi import APIRouter, Depends, status, HTTPException

from src.dependencies import get_procurement_service, get_current_user, require_manager_role
from src.models import User, ProcurementCreate, ProcurementApproval, ProcurementStatus
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


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_procurement(
    procurement_in: ProcurementCreate,
    procurement_service: Annotated[ProcurementService, Depends(get_procurement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Submits a new saree procurement for manager approval.
    Staff can submit procurements with images and details.
    The procurement will be in pending status until approved by a manager.
    """
    created_procurement = procurement_service.submit_procurement(
        procurement_data=procurement_in, user=current_user
    )
    return created_procurement


@router.get("/pending", dependencies=[Depends(require_manager_role)])
def get_pending_procurements(
    procurement_service: Annotated[ProcurementService, Depends(get_procurement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get all procurement records that are pending approval.
    Manager+ only endpoint. Partners can see across all managers.
    """
    pending_procurements = procurement_service.get_pending_procurements(current_user)
    return {"pending_procurements": pending_procurements}


@router.post("/{procurement_id}/approve", dependencies=[Depends(require_manager_role)])
def approve_procurement(
    procurement_id: str,
    approval_details: ProcurementApproval,
    procurement_service: Annotated[ProcurementService, Depends(get_procurement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Approve a procurement with optional additional costs and markup adjustments.
    Manager+ only endpoint.
    
    Managers can:
    - Add additional costs in INR (transportation, handling, etc.) - classified as procurement-related expenses
    - Override the markup percentage
    - Override the exchange rate if needed
    - Add approval notes
    """
    result = procurement_service.approve_procurement(
        procurement_id=procurement_id,
        approval=approval_details,
        manager=current_user
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Procurement not found")
    return result


@router.post("/{procurement_id}/reject", dependencies=[Depends(require_manager_role)])
def reject_procurement(
    procurement_id: str,
    rejection_reason: str,
    procurement_service: Annotated[ProcurementService, Depends(get_procurement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Reject a procurement with a reason.
    Manager+ only endpoint.
    """
    result = procurement_service.reject_procurement(
        procurement_id=procurement_id,
        manager=current_user,
        reason=rejection_reason
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Procurement not found")
    return result


@router.get("/")
def list_all_procurements(
    procurement_service: Annotated[ProcurementService, Depends(get_procurement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    List all procurement records.
    Available to all authenticated users.
    """
    procurements = procurement_service.list_procurements()
    return {"procurements": procurements}


# Legacy endpoint for backward compatibility
@router.post("/legacy", status_code=status.HTTP_201_CREATED)
def create_procurement_legacy(
    procurement_in: ProcurementCreate,
    procurement_service: Annotated[ProcurementService, Depends(get_procurement_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Legacy endpoint for backward compatibility.
    Use /procurements/ (submit_procurement) for new implementations.
    """
    created_procurement = procurement_service.process_procurement(
        procurement_data=procurement_in, user=current_user
    )
    return created_procurement 