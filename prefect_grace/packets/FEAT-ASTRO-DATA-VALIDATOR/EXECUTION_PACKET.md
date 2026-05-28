# Execution Packet: FEAT-ASTRO-DATA-VALIDATOR-W01-SCHEMA-VALIDATION

## Objective

Implement a flexible data validation framework with schema definitions and custom validators.
This packet creates a validation system for structured data with type checking, constraints, and error reporting.

## Slice

- slice_id: `SLICE-ASTRO-DATA-VALIDATOR`
- slice_slug: `astro-data-validator`
- feature_id: `FEAT-ASTRO-DATA-VALIDATOR`
- packet_id: `FEAT-ASTRO-DATA-VALIDATOR-W01-SCHEMA-VALIDATION`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-ASTRO-VALIDATION-MVP`
- depends_on: ``
- feature_dir: `prefect_grace/packets/FEAT-ASTRO-DATA-VALIDATOR`

## Source Of Truth

- `backend/app/validation/schema.py` (will be created)
- `backend/app/validation/validators.py` (will be created)
- `backend/app/validation/errors.py` (will be created)
- `backend/tests/test_validation.py` (will be created)

## Impacted Modules

- `M-ASTRO-BACKEND-VALIDATION`
- `M-ASTRO-BACKEND-TESTS`

## Allowed Write Scope

- `backend/app/validation/schema.py`
- `backend/app/validation/validators.py`
- `backend/app/validation/errors.py`
- `backend/app/validation/__init__.py`
- `backend/tests/test_validation.py`
- `prefect_grace/packets/FEAT-ASTRO-DATA-VALIDATOR/**`

## Frozen Scope

- `frontend/**`
- `scripts/pipeline.py`
- `prefect_grace/platform/**`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/**`
- `backend/app/api/**`
- `backend/app/models/**`
- `backend/app/cache/**`

## Must Preserve

- No breaking changes to existing code
- All tests must pass
- Clear error messages for validation failures
- Extensible validator system
- No external dependencies beyond standard library

## Recommended Role Assignment

- coder: `Codex high`; complex validation logic and error handling
- verifier: `Codex high`; comprehensive edge case testing
- reviewer: `Codex high`; API design and extensibility review
- rework policy: standard resume for validation logic issues

## Required Design Decisions

### 1. Validation Errors

Create `backend/app/validation/errors.py`:

- `ValidationError(Exception)` - base validation error
  - `field: str` - field name that failed
  - `message: str` - error description
  - `value: Any` - invalid value
- `ValidationResult` - dataclass with:
  - `valid: bool` - overall validation status
  - `errors: list[ValidationError]` - list of validation errors
  - `add_error(field, message, value)` - helper method

### 2. Built-in Validators

Create `backend/app/validation/validators.py` with validator functions:

- `required(value: Any) -> bool` - check value is not None/empty
- `type_check(value: Any, expected_type: type) -> bool` - verify type
- `min_length(value: str, length: int) -> bool` - minimum string length
- `max_length(value: str, length: int) -> bool` - maximum string length
- `min_value(value: int | float, minimum: int | float) -> bool` - minimum numeric value
- `max_value(value: int | float, maximum: int | float) -> bool` - maximum numeric value
- `regex_match(value: str, pattern: str) -> bool` - regex pattern matching
- `email_format(value: str) -> bool` - validate email format
- `url_format(value: str) -> bool` - validate URL format
- `in_choices(value: Any, choices: list) -> bool` - value in allowed list

### 3. Schema Definition

Create `backend/app/validation/schema.py` with Schema class:

- `Field` - dataclass defining field validation rules:
  - `name: str` - field name
  - `required: bool = True` - is field required
  - `field_type: type | None = None` - expected type
  - `validators: list[tuple[callable, dict]] = []` - list of (validator_func, kwargs)
  - `default: Any = None` - default value if missing
- `Schema` - class for defining validation schemas:
  - `__init__(fields: list[Field])` - initialize with field definitions
  - `validate(data: dict) -> ValidationResult` - validate data against schema
  - `add_field(field: Field)` - add field to schema
  - `get_field(name: str) -> Field | None` - get field definition

### 4. Validation Flow

1. Check required fields present
2. Check field types match
3. Run custom validators for each field
4. Collect all errors (don't stop at first error)
5. Return ValidationResult with all errors

### 5. Test Coverage

Create `backend/tests/test_validation.py`:

- Test each built-in validator individually
- Test required field validation
- Test type checking
- Test multiple validators on single field
- Test schema validation with valid data
- Test schema validation with invalid data (multiple errors)
- Test default values
- Test custom validator integration
- Test edge cases (None, empty strings, special chars)
- Test complex nested validation scenarios

## Implementation Requirements

1. Create ValidationError and ValidationResult classes
2. Implement all 10 built-in validators
3. Create Field and Schema classes
4. Implement comprehensive validation logic
5. Add detailed error messages
6. Create extensive test suite (15+ test cases)
7. Use Python type hints throughout
8. Follow PEP 8 style guidelines

## Acceptance Criteria

- All 10 built-in validators implemented
- Schema validation working with multiple fields
- ValidationResult collects all errors (not just first)
- Clear, descriptive error messages
- All tests pass (minimum 15 test cases)
- Support for custom validators
- No external dependencies added
- Extensible design for future validators

## Verification

Run unit tests:

```bash
cd /opt/astro-project/backend
python -m pytest tests/test_validation.py -v
```

Run linting:

```bash
cd /opt/astro-project/backend
python -m pylint app/validation/schema.py app/validation/validators.py app/validation/errors.py
```

Test example usage:

```python
from backend.app.validation.schema import Schema, Field
from backend.app.validation.validators import required, email_format, min_length

schema = Schema([
    Field("username", required=True, field_type=str, validators=[(min_length, {"length": 3})]),
    Field("email", required=True, field_type=str, validators=[(email_format, {})]),
])

result = schema.validate({"username": "ab", "email": "invalid"})
assert not result.valid
assert len(result.errors) == 2
```

## Expected Evidence

- Test output showing all tests passed (minimum 15 tests)
- Linting output showing no critical errors
- Example usage demonstrating validation
- Error message quality verification

## Escalation Triggers

- Validators produce incorrect results
- Error messages unclear or missing
- Tests fail
- Performance issues with large datasets
- Linting shows critical errors
