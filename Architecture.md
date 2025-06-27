# Couture Bookkeeping System - Technical Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Application Architecture](#application-architecture)
4. [Data Models & Database Design](#data-models--database-design)
5. [Authentication & Authorization](#authentication--authorization)
6. [API Design](#api-design)
7. [Business Logic](#business-logic)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Architecture](#deployment-architecture)
10. [Security Considerations](#security-considerations)
11. [Performance & Scalability](#performance--scalability)
12. [Future Enhancements](#future-enhancements)

## System Overview

The Couture Bookkeeping System is a FastAPI-based REST API designed to manage the complete business operations of a Mysore silk saree import/retail business. The system handles the flow from procurement in Bangalore, India to sales in the USA, with comprehensive expense management and role-based access control.

### Business Flow
```
Bangalore (Procurement) → Currency Conversion → Markup Application → USA (Sales)
                    ↓
            Expense Management & Approval Workflow
```

### Core Business Entities
- **Users**: Staff and managers with role-based permissions
- **Sarees**: Product catalog with procurement and selling prices
- **Procurement Records**: Purchase history with exchange rates
- **Expenses**: Submission and approval workflow

## Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management using Python type annotations
- **Uvicorn**: ASGI server for running FastAPI applications

### Database
- **Amazon DynamoDB**: NoSQL database for production
- **DynamoDB Local**: Local development environment
- **boto3**: AWS SDK for Python

### Authentication & Security
- **JWT (JSON Web Tokens)**: Stateless authentication
- **python-jose**: JWT implementation for Python
- **passlib**: Password hashing library
- **bcrypt**: Secure password hashing algorithm

### Development Tools
- **pytest**: Testing framework
- **ruff**: Fast Python linter
- **pyright**: Static type checker
- **uv**: Fast Python package installer and resolver

### Infrastructure
- **Docker**: Containerization for local development
- **Docker Compose**: Multi-container orchestration
- **AWS CDK**: Infrastructure as Code (planned)

## Application Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│           API Layer                 │
│     (FastAPI Routers)              │
├─────────────────────────────────────┤
│         Business Logic Layer        │
│         (Service Classes)           │
├─────────────────────────────────────┤
│          Data Access Layer          │
│       (DynamoDB Services)           │
├─────────────────────────────────────┤
│         Database Layer              │
│         (DynamoDB)                  │
└─────────────────────────────────────┘
```

### Directory Structure

```
src/
├── main.py                 # Application entry point & router registration
├── models.py               # Pydantic data models
├── dependencies.py         # Dependency injection configuration
├── security.py             # Authentication & authorization utilities
├── routers/                # API endpoint handlers
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management endpoints
│   ├── procurement.py     # Procurement endpoints
│   ├── sarees.py          # Saree catalog endpoints
│   └── expenses.py        # Expense management endpoints
└── services/               # Business logic layer
    ├── dynamodb.py        # Base DynamoDB service
    ├── user_service.py    # User business logic
    ├── procurement_service.py  # Procurement business logic
    ├── saree_service.py   # Saree catalog business logic
    └── expense_service.py # Expense management business logic
```

### Dependency Injection Pattern

The application uses FastAPI's dependency injection system for:
- **Service Layer Injection**: Clean separation between API and business logic
- **Authentication**: Centralized user authentication and role checking
- **Database Connections**: Configurable database service injection
- **Testing**: Easy mocking of services for unit tests

Example:
```python
@router.post("/expenses/")
def create_expense(
    expense_data: ExpenseCreate,
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    return expense_service.create_expense(expense_data, current_user)
```

## Data Models & Database Design

### Pydantic Models

The system uses Pydantic for data validation and serialization:

```python
# Base models for data validation
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.staff

# Create models for API input
class UserCreate(UserBase):
    password: str

# Full models for API output
class User(UserBase):
    id: uuid.UUID
    hashed_password: str
```

### DynamoDB Schema Design

#### Users Table
```
Primary Key: id (UUID)
Global Secondary Index: email-index
Attributes:
- id: String (UUID)
- email: String (unique)
- full_name: String
- role: String (manager|staff)
- hashed_password: String
```

#### Sarees Table
```
Primary Key: id (UUID)
Attributes:
- id: String (UUID)
- name: String
- description: String
- procurement_cost_inr: Number
- markup_percentage: Number
- selling_price_usd: Number
- image_urls: List[String]
```

#### Procurement Records Table
```
Primary Key: id (UUID)
Attributes:
- id: String (UUID)
- saree_id: String (UUID)
- procured_by_user_id: String (UUID)
- cost_inr: Number
- inr_to_usd_exchange_rate: Number
- procurement_date: String (ISO datetime)
```

#### Expenses Table
```
Primary Key: id (UUID)
Attributes:
- id: String (UUID)
- submitted_by_user_id: String (UUID)
- description: String
- amount: Number
- currency: String
- status: String (pending|approved|rejected)
- submission_date: String (ISO datetime)
- reviewed_by_user_id: String (UUID, optional)
- review_date: String (ISO datetime, optional)
```

### Data Relationships

```
User (1) ──────── (N) Procurement Records
  │                        │
  │                        │
  └── (N) Expenses         └── (1) Saree
```

## Authentication & Authorization

### JWT-Based Authentication

1. **User Registration**: Password hashing with bcrypt
2. **Login**: Credential verification and JWT token generation
3. **Token Validation**: Middleware extracts and validates JWT tokens
4. **Role-Based Access**: Decorators enforce role requirements

### Authentication Flow

```
Client                    API Server                   Database
  │                          │                          │
  ├── POST /token           ──┤                          │
  │   (username/password)     │                          │
  │                          ├── Verify credentials   ──┤
  │                          │                          │
  │                          ├── Generate JWT token     │
  │   ← JWT token           ──┤                          │
  │                          │                          │
  ├── API Request           ──┤                          │
  │   (Authorization header)  │                          │
  │                          ├── Validate JWT           │
  │                          ├── Extract user info      │
  │                          ├── Check permissions      │
  │   ← API Response        ──┤                          │
```

### Role-Based Access Control

- **Staff Role**: Can submit expenses and procurements
- **Manager Role**: All staff permissions + expense approval

Implementation:
```python
def require_manager_role(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.role != UserRole.manager:
        raise HTTPException(status_code=403, detail="Manager role required")
    return current_user
```

## API Design

### RESTful Principles

The API follows REST conventions:
- **Resource-based URLs**: `/users/`, `/expenses/`, `/sarees/`
- **HTTP Methods**: GET, POST, PATCH for appropriate operations
- **HTTP Status Codes**: 200, 201, 401, 403, 404, 422
- **JSON Payloads**: Consistent request/response format

### Endpoint Categories

#### Public Endpoints
- `GET /` - Health check
- `GET /sarees/` - Browse saree catalog
- `GET /sarees/{id}` - Individual saree details

#### Authentication Endpoints
- `POST /users/register` - User registration
- `POST /token` - Login and token generation

#### Protected Endpoints (Authenticated Users)
- `GET /users/me` - Current user profile
- `POST /procurements/` - Record procurement
- `POST /expenses/` - Submit expense

#### Manager-Only Endpoints
- `GET /expenses/` - List all expenses
- `PATCH /expenses/{id}/status` - Approve/reject expenses

### API Response Format

Consistent JSON structure:
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": "value2",
  "created_at": "2024-01-01T00:00:00Z"
}
```

Error responses:
```json
{
  "detail": "Descriptive error message"
}
```

## Business Logic

### Currency Conversion

The system handles INR to USD conversion for procurement:

```python
def calculate_selling_price(cost_inr: float, exchange_rate: float, markup: float) -> float:
    cost_usd = cost_inr / exchange_rate
    return cost_usd * (1 + markup / 100)
```

**Current Implementation**: Fixed exchange rate for testing
**Future Enhancement**: Real-time exchange rate API integration

### Markup Calculation

- **Global Default**: 20% markup if not specified
- **Per-Item Override**: Configurable markup per saree
- **Automatic Calculation**: USD selling price computed on procurement

### Expense Workflow

```
Staff Submits Expense → Pending Status → Manager Reviews → Approved/Rejected
```

State transitions:
- `pending` → `approved` (manager action)
- `pending` → `rejected` (manager action)
- No transitions from `approved` or `rejected` (immutable decisions)

## Testing Strategy

### Test Architecture

```
Test Layer                 Mock Layer                 Real Layer
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   API Tests     │  ──→  │  Mock Services  │  ──→  │  In-Memory DB   │
│                 │       │                 │       │                 │
│ - Authentication│       │ - MockUserSvc   │       │ - Python Dict   │
│ - Authorization │       │ - MockExpenseSvc│       │ - Test Isolation│
│ - Business Logic│       │ - MockSareeSvc  │       │ - Predictable   │
│ - Error Handling│       │ - MockProcSvc   │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### Test Categories

1. **Unit Tests**: Individual function testing
2. **Integration Tests**: API endpoint testing
3. **Authentication Tests**: Security validation
4. **Business Logic Tests**: Calculation verification
5. **Error Handling Tests**: Edge case coverage

### Mock Strategy

- **Dependency Injection**: FastAPI's override system
- **Isolated State**: Clean database between tests
- **Predictable Data**: Fixed exchange rates and timestamps
- **Comprehensive Coverage**: All business scenarios

### Test Data Management

```python
# Test isolation with automatic cleanup
@pytest.fixture(autouse=True)
def override_dependencies():
    # Clear all mock data before each test
    mock_db["users"].clear()
    mock_db["sarees"].clear()
    # ... setup mocks
    yield
    # Cleanup after test
```

## Deployment Architecture

### Local Development

```
Developer Machine
├── Python Virtual Environment (.venv)
├── Docker Compose
│   └── DynamoDB Local Container
├── FastAPI Application (uvicorn)
└── Test Suite (pytest)
```

### Production Architecture (Planned)

```
Internet
    │
    ▼
┌─────────────────┐
│  API Gateway    │  (Public URL, SSL termination)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  AWS Lambda     │  (Containerized FastAPI)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│   DynamoDB      │  (Managed NoSQL database)
└─────────────────┘
```

### Infrastructure as Code

AWS CDK will define:
- **Lambda Function**: Containerized FastAPI application
- **API Gateway**: HTTP API with CORS configuration
- **DynamoDB Tables**: With appropriate indexes and capacity
- **IAM Roles**: Least-privilege access policies
- **CloudWatch**: Logging and monitoring

## Security Considerations

### Authentication Security

- **Password Hashing**: bcrypt with salt rounds
- **JWT Tokens**: Short expiration times (configurable)
- **Token Validation**: Signature verification on every request
- **Role Enforcement**: Server-side permission checking

### API Security

- **Input Validation**: Pydantic models prevent injection
- **CORS Configuration**: Controlled cross-origin access
- **Rate Limiting**: (Planned) Request throttling
- **HTTPS Only**: TLS encryption in production

### Data Security

- **PII Protection**: Email addresses properly handled
- **Access Logging**: Audit trail for sensitive operations
- **Principle of Least Privilege**: Role-based data access
- **Data Encryption**: At rest (DynamoDB) and in transit (HTTPS)

## Performance & Scalability

### Current Performance Characteristics

- **Stateless Design**: Horizontal scaling capability
- **NoSQL Database**: High read/write performance
- **Efficient Queries**: Proper DynamoDB key design
- **Lightweight Framework**: FastAPI's high performance

### Scalability Considerations

1. **Database Scaling**: DynamoDB auto-scaling
2. **Application Scaling**: Lambda concurrent execution
3. **Caching Strategy**: (Future) Redis for frequent queries
4. **CDN Integration**: (Future) Static asset delivery

### Monitoring & Observability

Planned monitoring:
- **Application Metrics**: Request latency, error rates
- **Business Metrics**: Procurement volume, expense approval times
- **Infrastructure Metrics**: Lambda duration, DynamoDB consumption
- **Alerting**: Critical error notifications

## Future Enhancements

### Phase 2: File Upload & Storage

- **Image Upload**: Proof of purchase for procurements
- **S3 Integration**: Secure file storage
- **Image Processing**: Thumbnail generation, compression

### Phase 3: Advanced Business Features

- **Sales Recording**: Complete transaction tracking
- **Discount Management**: Promotional pricing
- **Inventory Management**: Stock level tracking
- **Reporting Dashboard**: Business analytics

### Phase 4: Integration & Automation

- **WhatsApp Business API**: Direct catalog integration
- **Real-time Exchange Rates**: Live currency conversion
- **Automated Workflows**: Approval notifications
- **Mobile Application**: React Native or Flutter frontend

### Phase 5: Advanced Analytics

- **Profit Analysis**: Margin calculations and trends
- **Demand Forecasting**: ML-based inventory planning
- **Customer Analytics**: Purchase pattern analysis
- **Transfer Pricing**: International tax compliance

## Conclusion

The Couture Bookkeeping System provides a solid foundation for managing a saree import/retail business with:

- **Clean Architecture**: Modular, testable, and maintainable code
- **Security First**: Role-based access and data protection
- **Scalable Design**: Ready for cloud deployment and growth
- **Business Focus**: Tailored to the specific needs of the saree business
- **Future Ready**: Extensible architecture for planned enhancements

The system successfully implements the core requirements from the original plan while maintaining flexibility for future iterations and enhancements.
