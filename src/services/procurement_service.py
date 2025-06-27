import uuid
from datetime import datetime, timezone
from typing import Optional

from src.models import ProcurementCreate, Saree, ProcurementRecord
from src.services.dynamodb import DynamoDBService


class ProcurementService:
    def __init__(self, endpoint_url: Optional[str] = None):
        self.saree_service = DynamoDBService(table_name="sarees", endpoint_url=endpoint_url)
        self.procurement_record_service = DynamoDBService(table_name="procurement_records", endpoint_url=endpoint_url)

    def _get_inr_to_usd_exchange_rate(self) -> float:
        """
        Retrieves the current INR to USD exchange rate.
        NOTE: This is a placeholder. In a real application, this would call
        an external currency conversion API.
        """
        return 83.50  # Hardcoded exchange rate for now

    def process_procurement(self, procurement_data: ProcurementCreate, user_id: uuid.UUID) -> Saree:
        """
        Processes a new procurement, creating a saree and a procurement record.
        """
        # 1. Get current exchange rate
        exchange_rate = self._get_inr_to_usd_exchange_rate()
        
        # 2. Calculate selling price
        cost_usd = procurement_data.procurement_cost_inr / exchange_rate
        markup = procurement_data.markup_percentage or 20.0  # Default markup
        selling_price = cost_usd * (1 + markup / 100)

        # 3. Create the Saree object
        saree_id = uuid.uuid4()
        saree = Saree(
            id=saree_id,
            name=procurement_data.saree_name,
            description=procurement_data.saree_description,
            procurement_cost_inr=procurement_data.procurement_cost_inr,
            markup_percentage=markup,
            selling_price_usd=round(selling_price, 2),
            image_urls=[]
        )

        # 4. Create the ProcurementRecord object
        procurement_record = ProcurementRecord(
            id=uuid.uuid4(),
            saree_id=saree_id,
            procured_by_user_id=user_id,
            cost_inr=procurement_data.procurement_cost_inr,
            inr_to_usd_exchange_rate=exchange_rate,
            procurement_date=datetime.now(timezone.utc)
        )

        # 5. Save to DynamoDB
        self.saree_service.table.put_item(Item=saree.model_dump(mode='json'))
        self.procurement_record_service.table.put_item(Item=procurement_record.model_dump(mode='json'))

        return saree 

    def _calculate_usd_selling_price(
        self, cad_price: float, exchange_rate: float, markup: float
    ) -> float:
        # Implementation of _calculate_usd_selling_price method
        cad_selling_price = cad_price * (1 + markup / 100)
        return cad_selling_price * exchange_rate 