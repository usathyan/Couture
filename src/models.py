from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
import uuid
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    manager = "manager"
    staff = "staff"

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

class ExpenseStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ExpenseBase(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"

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

class SareeBase(BaseModel):
    name: str
    description: Optional[str] = None
    procurement_cost_inr: float = Field(..., gt=0)
    markup_percentage: float = Field(default=20.0, ge=0)

class Saree(SareeBase):
    id: uuid.UUID
    selling_price_usd: float
    image_urls: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class ProcurementRecordBase(BaseModel):
    saree_id: uuid.UUID
    procured_by_user_id: uuid.UUID
    cost_inr: float
    inr_to_usd_exchange_rate: float

class ProcurementRecord(ProcurementRecordBase):
    id: uuid.UUID
    procurement_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcurementCreate(BaseModel):
    saree_name: str
    saree_description: Optional[str] = None
    procurement_cost_inr: float
    markup_percentage: Optional[float] = None
    # In a real app, this would be an UploadFile 