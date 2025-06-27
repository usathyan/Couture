from typing import Optional

from src.services.dynamodb import DynamoDBService


class UserService(DynamoDBService):
    def __init__(self, endpoint_url: Optional[str] = None):
        super().__init__(table_name="users", endpoint_url=endpoint_url)

    def create_user(self, user_data: dict) -> dict:
        """
        Creates a new user item in the DynamoDB table.
        :param user_data: A dictionary containing the user data.
        :return: The item that was created.
        """
        self.table.put_item(Item=user_data)
        return user_data

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Retrieves a user from the DynamoDB table by their email.
        We will need a Global Secondary Index (GSI) on the 'email' attribute for this to be efficient.
        :param email: The email of the user to retrieve.
        :return: The user item if found, otherwise None.
        """
        response = self.table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        items = response.get('Items', [])
        return items[0] if items else None 