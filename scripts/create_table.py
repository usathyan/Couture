import boto3
from botocore.exceptions import ClientError
import time


def create_table(dynamodb_resource, table_name, key_schema, attr_definitions, gsis=None):
    """Generic function to create a DynamoDB table."""
    print(f"Attempting to create table: {table_name}")
    try:
        provisioned_throughput = {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        
        table_params = {
            'TableName': table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attr_definitions,
            'ProvisionedThroughput': provisioned_throughput
        }
        
        if gsis:
            for gsi in gsis:
                gsi['ProvisionedThroughput'] = provisioned_throughput
            table_params['GlobalSecondaryIndexes'] = gsis

        table = dynamodb_resource.create_table(**table_params)
        table.wait_until_exists()
        print(f"Table '{table_name}' created successfully.")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table '{table_name}' already exists.")
        else:
            raise e


def main():
    """Initializes DynamoDB tables."""
    # Give DynamoDB Local a moment to start up
    time.sleep(5)

    # When running locally, we need to provide dummy credentials and a region.
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url="http://localhost:8000",
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )

    # Users table
    create_table(
        dynamodb_resource=dynamodb,
        table_name='users',
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attr_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        gsis=[{
            'IndexName': 'email-index',
            'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )

    # Sarees table
    create_table(
        dynamodb_resource=dynamodb,
        table_name='sarees',
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attr_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
    )

    # Procurement Records table
    create_table(
        dynamodb_resource=dynamodb,
        table_name='procurement_records',
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attr_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
    )

    # Expenses table
    create_table(
        dynamodb_resource=dynamodb,
        table_name='expenses',
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attr_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
    )


if __name__ == '__main__':
    main() 