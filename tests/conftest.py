import pytest
import uuid
from datetime import datetime, timezone
from src.models import Saree, ProcurementRecord, ProcurementStatus, User, UserRole, ExpenseCategory
from src import dependencies

# This file contains the setup for all tests.
# It is automatically discovered by pytest.
# It uses dependency injection to replace real services (like database connectors)
# with simple, predictable mock objects that use an in-memory dictionary as a database.

# --- Shared In-Memory DB for all tests ---
mock_db = {
    "users": {},
    "sarees": {},
    "procurement_records": {},
}

# --- Simple, Standalone Mock Services ---

class MockUserService:
    def __init__(self):
        self.users = {}

    def create_user(self, user_data: dict) -> dict:
        email = user_data["email"]
        self.users[email] = user_data
        return user_data

    def get_user_by_email(self, email: str):
        return self.users.get(email)
    
    def clear(self):
        """Clear all data for test isolation"""
        self.users.clear()

class MockProcurementService:
    def __init__(self):
        pass

    def submit_procurement(self, procurement_data, user):
        """New method for approval workflow - updated to use User object"""
        saree_id = uuid.uuid4()
        
        saree = Saree(
            id=saree_id,
            name=procurement_data.saree_name,
            description=procurement_data.saree_description,
            procurement_cost_inr=procurement_data.procurement_cost_inr,
            markup_percentage=procurement_data.markup_percentage or 20.0,
            selling_price_usd=None,  # Will be set after approval
            image_urls=procurement_data.image_urls or [],
            procurement_status=ProcurementStatus.pending
        )
        
        procurement_record = ProcurementRecord(
            id=uuid.uuid4(),
            saree_id=saree_id,
            procured_by_user_id=user.id,
            cost_inr=procurement_data.procurement_cost_inr,
            inr_to_usd_exchange_rate=0.0,  # Will be set during approval
            procurement_date=datetime.now(timezone.utc),
            status=ProcurementStatus.pending
        )
        
        mock_db["sarees"][str(saree.id)] = saree.model_dump(mode='json')
        mock_db["procurement_records"][str(procurement_record.id)] = procurement_record.model_dump(mode='json')
        
        return procurement_record.model_dump(mode='json')

    def get_pending_procurements(self, user):
        """Get pending procurement records - supports role-based access"""
        pending_records = [
            record for record in mock_db["procurement_records"].values()
            if record.get("status") == "pending"
        ]
        
        # Partners and admins can see all pending procurements
        if user.role in [UserRole.partner, UserRole.admin]:
            return pending_records
        
        # Managers can see all pending procurements (for now)
        return pending_records

    def approve_procurement(self, procurement_id, approval, manager):
        """Approve a procurement - updated to use new parameter structure"""
        # Find the procurement record
        procurement_record = None
        for record in mock_db["procurement_records"].values():
            if record["id"] == procurement_id:
                procurement_record = record
                break
        
        if not procurement_record:
            return None

        # Find the saree record
        saree_record = mock_db["sarees"].get(procurement_record["saree_id"])
        if not saree_record:
            return None

        # Calculate final price
        base_cost = procurement_record["cost_inr"]
        additional_costs = approval.additional_costs_inr or 0.0
        total_cost_inr = base_cost + additional_costs
        
        exchange_rate = approval.exchange_rate_override or 0.012
        markup = approval.markup_override or saree_record["markup_percentage"]
        
        cost_usd = total_cost_inr * exchange_rate
        final_price = cost_usd * (1 + markup / 100)

        # Update records
        procurement_record["status"] = "approved"
        procurement_record["reviewed_by_user_id"] = str(manager.id)
        procurement_record["review_date"] = datetime.now(timezone.utc).isoformat()
        procurement_record["final_selling_price_usd"] = round(final_price, 2)
        procurement_record["manager_additional_costs_inr"] = additional_costs
        procurement_record["manager_markup_override"] = markup
        procurement_record["inr_to_usd_exchange_rate"] = exchange_rate

        saree_record["procurement_status"] = "approved"
        saree_record["selling_price_usd"] = round(final_price, 2)

        return procurement_record

    def reject_procurement(self, procurement_id, manager, reason=None):
        """Reject a procurement - updated to use new parameter structure"""
        # Find the procurement record
        procurement_record = None
        for record in mock_db["procurement_records"].values():
            if record["id"] == procurement_id:
                procurement_record = record
                break
        
        if not procurement_record:
            return None

        # Update records
        procurement_record["status"] = "rejected"
        procurement_record["reviewed_by_user_id"] = str(manager.id)
        procurement_record["review_date"] = datetime.now(timezone.utc).isoformat()

        # Update saree record
        saree_record = mock_db["sarees"].get(procurement_record["saree_id"])
        if saree_record:
            saree_record["procurement_status"] = "rejected"

        return procurement_record

    def list_procurements(self):
        """List all procurement records"""
        return list(mock_db["procurement_records"].values())

    def process_procurement(self, procurement_data, user):
        """Legacy method for backward compatibility - updated to use User object"""
        exchange_rate = 0.012  # Updated exchange rate
        cost_usd = procurement_data.procurement_cost_inr * exchange_rate
        markup = procurement_data.markup_percentage or 20.0
        selling_price = cost_usd * (1 + markup / 100)
        saree_id = uuid.uuid4()
        
        saree = Saree(
            id=saree_id,
            name=procurement_data.saree_name,
            description=procurement_data.saree_description,
            procurement_cost_inr=procurement_data.procurement_cost_inr,
            markup_percentage=markup,
            selling_price_usd=round(selling_price, 2),
            image_urls=procurement_data.image_urls or [],
            procurement_status=ProcurementStatus.approved  # Legacy auto-approves
        )
        procurement_record = ProcurementRecord(
            id=uuid.uuid4(),
            saree_id=saree_id,
            procured_by_user_id=user.id,
            cost_inr=procurement_data.procurement_cost_inr,
            inr_to_usd_exchange_rate=exchange_rate,
            procurement_date=datetime.now(timezone.utc),
            status=ProcurementStatus.approved,
            final_selling_price_usd=round(selling_price, 2)
        )
        
        mock_db["sarees"][str(saree.id)] = saree.model_dump(mode='json')
        mock_db["procurement_records"][str(procurement_record.id)] = procurement_record.model_dump(mode='json')
        
        return procurement_record.model_dump(mode='json')

    def create_procurement(self, procurement_data, user_id):
        return {"saree": {"name": "Test Saree"}, "procurement_record": {}}

