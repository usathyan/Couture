import pytest
import uuid
from datetime import datetime, timezone
from src.models import Saree, ProcurementRecord
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

    def process_procurement(self, procurement_data, user_id):
        exchange_rate = 83.50  # Hardcoded for test predictability
        cost_usd = procurement_data.procurement_cost_inr / exchange_rate
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
            image_urls=[]  # Empty list for now since we don't have image upload in tests
        )
        procurement_record = ProcurementRecord(
            id=uuid.uuid4(),
            saree_id=saree_id,
            procured_by_user_id=user_id,
            cost_inr=procurement_data.procurement_cost_inr,
            inr_to_usd_exchange_rate=exchange_rate,
            procurement_date=datetime.now(timezone.utc)
        )
        
        mock_db["sarees"][str(saree.id)] = saree.model_dump(mode='json')
        mock_db["procurement_records"][str(procurement_record.id)] = procurement_record.model_dump(mode='json')
        
        return saree

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
        self.expenses = []

    def create_expense(self, expense_data, user):
        from src.models import Expense
        import uuid
        from datetime import datetime, timezone

        new_expense = Expense(
            id=uuid.uuid4(),
            submitted_by_user_id=user.id,
            submission_date=datetime.now(timezone.utc),
            **expense_data.model_dump(),
        )
        # Convert enums and UUIDs to strings for the "database"
        item = new_expense.model_dump(mode="json")
        self.expenses.append(item)
        return item

    def list_expenses(self):
        return self.expenses

    def update_expense_status(self, expense_id, new_status, manager):
        from datetime import datetime, timezone
        for expense in self.expenses:
            if expense["id"] == expense_id:
                expense["status"] = new_status.value
                expense["reviewed_by_user_id"] = str(manager.id)
                expense["review_date"] = datetime.now(timezone.utc).isoformat()
                return expense
        return None
    
    def clear(self):
        """Clear all data for test isolation"""
        self.expenses.clear()

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