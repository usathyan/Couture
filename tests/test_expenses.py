from fastapi.testclient import TestClient
from fastapi import status
from src.main import app

# The conftest.py fixture now handles all mocking automatically.

client = TestClient(app)

def test_expense_workflow():
    # 1. Create a staff user and a manager user
    staff_email = "staff@example.com"
    manager_email = "manager@example.com"
    password = "password"

    # Register staff
    client.post("/users/register", json={"email": staff_email, "password": password, "full_name": "Staff User", "role": "staff"})
    
    # Register manager
    client.post("/users/register", json={"email": manager_email, "password": password, "full_name": "Manager User", "role": "manager"})

    # Log in as staff
    staff_login_res = client.post("/token", data={"username": staff_email, "password": password})
    print("STAFF LOGIN RESPONSE:", staff_login_res.status_code, staff_login_res.json())
    staff_token = staff_login_res.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # Log in as manager
    manager_login_res = client.post("/token", data={"username": manager_email, "password": password})
    print("MANAGER LOGIN RESPONSE:", manager_login_res.status_code, manager_login_res.json())
    manager_token = manager_login_res.json()["access_token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    # 2. Staff user submits an expense
    expense_data = {"description": "Team Lunch", "amount": 120.50, "currency": "USD"}
    submit_res = client.post("/expenses/", json=expense_data, headers=staff_headers)
    assert submit_res.status_code == status.HTTP_201_CREATED
    expense = submit_res.json()
    expense_id = expense["id"]
    assert expense["description"] == expense_data["description"]
    assert expense["status"] == "pending"

    # 3. Staff user CANNOT list expenses
    list_res_staff = client.get("/expenses/", headers=staff_headers)
    assert list_res_staff.status_code == status.HTTP_403_FORBIDDEN

    # 4. Manager CAN list expenses
    list_res_manager = client.get("/expenses/", headers=manager_headers)
    assert list_res_manager.status_code == status.HTTP_200_OK
    assert len(list_res_manager.json()) > 0
    assert any(e["id"] == expense_id for e in list_res_manager.json())
    
    # 5. Staff user CANNOT approve the expense
    approve_res_staff = client.patch(f"/expenses/{expense_id}/status?status_update=approved", headers=staff_headers)
    assert approve_res_staff.status_code == status.HTTP_403_FORBIDDEN

    # 6. Manager CAN approve the expense
    approve_res_manager = client.patch(f"/expenses/{expense_id}/status?status_update=approved", headers=manager_headers)
    assert approve_res_manager.status_code == status.HTTP_200_OK
    updated_expense = approve_res_manager.json()
    assert updated_expense["status"] == "approved"
    assert updated_expense["id"] == expense_id
    assert updated_expense["reviewed_by_user_id"] is not None 