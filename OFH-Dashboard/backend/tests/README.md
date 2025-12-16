# Backend Tests

This directory contains tests for the OFH Dashboard Backend.

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test File
```bash
pytest tests/test_health.py
```

### With Coverage
```bash
pytest --cov=. --cov-report=html
```

### Specific Markers
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Structure

- `test_*.py` - Test files
- `conftest.py` - Pytest configuration and fixtures
- `__init__.py` - Package initialization

## Writing Tests

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    """Unit test"""
    pass

@pytest.mark.integration
@pytest.mark.requires_db
def test_database_operation():
    """Integration test requiring database"""
    pass
```

## Test Fixtures

Available fixtures (defined in `conftest.py`):
- `app` - Flask application instance
- `client` - Test client for making requests
- `runner` - CLI test runner
- `reset_db` - Database reset fixture (runs before each test)

