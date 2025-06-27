import uuid
from datetime import datetime, timezone
from typing import Optional, List

from src.models import (
    Saree, ProcurementRecord, ProcurementCreate, ProcurementApproval, 
    ProcurementStatus, User, UserRole, ExpenseCreate, ExpenseCategory
)
from src.services.dynamodb import DynamoDBService


class ProcurementService(DynamoDBService):
    def __init__(self, endpoint_url: Optional[str] = None):
        super().__init__(table_name="procurement_records", endpoint_url=endpoint_url)
        # Initialize expense service for creating procurement-related expenses
        # Import here to avoid circular imports
        from src.services.expense_service import ExpenseService
        self.expense_service = ExpenseService(endpoint_url=endpoint_url)

    def _get_inr_to_usd_exchange_rate(self) -> float:
        """
        Retrieves the current INR to USD exchange rate.
        NOTE: This is a placeholder. In a real application, this would call
        an external currency conversion API.
        """
        return 83.50  # Hardcoded exchange rate for now

    def submit_procurement(self, procurement_data: ProcurementCreate, user: User) -> dict:
        """Submit a procurement request for manager approval."""
        # Create saree record
        saree_id = uuid.uuid4()
        saree = Saree(
            id=saree_id,
            name=procurement_data.saree_name,
            description=procurement_data.saree_description,
            procurement_cost_inr=procurement_data.procurement_cost_inr,
            markup_percentage=procurement_data.markup_percentage or 20.0,
            image_urls=procurement_data.image_urls or [],
            procurement_status=ProcurementStatus.pending
        )
        
        # Store saree in sarees table
        saree_service = SareeService(endpoint_url=self.endpoint_url)
        saree_service.put_item(Item=saree.model_dump(mode='json'))
        
        # Create procurement record
        procurement_id = uuid.uuid4()
        procurement_record = ProcurementRecord(
            id=procurement_id,
            saree_id=saree_id,
            procured_by_user_id=user.id,
            cost_inr=procurement_data.procurement_cost_inr,
            inr_to_usd_exchange_rate=0.0,  # Will be set during approval
            procurement_date=datetime.now(timezone.utc),
            status=ProcurementStatus.pending
        )
        
        item = procurement_record.model_dump(mode='json')
        self.put_item(Item=item)
        return item

    def get_pending_procurements(self, user: User) -> List[dict]:
        """Get pending procurement requests. Partners can see all, managers see only their own."""
        response = self.table.scan(
            FilterExpression="attribute_exists(#status) AND #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ProcurementStatus.pending.value}
        )
        
        procurements = response.get('Items', [])
        
        # Partners and admins can see all pending procurements
        if user.role in [UserRole.partner, UserRole.admin]:
            return procurements
        
        # Managers can see all pending procurements (for now - can be restricted later)
        return procurements

    def approve_procurement(self, procurement_id: str, approval: ProcurementApproval, manager: User) -> Optional[dict]:
        """Approve a procurement request with optional additional costs and markup."""
        # Get the procurement record
        response = self.table.get_item(Key={'id': procurement_id})
        if 'Item' not in response:
            return None
        
        procurement_item = response['Item']
        
        # Get the associated saree
        saree_service = SareeService(endpoint_url=self.endpoint_url)
        saree_response = saree_service.table.get_item(Key={'id': procurement_item['saree_id']})
        if 'Item' not in saree_response:
            return None
        
        saree_item = saree_response['Item']
        
        # Calculate final costs
        base_cost_inr = float(procurement_item['cost_inr'])
        additional_costs = approval.additional_costs_inr or 0.0
        total_cost_inr = base_cost_inr + additional_costs
        
        # Use provided exchange rate or default
        exchange_rate = approval.exchange_rate_override or 0.012  # Default INR to USD rate
        
        # Calculate markup
        markup_percentage = approval.markup_override or float(saree_item.get('markup_percentage', 20.0))
        cost_usd = total_cost_inr * exchange_rate
        final_price_usd = cost_usd * (1 + markup_percentage / 100)
        
        # Create procurement-related expense for additional costs if any
        if additional_costs > 0:
            expense_data = ExpenseCreate(
                description=f"Additional procurement costs for saree: {saree_item['name']} (Procurement ID: {procurement_id})",
                amount=additional_costs * exchange_rate,  # Convert to USD
                currency="USD",
                category=ExpenseCategory.procurement_related
            )
            self.expense_service.create_expense(expense_data, manager)
        
        # Update procurement record
        update_response = self.table.update_item(
            Key={'id': procurement_id},
            UpdateExpression="""
                SET #status = :status, 
                    reviewed_by_user_id = :manager_id, 
                    review_date = :review_date,
                    manager_additional_costs_inr = :additional_costs,
                    manager_markup_override = :markup_override,
                    final_selling_price_usd = :final_price,
                    inr_to_usd_exchange_rate = :exchange_rate
            """,
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": ProcurementStatus.approved.value,
                ":manager_id": str(manager.id),
                ":review_date": datetime.now(timezone.utc).isoformat(),
                ":additional_costs": additional_costs,
                ":markup_override": markup_percentage,
                ":final_price": final_price_usd,
                ":exchange_rate": exchange_rate
            },
            ReturnValues="ALL_NEW"
        )
        
        # Update saree record
        saree_service.table.update_item(
            Key={'id': procurement_item['saree_id']},
            UpdateExpression="SET procurement_status = :status, selling_price_usd = :price",
            ExpressionAttributeValues={
                ":status": ProcurementStatus.approved.value,
                ":price": final_price_usd
            }
        )
        
        return update_response.get('Attributes')

    def reject_procurement(self, procurement_id: str, manager: User, reason: Optional[str] = None) -> Optional[dict]:
        """Reject a procurement request."""
        # Get the procurement record
        response = self.table.get_item(Key={'id': procurement_id})
        if 'Item' not in response:
            return None
        
        procurement_item = response['Item']
        
        # Update procurement record
        update_response = self.table.update_item(
            Key={'id': procurement_id},
            UpdateExpression="SET #status = :status, reviewed_by_user_id = :manager_id, review_date = :review_date",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": ProcurementStatus.rejected.value,
                ":manager_id": str(manager.id),
                ":review_date": datetime.now(timezone.utc).isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        
        # Update saree record
        saree_service = SareeService(endpoint_url=self.endpoint_url)
        saree_service.table.update_item(
            Key={'id': procurement_item['saree_id']},
            UpdateExpression="SET procurement_status = :status",
            ExpressionAttributeValues={
                ":status": ProcurementStatus.rejected.value
            }
        )
        
        return update_response.get('Attributes')

    # Legacy method for backward compatibility
    def process_procurement(self, procurement_data: ProcurementCreate, user: User) -> dict:
        """Legacy method - directly processes procurement without approval workflow."""
        # Create saree record
        saree_id = uuid.uuid4()
        saree = Saree(
            id=saree_id,
            name=procurement_data.saree_name,
            description=procurement_data.saree_description,
            procurement_cost_inr=procurement_data.procurement_cost_inr,
            markup_percentage=procurement_data.markup_percentage or 20.0,
            image_urls=procurement_data.image_urls or [],
            procurement_status=ProcurementStatus.approved  # Auto-approved in legacy mode
        )
        
        # Calculate selling price
        inr_to_usd_rate = 0.012  # Default exchange rate
        base_cost_usd = procurement_data.procurement_cost_inr * inr_to_usd_rate
        selling_price_usd = base_cost_usd * (1 + saree.markup_percentage / 100)
        saree.selling_price_usd = selling_price_usd
        
        # Store saree in sarees table
        saree_service = SareeService(endpoint_url=self.endpoint_url)
        saree_service.put_item(Item=saree.model_dump(mode='json'))
        
        # Create procurement record
        procurement_id = uuid.uuid4()
        procurement_record = ProcurementRecord(
            id=procurement_id,
            saree_id=saree_id,
            procured_by_user_id=user.id,
            cost_inr=procurement_data.procurement_cost_inr,
            inr_to_usd_exchange_rate=inr_to_usd_rate,
            procurement_date=datetime.now(timezone.utc),
            status=ProcurementStatus.approved,
            final_selling_price_usd=selling_price_usd
        )
        
        item = procurement_record.model_dump(mode='json')
        self.put_item(Item=item)
        return item

    def list_procurements(self) -> List[dict]:
        """Lists all procurement records."""
        response = self.table.scan()
        return response.get('Items', [])


# Import here to avoid circular imports
from src.services.saree_service import SareeService 