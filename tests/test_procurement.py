from fastapi.testclient import TestClient
from fastapi import status
from src.main import app

# The conftest.py fixture now handles all mocking automatically.

client = TestClient(app)

def test_create_procurement_unauthorized():
    """An unauthenticated user should not be able to create a procurement."""
    response = client.post("/procurements/", json={"saree_name": "test"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_procurement_authorized():
    """An authenticated user should be able to submit a procurement for approval."""
    # 1. Register a user
    client.post("/users/register", json={"email": "test@example.com", "password": "password", "role": "staff"})

    # 2. Get a token
    token_response = client.post("/token", data={"username": "test@example.com", "password": "password"})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Submit the procurement
    procurement_data = {
        "saree_name": "A beautiful saree",
        "saree_description": "From the finest silk.",
        "procurement_cost_inr": 150.0,
        "markup_percentage": 25.0,
    }
    proc_response = client.post("/procurements/", headers=headers, json=procurement_data)

    # 4. Assert the submission was successful
    assert proc_response.status_code == status.HTTP_201_CREATED
    procurement_data = proc_response.json()
    assert procurement_data["cost_inr"] == 150.0
    assert procurement_data["status"] == "pending"  # New procurements are pending approval

    # 5. Check that a saree was created in pending status
    list_response = client.get("/sarees/")
    assert list_response.status_code == status.HTTP_200_OK
    sarees = list_response.json()
    assert len(sarees) == 1
    assert sarees[0]["name"] == "A beautiful saree"
    assert sarees[0]["procurement_status"] == "pending" 