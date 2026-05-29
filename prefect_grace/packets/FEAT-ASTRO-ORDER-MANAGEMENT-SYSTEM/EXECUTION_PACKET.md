# Execution Packet: FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM-W01-FULL-SYSTEM

## Objective

Implement a complete order management system with order models, API endpoints, state machine, and analytics.
This is a large feature designed to test the architect's ability to break down complex work into manageable tasks.

## Slice

- slice_id: `SLICE-ASTRO-ORDER-MANAGEMENT`
- slice_slug: `astro-order-management`
- feature_id: `FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM`
- packet_id: `FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM-W01-FULL-SYSTEM`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-ASTRO-BACKEND-MVP`
- depends_on: ``
- feature_dir: `prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM`

## Source Of Truth

- `backend/app/models/order.py` (will be created)
- `backend/app/models/order_item.py` (will be created)
- `backend/app/api/orders.py` (will be created)
- `backend/app/services/order_service.py` (will be created)
- `backend/app/services/order_analytics.py` (will be created)
- `backend/tests/test_order_model.py` (will be created)
- `backend/tests/test_order_api.py` (will be created)
- `backend/tests/test_order_service.py` (will be created)
- `backend/tests/test_order_analytics.py` (will be created)

## Impacted Modules

- `M-ASTRO-BACKEND-MODELS`
- `M-ASTRO-BACKEND-API`
- `M-ASTRO-BACKEND-SERVICES`
- `M-ASTRO-BACKEND-TESTS`

## Allowed Write Scope

- `backend/app/models/order.py`
- `backend/app/models/order_item.py`
- `backend/app/api/orders.py`
- `backend/app/services/order_service.py`
- `backend/app/services/order_analytics.py`
- `backend/tests/test_order_model.py`
- `backend/tests/test_order_api.py`
- `backend/tests/test_order_service.py`
- `backend/tests/test_order_analytics.py`
- `prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM/**`

## Frozen Scope

- `frontend/**`
- `scripts/pipeline.py`
- `prefect_grace/platform/**`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/**`
- `backend/app/config/**`
- `backend/app/database/**`

## Must Preserve

- All existing API endpoints must continue working
- No breaking changes to existing models
- All tests must pass
- Thread-safe operations for in-memory storage
- No external dependencies beyond FastAPI and Pydantic

## Recommended Role Assignment

- coder: `Codex high`; complex state machine and multiple components
- verifier: `Codex high`; comprehensive testing of state transitions and analytics
- reviewer: `Codex high`; architecture and API design review
- rework policy: standard resume for validation or state machine issues

## Required Design Decisions

### 1. Order Model

Create `backend/app/models/order.py`:

- `id: str` - UUID order identifier
- `customer_id: str` - customer identifier
- `items: list[OrderItem]` - list of order items
- `total_amount: float` - total order amount (calculated from items)
- `status: OrderStatus` - order status enum
- `created_at: datetime` - creation timestamp
- `updated_at: datetime` - last update timestamp
- OrderStatus enum: pending, confirmed, processing, shipped, delivered, cancelled
- Validation: minimum 1 item, positive amounts, valid status transitions

### 2. OrderItem Model

Create `backend/app/models/order_item.py`:

- `product_id: str` - product identifier
- `quantity: int` - item quantity (positive integer)
- `unit_price: float` - price per unit (positive)
- `subtotal: float` - calculated as quantity * unit_price
- Automatic subtotal calculation
- Validation: positive quantity and unit_price

### 3. Order Service

Create `backend/app/services/order_service.py`:

- In-memory order storage (dict)
- CRUD operations: create, get, list, update, delete
- Status transition validation (state machine)
- Order confirmation logic
- Order shipping logic
- Order cancellation logic
- Thread-safe operations using threading.Lock

### 4. Order API Endpoints

Create `backend/app/api/orders.py` with FastAPI router:

- `POST /api/orders` - Create new order (201)
- `GET /api/orders/{order_id}` - Get order by ID (200/404)
- `GET /api/orders` - List orders with filters: status, customer_id (200)
- `PUT /api/orders/{order_id}` - Update order (200/404/400)
- `DELETE /api/orders/{order_id}` - Cancel order (200/404)
- `POST /api/orders/{order_id}/confirm` - Confirm order (200/404/400)
- `POST /api/orders/{order_id}/ship` - Mark as shipped (200/404/400)
- Proper error handling with appropriate status codes
- Input validation using Pydantic models

### 5. Order Analytics

Create `backend/app/services/order_analytics.py`:

- `GET /api/orders/analytics/summary` - Total orders, revenue, average order value
- `GET /api/orders/analytics/by-status` - Order count by status
- `GET /api/orders/analytics/top-customers` - Top 10 customers by order count
- Real-time calculations from in-memory storage

### 6. State Machine

Valid status transitions:
- pending → confirmed, cancelled
- confirmed → processing, cancelled
- processing → shipped, cancelled
- shipped → delivered
- delivered → (terminal state)
- cancelled → (terminal state)

### 7. Test Coverage

Create comprehensive test suite (minimum 25 tests):

`backend/tests/test_order_model.py`:
- Order creation and validation
- OrderItem calculations
- Status enum values

`backend/tests/test_order_service.py`:
- CRUD operations
- Status transitions (valid and invalid)
- Thread safety
- Edge cases

`backend/tests/test_order_api.py`:
- All API endpoints
- Success cases (200, 201)
- Error cases (400, 404, 409)
- Filtering and pagination
- Input validation

`backend/tests/test_order_analytics.py`:
- Summary calculations
- Status grouping
- Top customers ranking

## Acceptance Criteria

1. All 10+ API endpoints implemented and working
2. Order and OrderItem models with proper validation
3. State machine enforcing valid transitions
4. Order service with thread-safe operations
5. Analytics endpoints with correct calculations
6. All tests pass (minimum 25 test cases)
7. Proper HTTP status codes (200, 201, 400, 404, 409)
8. Input validation working correctly
9. No scope violations
10. No external dependencies added

## Expected Evidence

- `test_output` - Pytest output showing all 25+ tests passed
- `implementation_verification` - Manual verification of all components
- `api_verification` - Manual API endpoint testing with sample requests

## Verification

All 25+ tests must pass. All API endpoints must return correct status codes. Order state machine must enforce valid transitions. Analytics must calculate correct values. No scope violations.

## Escalation Triggers

- Scope violations detected
- Test coverage below 25 tests
- API endpoints returning incorrect status codes
- State machine allowing invalid transitions
- Analytics calculations incorrect
- Thread safety issues detected

## Architecture Notes

This is a large feature designed to test the architect's ability to break down complex work.
The architect should analyze the requirements and create a plan that sequences the implementation:

Suggested breakdown:
1. Order and OrderItem models with validation
2. Order service with in-memory storage and CRUD
3. Basic order API endpoints (CRUD)
4. State machine and status transition endpoints
5. Analytics service and endpoints
6. Comprehensive test suite

The architect should determine the optimal task decomposition and sequencing.
