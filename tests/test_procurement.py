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
    """An authenticated user should be able to create a procurement."""
    # 1. Register a user
    client.post("/users/register", json={"email": "test@example.com", "password": "password", "role": "staff"})

    # 2. Get a token
    token_response = client.post("/token", data={"username": "test@example.com", "password": "password"})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create the procurement
    procurement_data = {
        "saree_name": "A beautiful saree",
        "saree_description": "From the finest silk.",
        "procurement_cost_inr": 150.0,
        "markup_percentage": 25.0,
    }
    proc_response = client.post("/procurements/", headers=headers, json=procurement_data)

    # 4. Assert the creation was successful
    assert proc_response.status_code == status.HTTP_201_CREATED
    saree_data = proc_response.json()
    assert saree_data["name"] == "A beautiful saree"

    # 5. Assert that the created saree now appears in the public list
    list_response = client.get("/sarees/")
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == "A beautiful saree" 