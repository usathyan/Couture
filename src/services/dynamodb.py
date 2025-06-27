import boto3
from botocore.exceptions import ClientError


class DynamoDBService:
    def __init__(self, table_name: str, region_name: str = "us-east-1", endpoint_url: str | None = None):
        """
        Initializes the DynamoDBService.

        :param table_name: Name of the DynamoDB table.
        :param region_name: AWS region.
        :param endpoint_url: The endpoint URL for DynamoDB. If None, uses the default AWS endpoint.
                             For local development, this should be 'http://localhost:8000'.
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=region_name,
            endpoint_url=endpoint_url
        )
        self.table = self.dynamodb.Table(self.table_name)

    def put_item(self, Item: dict):
        """Puts an item into the DynamoDB table."""
        try:
            self.table.put_item(Item=Item)
        except ClientError as e:
            error_message = e.response.get("Error", {}).get("Message", "Unknown error")
            print(f"Error putting item: {error_message}")
            raise

    def get_table(self):
        """Returns the DynamoDB table object."""
        return self.table

    def item_exists(self, key: dict) -> bool:
        """
        Checks if an item exists in the table.
        :param key: The primary key of the item.
        :return: True if the item exists, False otherwise.
        """
        try:
            response = self.table.get_item(Key=key)
            return 'Item' in response
        except ClientError as e:
            error_message = e.response.get("Error", {}).get("Message", "Unknown error")
            print(f"Error checking item existence: {error_message}")
            return False 