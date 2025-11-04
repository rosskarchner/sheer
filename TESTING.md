# Testing Sheer

This document describes how to run tests for Sheer, including both unit tests and integration tests.

## Prerequisites

- Python 3.8 or higher
- Docker (for integration tests)
- Docker Compose (for manual container management)

## Installation

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### All Tests

Run all tests (unit and integration):

```bash
pytest
```

### Unit Tests Only

Run only unit tests (no Docker required):

```bash
pytest -m "not integration"
```

### Integration Tests Only

Run only integration tests (requires Docker):

```bash
pytest -m integration
```

## Integration Tests

Integration tests spin up real Elasticsearch and OpenSearch containers using testcontainers. These tests verify that Sheer works correctly with actual search engines.

### What Integration Tests Cover

1. **Connection Tests**: Verify connectivity to ES/OpenSearch
2. **Index Creation**: Test index creation with settings
3. **Document Indexing**: Index test documents from processors
4. **Search Functionality**: Query documents with various search types
5. **Mappings**: Verify field mappings are correctly applied
6. **Document Retrieval**: Get documents by ID
7. **Aggregations**: Test aggregation queries
8. **Reindexing**: Test reindexing functionality
9. **Bool Queries**: Test modern bool query syntax
10. **Partial Indexing**: Test indexing specific processors

### Docker Requirements

Integration tests automatically manage containers using testcontainers. However, you can also manually start containers for testing:

```bash
# Start both Elasticsearch and OpenSearch
docker-compose -f docker-compose.test.yml up -d

# Stop containers
docker-compose -f docker-compose.test.yml down
```

When using docker-compose:
- Elasticsearch runs on port 9200
- OpenSearch runs on port 9201

### Running Integration Tests Against Local Containers

If you prefer to use docker-compose instead of testcontainers:

1. Start the containers:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

2. Wait for services to be ready (check health):
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

3. Run your tests manually or with custom fixtures pointing to localhost

## Test Coverage

Generate a coverage report:

```bash
pytest --cov=sheer --cov-report=html
```

View the HTML report:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Structure

```
tests/
├── integration/           # Integration tests with real ES/OpenSearch
│   ├── conftest.py       # Pytest fixtures for containers
│   ├── test_data/        # Test data for indexing
│   ├── test_elasticsearch_integration.py
│   └── test_opensearch_integration.py
└── ...                   # Unit tests in sheer/ directory
```

## Writing New Tests

### Unit Tests

Unit tests should use mocking and not require external services:

```python
import mock
from sheer.indexer import index_location

@mock.patch('sheer.indexer.Elasticsearch')
def test_something(mock_es):
    # Your test here
    pass
```

### Integration Tests

Integration tests should use the provided fixtures:

```python
import pytest

@pytest.mark.integration
class TestMyFeature:
    def test_with_elasticsearch(self, elasticsearch_container, test_data_dir):
        # elasticsearch_container provides connection info
        # test_data_dir provides path to test data
        pass
```

## Continuous Integration

Integration tests are designed to run in CI environments. The testcontainers library handles container lifecycle automatically.

### GitHub Actions Example

```yaml
- name: Run integration tests
  run: |
    pip install -r requirements-test.txt
    pytest -m integration
```

## Troubleshooting

### Docker Permission Issues

If you get permission errors with Docker:

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Port Conflicts

If ports 9200 or 9201 are in use:

```bash
# Find what's using the port
lsof -i :9200

# Stop existing Elasticsearch/OpenSearch
docker ps | grep elastic
docker stop <container_id>
```

### Container Startup Timeout

Integration tests wait up to 30 seconds for containers to start. If tests fail with timeout errors:

1. Check Docker is running: `docker ps`
2. Try pulling images manually: `docker pull docker.elastic.co/elasticsearch/elasticsearch:8.11.0`
3. Check Docker logs: `docker-compose -f docker-compose.test.yml logs`

### Memory Issues

Elasticsearch and OpenSearch need adequate memory. If containers crash:

1. Increase Docker memory limit (Docker Desktop settings)
2. Reduce JVM heap size in docker-compose.test.yml
3. Run tests one at a time instead of in parallel

## Test Data

Test data is located in `tests/integration/test_data/`:

- `_posts/`: Sample markdown blog posts
- `_settings/`: Configuration files (processors, mappings, etc.)
- `_queries/`: Query definitions

You can add more test data by creating additional markdown files in `_posts/` or modifying the configuration files.
