# Execution Packet: FEAT-ASTRO-USER-API-ENDPOINT-W01-USER-CRUD

## Objective

Implement a RESTful API endpoint for user management with CRUD operations.
This packet creates a complete user management API with validation, error handling, and tests.

## Slice

- slice_id: `SLICE-ASTRO-USER-API`
- slice_slug: `astro-user-api`
- feature_id: `FEAT-ASTRO-USER-API-ENDPOINT`
- packet_id: `FEAT-ASTRO-USER-API-ENDPOINT-W01-USER-CRUD`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-ASTRO-API-MVP`
- depends_on: ``
- feature_dir: `prefect_grace/packets/FEAT-ASTRO-USER-API-ENDPOINT`

## Source Of Truth

- `backend/app/api/users.py` (will be created)
- `backend/app/models/user.py` (will be created)
- `backend/tests/test_api_users.py` (will be created)

## Impacted Modules

- `M-ASTRO-BACKEND-API`
- `M-ASTRO-BACKEND-MODELS`
- `M-ASTRO-BACKEND-TESTS`

## Allowed Write Scope

- `backend/app/api/users.py`
- `backend/app/models/user.py`
- `backend/tests/test_api_users.py`
- `prefect_grace/packets/FEAT-ASTRO-USER-API-ENDPOINT/**`

## Frozen Scope

- `frontend/**`
- `scripts/pipeline.py`
- `prefect_grace/platform/**`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/**`
- `backend/app/utils/**`

## Must Preserve

- No breaking changes to existing code
- All tests must pass
- Follow REST API best practices
- Proper error handling and validation
- No external dependencies beyond standard library

## Recommended Role Assignment

- coder: `Codex high`; complex API with validation
- verifier: `Codex medium`; API and integration tests
- reviewer: `Codex high`; security and API design review
- rework policy: standard resume for validation issues

## Required Design Decisions

### 1. User Model

Create `backend/app/models/user.py` with User dataclass:

- `id: str` - unique user identifier (UUID)
- `username: str` - unique username (3-50 chars, alphanumeric + underscore)
- `email: str` - valid email address
- `created_at: datetime` - creation timestamp
- `is_active: bool` - account status

### 2. API Endpoints

Implement in `backend/app/api/users.py`:

- `POST /api/users` - Create new user (validate username, email)
- `GET /api/users/{user_id}` - Get user by ID
- `GET /api/users` - List all users (with optional ?active=true filter)
- `PUT /api/users/{user_id}` - Update user (email, is_active only)
- `DELETE /api/users/{user_id}` - Soft delete user (set is_active=False)

### 3. Validation Rules

- Username: 3-50 chars, alphanumeric + underscore, unique
- Email: valid email format, unique
- User ID: valid UUID format
- Return 400 for validation errors with descriptive messages
- Return 404 for non-existent users
- Return 409 for duplicate username/email

### 4. Test Coverage

Create `backend/tests/test_api_users.py`:

- Test successful user creation
- Test validation errors (invalid username, email)
- Test duplicate username/email handling
- Test get user by ID (success and 404)
- Test list users with and without filters
- Test update user (success and validation)
- Test delete user (soft delete)

## Implementation Requirements

1. Create User model with validation methods
2. Implement in-memory storage (dict) for users
3. Create all 5 API endpoints with proper error handling
4. Add comprehensive unit and integration tests
5. Use Python type hints throughout
6. Follow PEP 8 style guidelines

## Acceptance Criteria

- All 5 API endpoints implemented and working
- User model with validation
- All tests pass (minimum 10 test cases)
- Proper HTTP status codes (200, 201, 400, 404, 409)
- Input validation working correctly
- No external dependencies added

## Verification

Run unit tests:

```bash
cd /opt/astro-project/backend
python -m pytest tests/test_api_users.py -v
```

Run linting:

```bash
cd /opt/astro-project/backend
python -m pylint app/api/users.py app/models/user.py
```

## Expected Evidence

- Test output showing all tests passed (minimum 10 tests)
- Linting output showing no critical errors
- Manual verification of API endpoints
- Confirmation of proper error handling

## Escalation Triggers

- Tests fail
- Security vulnerabilities in validation
- Performance issues with user storage
- Linting shows critical errors
