import uuid
from datetime import datetime, timezone
from typing import Optional, List

from src.models import Expense, ExpenseCreate, ExpenseStatus, User
from src.services.dynamodb import DynamoDBService

class ExpenseService(DynamoDBService):
    def __init__(self, endpoint_url: Optional[str] = None):
        super().__init__(table_name="expenses", endpoint_url=endpoint_url)

    def create_expense(self, expense_data: ExpenseCreate, user: User) -> dict:
        """Creates a new expense record in the database."""
        expense_id = uuid.uuid4()
        new_expense = Expense(
            id=expense_id,
            submitted_by_user_id=user.id,
            submission_date=datetime.now(timezone.utc),
            **expense_data.model_dump()
        )
        item = new_expense.model_dump(mode='json')
        self.put_item(Item=item)
        return item

    def list_expenses(self) -> List[dict]:
        """Lists all expenses. In a real app, this would have pagination."""
        response = self.table.scan()
        return response.get('Items', [])

    def update_expense_status(self, expense_id: str, new_status: ExpenseStatus, manager: User) -> Optional[dict]:
        """Updates the status of an expense."""
        response = self.table.update_item(
            Key={'id': expense_id},
            UpdateExpression="SET #s = :status, reviewed_by_user_id = :manager_id, review_date = :review_date",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": new_status.value,
                ":manager_id": str(manager.id),
                ":review_date": datetime.now(timezone.utc).isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        return response.get('Attributes') 