from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
import uuid
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    staff = "staff"
    manager = "manager"
    partner = "partner"
    admin = "admin"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.staff

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: uuid.UUID
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


# --- Expense Models ---

class ExpenseCategory(str, Enum):
    general = "general"
    procurement_related = "procurement_related"
    marketing = "marketing"
    operational = "operational"

class ExpenseStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ExpenseBase(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    category: ExpenseCategory = ExpenseCategory.general

class ExpenseCreate(ExpenseBase):
    pass

class Expense(ExpenseBase):
    id: uuid.UUID
    submitted_by_user_id: uuid.UUID
    submission_date: datetime
    status: ExpenseStatus = ExpenseStatus.pending
    reviewed_by_user_id: Optional[uuid.UUID] = None
    review_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Procurement Models ---

class ProcurementStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class SareeBase(BaseModel):
    name: str
    description: Optional[str] = None
    procurement_cost_inr: float = Field(..., gt=0)
    markup_percentage: float = Field(default=20.0, ge=0)

class Saree(SareeBase):
    id: uuid.UUID
    selling_price_usd: Optional[float] = None  # Only set after procurement approval
    image_urls: List[str] = []
    procurement_status: ProcurementStatus = ProcurementStatus.pending

    model_config = ConfigDict(from_attributes=True)


class ProcurementRecordBase(BaseModel):
    saree_id: uuid.UUID
    procured_by_user_id: uuid.UUID
    cost_inr: float
    inr_to_usd_exchange_rate: float

class ProcurementRecord(ProcurementRecordBase):
    id: uuid.UUID
    procurement_date: datetime
    status: ProcurementStatus = ProcurementStatus.pending
    reviewed_by_user_id: Optional[uuid.UUID] = None
    review_date: Optional[datetime] = None
    manager_additional_costs_inr: Optional[float] = None
    manager_markup_override: Optional[float] = None
    final_selling_price_usd: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ProcurementCreate(BaseModel):
    saree_name: str
    saree_description: Optional[str] = None
    procurement_cost_inr: float = Field(..., gt=0)
    markup_percentage: Optional[float] = None
    image_urls: Optional[List[str]] = []  # URLs to uploaded images


class ProcurementApproval(BaseModel):
    additional_costs_inr: Optional[float] = Field(None, ge=0)
    markup_override: Optional[float] = Field(None, ge=0)
    exchange_rate_override: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None


class ProcurementStatusUpdate(BaseModel):
    status: ProcurementStatus
    approval_details: Optional[ProcurementApproval] = None 