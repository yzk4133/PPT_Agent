# Memory Layer Tests

Comprehensive test suite for the three-tier hierarchical memory system.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
│   ├── test_models.py      # Data model tests
│   ├── test_l1_layer.py    # L1 Transient Memory tests
│   ├── test_l2_layer.py    # L2 Short-term Memory tests
│   ├── test_l3_layer.py    # L3 Long-term Memory tests
│   ├── test_promotion.py   # Promotion Engine tests
│   └── test_manager.py     # Memory Manager tests
├── integration/            # Integration tests
│   ├── test_layer_promotion.py       # Layer promotion integration
│   ├── test_scope_isolation.py       # Scope isolation tests
│   ├── test_concurrent_access.py     # Concurrent access tests
│   └── test_end_to_end.py            # End-to-end scenarios
├── services/               # Service layer tests (TODO)
│   └── test_*_service.py   # Individual service tests
└── fixtures/               # Test fixtures and utilities
    ├── memory_fixtures.py  # Mock objects and test data
    └── test_data.py        # Test data generators
```

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
pip install fakeredis
```

### Run All Tests

```bash
cd backend/memory/tests
pytest -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest unit/ -v

# Integration tests only
pytest integration/ -v

# Specific test file
pytest unit/test_l1_layer.py -v

# Specific test
pytest unit/test_l1_layer.py::TestL1TransientLayer::test_set_and_get -v
```

### Run with Coverage

```bash
# HTML coverage report
pytest --cov=backend.memory --cov-report=html

# Terminal coverage report
pytest --cov=backend.memory --cov-report=term-missing
```

### Run Specific Markers

```bash
# Skip slow tests
pytest -m "not slow" -v

# Only unit tests
pytest -m unit -v

# Only integration tests
pytest -m integration -v
```

## Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| **Models** | ≥ 90% |
| **L1 Layer** | ≥ 85% |
| **L2 Layer** | ≥ 80% |
| **L3 Layer** | ≥ 75% |
| **Promotion Engine** | ≥ 80% |
| **Manager** | ≥ 75% |
| **Overall** | ≥ 75% |

## Test Categories

### Unit Tests

Test individual components in isolation with mocked dependencies:

- **test_models.py**: Core data structures (MemoryMetadata, enums, PromotionTracker)
- **test_l1_layer.py**: L1 in-memory cache functionality
- **test_l2_layer.py**: L2 Redis layer with serialization
- **test_l3_layer.py**: L3 PostgreSQL layer with JSONB storage
- **test_promotion.py**: Promotion engine and rule evaluation
- **test_manager.py**: Hierarchical memory manager coordination

### Integration Tests

Test interactions between components:

- **test_layer_promotion.py**: Auto-promotion between layers (L1→L2→L3)
- **test_scope_isolation.py**: Scope isolation and data leakage prevention
- **test_concurrent_access.py**: Thread safety and concurrent operations
- **test_end_to_end.py**: Complete scenarios and workflows

### Service Tests

Test high-level business services:

- User preferences
- Shared workspace
- Vector memory
- Agent decisions
- Context optimization

## Key Test Scenarios

### 1. LRU Cache Behavior

```python
async def test_lru_eviction():
    layer = L1TransientLayer(capacity=3)
    # Fill capacity
    for i in range(3):
        await layer.set(f"key{i}", {"data": i}, scope, scope_id)
    # Add one more, should evict oldest
    await layer.set("key3", {"data": 3}, scope, scope_id)
    assert not await layer.exists("key0", scope, scope_id)
```

### 2. Scope Isolation

```python
async def test_scope_isolation():
    layer = L1TransientLayer()
    await layer.set("key", {"value": "task"}, MemoryScope.TASK, "task1")
    await layer.set("key", {"value": "session"}, MemoryScope.SESSION, "session1")
    # Both should coexist independently
    task_value = await layer.get("key", MemoryScope.TASK, "task1")
    session_value = await layer.get("key", MemoryScope.SESSION, "session1")
```

### 3. Auto-Promotion

```python
async def test_auto_promotion():
    # Write to L1
    await l1.set("key", {"data": "value"}, scope, scope_id)
    # Access 3 times to trigger promotion
    for _ in range(3):
        await l1.get("key", scope, scope_id)
    # Trigger promotion
    await engine.promote_l1_to_l2(l1, l2)
    # Verify in L2
    assert await l2.exists("key", scope, scope_id)
```

## Mock Strategy

- **L1 Layer**: Uses real LRUCache (in-memory, fast)
- **L2 Layer**: Uses `fakeredis` to mock Redis
- **L3 Layer**: Fully mocked using `unittest.mock.Mock`
- **Promotion Engine**: Uses custom configuration for faster tests

## Performance Benchmarks

Run performance tests with:

```bash
pytest -m slow -v
```

Performance targets:

| Operation | Target |
|-----------|--------|
| L1 read/write | < 1ms |
| L2 read/write | < 10ms |
| L3 read | < 50ms |
| L1→L2 promotion | 100 items / 5s |
| L2→L3 promotion | 50 items / 10s |

## Troubleshooting

### Tests Fail with Redis Error

```bash
# Ensure fakeredis is installed
pip install fakeredis
```

### Tests Fail with Import Errors

```bash
# Run from backend directory
cd backend
python -m pytest memory/tests/
```

### Async Tests Hang

Ensure you're using `pytest-asyncio` with correct configuration:

```ini
# pytest.ini
asyncio_mode = auto
```

## Contributing

When adding new features:

1. Write unit tests first
2. Ensure coverage ≥ 75%
3. Add integration tests for interactions
4. Update this README if needed

## License

Same as parent project.
