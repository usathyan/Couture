# Couture Bookkeeping API

A comprehensive bookkeeping system for a Mysore silk saree business that imports sarees from Bangalore, India and sells them in the USA via WhatsApp store.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Development Guide](#development-guide)
- [Frontend Integration Guide](#frontend-integration-guide)
- [Deployment](#deployment)

## Overview

This FastAPI-based backend system manages the complete lifecycle of a saree business:
- **User Management**: Role-based access control (Manager/Staff)
- **Procurement**: Recording saree purchases from Bangalore with INR costs
- **Inventory**: Managing saree catalog with automatic USD pricing
- **Expense Management**: Expense submission and approval workflow
- **Business Logic**: Automatic currency conversion and markup calculations

## Features

### ✅ Implemented Features

1. **User Management & Authentication**
   - User registration with 4-tier role system (staff/manager/partner/admin)
   - JWT-based authentication
   - Hierarchical role-based access control

2. **Procurement Module with Approval Workflow**
   - Staff submit procurement requests (pending status)
   - Manager+ approval workflow with cost override capabilities
   - Automatic currency conversion (INR → USD) after approval
   - Manager can add additional costs (transportation, handling, etc.)
   - Configurable markup percentages with override options
   - Image upload support for saree documentation
   - Procurement-related expense classification

3. **Saree Inventory**
   - List all available sarees with status tracking
   - Individual saree details with approval status
   - Public API for catalog browsing
   - Pending/Approved/Rejected status management

4. **Expense Management**
   - Staff can submit expenses with category classification
   - Managers can view and approve/reject expenses
   - Procurement-related expenses automatically created for additional costs
   - Complete audit trail with timestamps
   - Expense categories: general, procurement_related, marketing, operational

### 🚧 Planned Features (Future Iterations)

- File upload for proof of purchase
- Sales recording and tracking
- Discount management
- Advanced reporting and analytics
- Transfer pricing mechanisms
- Mobile app integration

## Architecture

The system follows a clean, modular architecture:

```
src/
├── main.py              # FastAPI application entry point
├── models.py            # Pydantic data models
├── dependencies.py      # Dependency injection setup
├── security.py          # Authentication & authorization
├── routers/             # API route handlers
│   ├── auth.py         # Authentication endpoints
│   ├── users.py        # User management
│   ├── procurement.py  # Procurement operations
│   ├── sarees.py       # Saree catalog
│   └── expenses.py     # Expense management
└── services/            # Business logic layer
    ├── dynamodb.py     # Database connection
    ├── user_service.py # User operations
    ├── procurement_service.py
    ├── saree_service.py
    └── expense_service.py
```

**Key Design Principles:**
- **Dependency Injection**: Clean separation of concerns
- **Role-Based Access Control**: Secure endpoint protection
- **Pydantic Models**: Type-safe data validation
- **Service Layer**: Business logic abstraction
- **Local-First Development**: DynamoDB Local for testing

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for DynamoDB Local)
- uv package manager

### Installation

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd couture
   uv venv --python 3.13
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

2. **Start DynamoDB Local:**
   ```bash
   docker-compose up -d dynamodb-local
   ```

3. **Create database tables:**
   ```bash
   python3 scripts/create_table.py
   ```

4. **Run the application:**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Using Makefile (Recommended)

```bash
make install    # Setup environment and dependencies
make run        # Start the application
make test       # Run all tests
make lint       # Run code quality checks
```

## API Documentation

### Authentication Flow

1. **Register a user:**
   ```bash
   # Register a manager
   curl -X POST "http://localhost:8000/users/register" \
        -H "Content-Type: application/json" \
        -d '{
          "email": "manager@example.com",
          "password": "securepassword",
          "full_name": "John Manager",
          "role": "manager"
        }'
   
   # Register a partner (can see across managers)
   curl -X POST "http://localhost:8000/users/register" \
        -H "Content-Type: application/json" \
        -d '{
          "email": "partner@example.com",
          "password": "securepassword",
          "full_name": "Jane Partner",
          "role": "partner"
        }'
   ```

2. **Get access token:**
   ```bash
   curl -X POST "http://localhost:8000/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=manager@example.com&password=securepassword"
   ```

3. **Use token in requests:**
   ```bash
   curl -X GET "http://localhost:8000/expenses/" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Core Endpoints

#### User Management
- `POST /users/register` - Register new user
- `GET /users/me` - Get current user profile

#### Procurement
- `POST /procurements/` - Submit procurement request for approval (authenticated)
- `GET /procurements/pending` - List pending procurement requests (manager+ only)
- `POST /procurements/{id}/approve` - Approve procurement with optional cost adjustments (manager+ only)
- `POST /procurements/{id}/reject` - Reject procurement request (manager+ only)
- `GET /procurements/` - List all procurement records (authenticated)
- `POST /procurements/legacy` - Legacy direct procurement (backward compatibility)

#### Saree Catalog
- `GET /sarees/` - List all sarees (public)
- `GET /sarees/{saree_id}` - Get specific saree details (public)

#### Expense Management
- `POST /expenses/` - Submit expense (any authenticated user)
- `GET /expenses/` - List all expenses (managers only)
- `PATCH /expenses/{expense_id}/status` - Approve/reject expense (managers only)

### Data Models

#### User Roles (Hierarchical)
- **staff**: Can submit expenses and procurement requests
- **manager**: Can approve/reject procurement requests and expenses + all staff permissions
- **partner**: Can see across all managers' procurements and expenses + all manager permissions
- **admin**: Full system access + all partner permissions

#### Procurement Data
```json
{
  "saree_name": "Mysore Silk Saree",
  "saree_description": "Traditional handwoven silk",
  "procurement_cost_inr": 15000.0,
  "markup_percentage": 25.0,
  "image_urls": ["https://example.com/saree1.jpg", "https://example.com/saree2.jpg"]
}
```

#### Procurement Approval Data
```json
{
  "additional_costs_inr": 500.0,
  "markup_override": 30.0,
  "exchange_rate_override": 0.013,
  "notes": "Approved with additional transportation costs"
}
```

#### Expense Data
```json
{
  "description": "Transportation costs",
  "amount": 150.0,
  "currency": "USD",
  "category": "procurement_related"
}
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_expenses.py

# Run with coverage
pytest --cov=src
```

### Test Structure

The test suite covers:

1. **Authentication & Authorization**
   - User registration and login
   - JWT token validation
   - Role-based access control

2. **Procurement Workflow**
   - Authenticated procurement creation
   - Automatic price calculation
   - Saree catalog integration

3. **Expense Management**
   - Expense submission by staff
   - Manager approval workflow
   - Status tracking and audit trail

4. **API Security**
   - Unauthorized access prevention
   - Input validation
   - Error handling

### Expected Test Results

All tests should pass with the following validations:

- **User Registration**: Creates user with correct role assignment
- **Authentication**: Generates valid JWT tokens
- **Procurement**: Creates sarees with calculated USD prices
- **Role Enforcement**: Managers can approve, staff cannot
- **Data Persistence**: Mock database maintains state correctly
- **API Responses**: Correct HTTP status codes and response formats

### Test Data & Assumptions

- **Exchange Rate**: Fixed at 83.50 INR/USD for test predictability
- **Default Markup**: 20% if not specified
- **Mock Services**: In-memory database for isolated testing
- **Test Isolation**: Clean state between each test run

## Development Guide

### For Backend Developers

#### Adding New Features

1. **Create Model** (in `src/models.py`):
   ```python
   class NewFeature(BaseModel):
       name: str
       value: float
   ```

2. **Create Service** (in `src/services/`):
   ```python
   class NewFeatureService(DynamoDBService):
       def create_feature(self, data):
           # Business logic here
           pass
   ```

3. **Add Router** (in `src/routers/`):
   ```python
   @router.post("/features/")
   def create_feature(
       feature: NewFeature,
       service: Annotated[NewFeatureService, Depends(get_new_feature_service)]
   ):
       return service.create_feature(feature)
   ```

4. **Add Tests** (in `tests/`):
   ```python
   def test_create_feature():
       response = client.post("/features/", json={"name": "test", "value": 100})
       assert response.status_code == 201
   ```

#### Code Quality Standards

- **Type Hints**: Use Pydantic models and Python type hints
- **Error Handling**: Proper HTTP status codes and error messages
- **Authentication**: Protect endpoints with `Depends(get_current_user)`
- **Validation**: Use Pydantic for input validation
- **Testing**: Write tests for all new functionality

#### Database Schema

The system uses DynamoDB with these tables:
- **users**: User accounts and roles
- **sarees**: Product catalog
- **procurement_records**: Purchase history
- **expenses**: Expense submissions and approvals

### For Frontend Developers

#### Authentication Integration

1. **Login Flow**:
   ```javascript
   // Get token
   const response = await fetch('/token', {
     method: 'POST',
     headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
     body: 'username=user@example.com&password=password'
   });
   const { access_token } = await response.json();
   
   // Store token
   localStorage.setItem('token', access_token);
   ```

2. **Authenticated Requests**:
   ```javascript
   const token = localStorage.getItem('token');
   const response = await fetch('/expenses/', {
     headers: { 'Authorization': `Bearer ${token}` }
   });
   ```

#### API Response Formats

All endpoints return JSON with consistent structure:

**Success Response**:
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": "value2",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Response**:
```json
{
  "detail": "Error message describing what went wrong"
}
```

#### User Interface Considerations

1. **Role-Based UI**: Show/hide features based on user role
2. **Real-Time Updates**: Consider WebSocket for live expense approvals
3. **File Uploads**: Prepare for image upload in procurement
4. **Responsive Design**: Mobile-first for WhatsApp store integration
5. **Offline Support**: Consider PWA features for field procurement

#### State Management Recommendations

```javascript
// User state
const userState = {
  isAuthenticated: false,
  user: null,
  role: null
};

// Business data state
const businessState = {
  sarees: [],
  expenses: [],
  pendingExpenses: []
};
```

## Deployment

### Local Development
- Uses DynamoDB Local in Docker
- Environment variables in `.env` file
- Hot reload with uvicorn

### Production (Future)
- AWS CDK for infrastructure as code
- AWS Lambda for serverless hosting
- Amazon DynamoDB for production database
- Amazon S3 for file storage
- API Gateway for public access

### Environment Variables

```bash
# Local Development
DYNAMODB_ENDPOINT=http://localhost:8000
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
AWS_DEFAULT_REGION=us-east-1

# Production
DYNAMODB_ENDPOINT=  # Use default AWS DynamoDB
JWT_SECRET_KEY=your-secret-key
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license here]
