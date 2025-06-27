from typing import Optional
from src.services.dynamodb import DynamoDBService


class SareeService(DynamoDBService):
    def __init__(self, endpoint_url: Optional[str] = None):
        super().__init__(table_name="sarees", endpoint_url=endpoint_url)

    def list_sarees(self) -> list[dict]:
        """
        Scans and retrieves all sarees from the DynamoDB table.
        NOTE: A scan operation can be inefficient on large tables. For a production
        system, this would be replaced with a more sophisticated query pattern.
        """
        response = self.table.scan()
        return response.get('Items', [])

    def get_saree_by_id(self, saree_id: str) -> Optional[dict]:
        """
        Retrieves a single saree from the DynamoDB table by its ID.
        """
        response = self.table.get_item(Key={'id': saree_id})
        return response.get('Item') 