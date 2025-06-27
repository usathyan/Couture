from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated
import uuid

from src.models import Expense, ExpenseCreate, User, ExpenseStatus
from src.services.expense_service import ExpenseService
from src.dependencies import get_expense_service, require_manager_role, get_current_user

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Expense, status_code=status.HTTP_201_CREATED)
def submit_expense(
    expense_in: ExpenseCreate,
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Submit a new expense.
    Any authenticated user can submit an expense.
    """
    created_expense = expense_service.create_expense(expense_in, current_user)
    return created_expense

@router.get("/", response_model=List[Expense])
def list_all_expenses(
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    manager: Annotated[User, Depends(require_manager_role)],
):
    """
    Retrieve all expenses.
    Only users with the 'manager' role can access this.
    """
    expenses = expense_service.list_expenses()
    return expenses

@router.patch("/{expense_id}/status", response_model=Expense)
def update_expense_status(
    expense_id: uuid.UUID,
    status_update: ExpenseStatus,
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    manager: Annotated[User, Depends(require_manager_role)],
):
    """
    Update the status of an expense (e.g., approve or reject).
    Only users with the 'manager' role can access this.
    """
    updated_expense = expense_service.update_expense_status(
        expense_id=str(expense_id), new_status=status_update, manager=manager
    )
    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )
    return updated_expense 