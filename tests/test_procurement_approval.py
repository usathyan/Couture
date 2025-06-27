from fastapi.testclient import TestClient
from fastapi import status
from src.main import app

client = TestClient(app)

def test_procurement_approval_workflow():
    """Test the complete procurement approval workflow."""
    # 1. Register users with different roles
    client.post("/users/register", json={"email": "staff@example.com", "password": "password", "role": "staff"})
    client.post("/users/register", json={"email": "manager@example.com", "password": "password", "role": "manager"})
    client.post("/users/register", json={"email": "partner@example.com", "password": "password", "role": "partner"})
    client.post("/users/register", json={"email": "admin@example.com", "password": "password", "role": "admin"})

    # 2. Get tokens for each user
    staff_token = client.post("/token", data={"username": "staff@example.com", "password": "password"}).json()["access_token"]
    manager_token = client.post("/token", data={"username": "manager@example.com", "password": "password"}).json()["access_token"]
    partner_token = client.post("/token", data={"username": "partner@example.com", "password": "password"}).json()["access_token"]
    admin_token = client.post("/token", data={"username": "admin@example.com", "password": "password"}).json()["access_token"]

    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    partner_headers = {"Authorization": f"Bearer {partner_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Staff submits a procurement
    procurement_data = {
        "saree_name": "Elegant Saree",
        "saree_description": "Beautiful handwoven saree",
        "procurement_cost_inr": 5000.0,
        "markup_percentage": 25.0,
        "image_urls": ["https://example.com/image1.jpg"]
    }
    proc_response = client.post("/procurements/", headers=staff_headers, json=procurement_data)
    assert proc_response.status_code == status.HTTP_201_CREATED
    procurement = proc_response.json()
    procurement_id = procurement["id"]
    assert procurement["status"] == "pending"

    # 4. Test that staff cannot access pending procurements endpoint (manager+ only)
    pending_response = client.get("/procurements/pending", headers=staff_headers)
    assert pending_response.status_code == status.HTTP_403_FORBIDDEN

    # 5. Manager can see pending procurements
    pending_response = client.get("/procurements/pending", headers=manager_headers)
    assert pending_response.status_code == status.HTTP_200_OK
    pending_procurements = pending_response.json()["pending_procurements"]
    assert len(pending_procurements) == 1
    assert pending_procurements[0]["id"] == procurement_id

    # 6. Partner can also see pending procurements
    pending_response = client.get("/procurements/pending", headers=partner_headers)
    assert pending_response.status_code == status.HTTP_200_OK
    pending_procurements = pending_response.json()["pending_procurements"]
    assert len(pending_procurements) == 1

    # 7. Admin can also see pending procurements
    pending_response = client.get("/procurements/pending", headers=admin_headers)
    assert pending_response.status_code == status.HTTP_200_OK
    pending_procurements = pending_response.json()["pending_procurements"]
    assert len(pending_procurements) == 1

    # 8. Manager approves procurement with additional costs
    approval_data = {
        "additional_costs_inr": 500.0,  # Additional transportation costs
        "markup_override": 30.0,  # Override markup to 30%
        "exchange_rate_override": 0.013,  # Custom exchange rate
        "notes": "Approved with additional transportation costs"
    }
    approve_response = client.post(f"/procurements/{procurement_id}/approve", 
                                   headers=manager_headers, json=approval_data)
    assert approve_response.status_code == status.HTTP_200_OK
    approved_procurement = approve_response.json()
    assert approved_procurement["status"] == "approved"
    assert approved_procurement["manager_additional_costs_inr"] == 500.0
    assert approved_procurement["manager_markup_override"] == 30.0

    # 9. Check that saree is now approved and has selling price
    sarees_response = client.get("/sarees/")
    assert sarees_response.status_code == status.HTTP_200_OK
    sarees = sarees_response.json()
    assert len(sarees) == 1
    saree = sarees[0]
    assert saree["procurement_status"] == "approved"
    assert saree["selling_price_usd"] is not None
    assert saree["selling_price_usd"] > 0

    # 10. Check that no more pending procurements exist
    pending_response = client.get("/procurements/pending", headers=manager_headers)
    assert pending_response.status_code == status.HTTP_200_OK
    assert len(pending_response.json()["pending_procurements"]) == 0


def test_procurement_rejection_workflow():
    """Test procurement rejection workflow."""
    # 1. Register users
    client.post("/users/register", json={"email": "staff2@example.com", "password": "password", "role": "staff"})
    client.post("/users/register", json={"email": "manager2@example.com", "password": "password", "role": "manager"})

    # 2. Get tokens
    staff_token = client.post("/token", data={"username": "staff2@example.com", "password": "password"}).json()["access_token"]
    manager_token = client.post("/token", data={"username": "manager2@example.com", "password": "password"}).json()["access_token"]

    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    # 3. Staff submits a procurement
    procurement_data = {
        "saree_name": "Rejected Saree",
        "saree_description": "This will be rejected",
        "procurement_cost_inr": 10000.0,
        "markup_percentage": 50.0,
    }
    proc_response = client.post("/procurements/", headers=staff_headers, json=procurement_data)
    assert proc_response.status_code == status.HTTP_201_CREATED
    procurement = proc_response.json()
    procurement_id = procurement["id"]

    # 4. Manager rejects procurement
    reject_response = client.post(f"/procurements/{procurement_id}/reject", 
                                  headers=manager_headers, 
                                  params={"rejection_reason": "Cost too high"})
    assert reject_response.status_code == status.HTTP_200_OK
    rejected_procurement = reject_response.json()
    assert rejected_procurement["status"] == "rejected"

    # 5. Check that saree is now rejected
    sarees_response = client.get("/sarees/")
    assert sarees_response.status_code == status.HTTP_200_OK
    sarees = sarees_response.json()
    # Find the rejected saree
    rejected_saree = next((s for s in sarees if s["name"] == "Rejected Saree"), None)
    assert rejected_saree is not None
    assert rejected_saree["procurement_status"] == "rejected"
    assert rejected_saree["selling_price_usd"] is None


def test_role_based_access_control():
    """Test that role-based access control works correctly."""
    # Register users with different roles
    client.post("/users/register", json={"email": "staff3@example.com", "password": "password", "role": "staff"})
    client.post("/users/register", json={"email": "manager3@example.com", "password": "password", "role": "manager"})
    client.post("/users/register", json={"email": "partner3@example.com", "password": "password", "role": "partner"})
    client.post("/users/register", json={"email": "admin3@example.com", "password": "password", "role": "admin"})

    # Get tokens
    staff_token = client.post("/token", data={"username": "staff3@example.com", "password": "password"}).json()["access_token"]
    manager_token = client.post("/token", data={"username": "manager3@example.com", "password": "password"}).json()["access_token"]
    partner_token = client.post("/token", data={"username": "partner3@example.com", "password": "password"}).json()["access_token"]
    admin_token = client.post("/token", data={"username": "admin3@example.com", "password": "password"}).json()["access_token"]

    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    partner_headers = {"Authorization": f"Bearer {partner_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Test pending procurements access
    # Staff should be denied
    response = client.get("/procurements/pending", headers=staff_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Manager, Partner, and Admin should have access
    for headers in [manager_headers, partner_headers, admin_headers]:
        response = client.get("/procurements/pending", headers=headers)
        assert response.status_code == status.HTTP_200_OK

    # Create a test procurement to test approval/rejection access
    procurement_data = {
        "saree_name": "Test Access Saree",
        "saree_description": "Testing access control",
        "procurement_cost_inr": 3000.0,
    }
    proc_response = client.post("/procurements/", headers=staff_headers, json=procurement_data)
    procurement_id = proc_response.json()["id"]

    # Test approval access
    approval_data = {"additional_costs_inr": 100.0}
    
    # Staff should be denied
    response = client.post(f"/procurements/{procurement_id}/approve", headers=staff_headers, json=approval_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Manager, Partner, and Admin should have access
    # Test with manager (others would work the same way)
    response = client.post(f"/procurements/{procurement_id}/approve", headers=manager_headers, json=approval_data)
    assert response.status_code == status.HTTP_200_OK


def test_legacy_procurement_endpoint():
    """Test that the legacy procurement endpoint still works for backward compatibility."""
    # Register a user
    client.post("/users/register", json={"email": "legacy@example.com", "password": "password", "role": "staff"})
    
    # Get token
    token = client.post("/token", data={"username": "legacy@example.com", "password": "password"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Use legacy endpoint
    procurement_data = {
        "saree_name": "Legacy Saree",
        "saree_description": "Created via legacy endpoint",
        "procurement_cost_inr": 2000.0,
        "markup_percentage": 20.0,
    }
    response = client.post("/procurements/legacy", headers=headers, json=procurement_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    procurement = response.json()
    assert procurement["status"] == "approved"  # Legacy auto-approves
    assert procurement["final_selling_price_usd"] is not None

    # Check that saree was created and approved
    sarees_response = client.get("/sarees/")
    sarees = sarees_response.json()
    legacy_saree = next((s for s in sarees if s["name"] == "Legacy Saree"), None)
    assert legacy_saree is not None
    assert legacy_saree["procurement_status"] == "approved"
    assert legacy_saree["selling_price_usd"] is not None 