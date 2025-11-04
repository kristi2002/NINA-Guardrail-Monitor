# SQLAlchemy Model Best Practices

## Critical Rule: Never Use SQLAlchemy Columns in Boolean Contexts

SQLAlchemy `Column` objects cannot be used directly in boolean contexts (like `if column:`). Always use explicit `is not None` checks.

### ❌ WRONG - Causes Type Errors
```python
if self.created_at:
    # This will fail type checking
    pass

if self.confidence_score and self.confidence_score >= 0.8:
    # This will fail type checking
    pass
```

### ✅ CORRECT - Permanent Solution
```python
# For nullable columns
if self.created_at is not None:
    # Safe and correct
    pass

# For nullable numeric columns with comparisons
if self.confidence_score is not None and self.confidence_score >= 0.8:
    # Safe and correct
    pass

# For extracting values before comparisons
confidence_val: float = float(self.confidence_score) if self.confidence_score is not None else 0.0  # type: ignore
if confidence_val >= 0.8:
    # Safe and correct
    pass
```

## Pattern for Column Comparisons

### Pattern 1: Simple Null Check
```python
# Before
if self.some_column:

# After
if self.some_column is not None:
```

### Pattern 2: Null Check with Comparison
```python
# Before
if self.score and self.score >= 0.8:

# After
if self.score is not None and self.score >= 0.8:
```

### Pattern 3: Multiple Column Checks
```python
# Before
if self.start_time and self.end_time:

# After
if self.start_time is not None and self.end_time is not None:
```

### Pattern 4: Value Extraction for Complex Logic
```python
# Before
if self.severity in ['HIGH', 'CRITICAL'] and self.confidence_score >= 0.8:

# After
severity_val: str = str(self.severity) if self.severity is not None else ''  # type: ignore
confidence_val: float = float(self.confidence_score) if self.confidence_score is not None else 0.0  # type: ignore

if severity_val in ['HIGH', 'CRITICAL'] and confidence_val >= 0.8:
    # Safe and correct
    pass
```

### Pattern 5: DateTime/JSON Column Checks
```python
# Before
if self.details and isinstance(self.details, dict):

# After
if self.details is not None and isinstance(self.details, dict):

# Before
if self.last_login:

# After
if self.last_login is not None:
```

## Why This Matters

- **Type Safety**: SQLAlchemy Columns return `Never` from `__bool__()`, not `bool`
- **Runtime Safety**: Prevents unexpected behavior with SQLAlchemy's query builder
- **IDE Support**: Allows proper type checking and autocomplete
- **Code Clarity**: Makes null handling explicit and intentional

## All Fixed Models

The following models have been permanently fixed:
- ✅ `guardrail_event.py` - All boolean checks fixed
- ✅ `chat_message.py` - All boolean checks fixed
- ✅ `conversation.py` - All boolean checks fixed
- ✅ `operator_action.py` - All boolean checks fixed
- ✅ `user.py` - All boolean checks fixed

## Future Development

When adding new model methods:
1. Always use `is not None` for nullable column checks
2. Extract values to typed variables before complex comparisons
3. Use `# type: ignore` comments when necessary for type checker
4. Test with actual model instances to verify runtime behavior