class MockSareeService:
    def list_sarees(self):
        return list(mock_db["sarees"].values())
    def get_saree_by_id(self, saree_id: str):
        return mock_db["sarees"].get(saree_id)
    def get_saree(self, saree_id: str):
        return next((s for s in self.sarees if s["id"] == saree_id), None)

class MockExpenseService:
    def __init__(self):
        self.expenses = {}

    def create_expense(self, expense_data, user):
        """Create a new expense - updated to support categories"""
        expense_id = str(uuid.uuid4())
        expense = {
            "id": expense_id,
            "description": expense_data.description,
            "amount": expense_data.amount,
            "currency": expense_data.currency,
            "category": expense_data.category.value if hasattr(expense_data, 'category') else ExpenseCategory.general.value,
            "submitted_by_user_id": str(user.id),
            "submission_date": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }
        self.expenses[expense_id] = expense
        mock_db.setdefault("expenses", {})[expense_id] = expense
        return expense

    def list_expenses(self):
        return list(self.expenses.values())

    def update_expense_status(self, expense_id, new_status, manager):
        if expense_id in self.expenses:
            self.expenses[expense_id]["status"] = new_status.value
            self.expenses[expense_id]["reviewed_by_user_id"] = str(manager.id)
            self.expenses[expense_id]["review_date"] = datetime.now(timezone.utc).isoformat()
            return self.expenses[expense_id]
        return None
    
    def clear(self):
        """Clear all data for test isolation"""
        self.expenses.clear()
        if "expenses" in mock_db:
            mock_db["expenses"].clear()

# --- Centralized Mock Instances ---

mock_user_service = MockUserService()
mock_procurement_service = MockProcurementService()
mock_saree_service = MockSareeService()
mock_expense_service = MockExpenseService()

# --- Centralized Fixture to apply mocks ---

@pytest.fixture(autouse=True)
def override_dependencies():
    """
    This fixture automatically applies mock services for every test run,
    ensuring a clean, isolated environment.
    """
    from src.main import app

    # Clear all mock data before each test
    mock_db["users"].clear()
    mock_db["sarees"].clear()
    mock_db["procurement_records"].clear()
    mock_user_service.clear()
    mock_expense_service.clear()

    app.dependency_overrides[dependencies.get_user_service] = lambda: mock_user_service
    app.dependency_overrides[dependencies.get_procurement_service] = lambda: mock_procurement_service
    app.dependency_overrides[dependencies.get_saree_service] = lambda: mock_saree_service
    app.dependency_overrides[dependencies.get_expense_service] = lambda: mock_expense_service

    yield

    # Clean up dependency overrides after test run
    app.dependency_overrides.clear() 