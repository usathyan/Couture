from fastapi.testclient import TestClient
from src.main import app

# The conftest.py fixture now handles all mocking automatically.

client = TestClient(app)

def test_list_sarees_empty():
    """Test that listing sarees returns an empty list when none have been created."""
    response = client.get("/sarees/")
    assert response.status_code == 200
    assert response.json() == []

def test_list_and_get_sarees():
    """
    Test listing all sarees and retrieving a specific one after creating it via procurement.
    """
    user_email = "testsaree@example.com"
    user_password = "password123"
    client.post(
        "/users/register",
        json={"email": user_email, "full_name": "Test Saree", "password": user_password, "role": "staff"},
    )
    login_response = client.post(
        "/token", data={"username": user_email, "password": user_password}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit procurement (creates saree in pending status)
    proc_response = client.post(
        "/procurements/",
        headers=headers,
        json={
            "saree_name": "Paithani Silk",
            "saree_description": "Handwoven masterpiece",
            "procurement_cost_inr": 12000.0,
            "markup_percentage": 30.0,
        },
    )
    assert proc_response.status_code == 201
    procurement_data = proc_response.json()
    assert procurement_data["cost_inr"] == 12000.0
    assert procurement_data["status"] == "pending"
    saree_id = procurement_data["saree_id"]

    # Check that saree appears in the list
    list_response = client.get("/sarees/")
    assert list_response.status_code == 200
    sarees = list_response.json()
    assert len(sarees) == 1
    assert sarees[0]["name"] == "Paithani Silk"
    assert sarees[0]["procurement_status"] == "pending"
    assert sarees[0]["id"] == saree_id

    # Test getting the specific saree
    get_response = client.get(f"/sarees/{saree_id}")
    assert get_response.status_code == 200
    saree_detail = get_response.json()
    assert saree_detail["id"] == saree_id
    assert saree_detail["name"] == "Paithani Silk"

    # Test getting a non-existent saree
    get_fail_response = client.get("/sarees/non-existent-id")
    assert get_fail_response.status_code == 404 