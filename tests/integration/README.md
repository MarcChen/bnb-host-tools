# Integration Tests

This directory contains integration tests for the bnb-host-tools package. 
These tests interact with external services and require valid credentials.

## Running Integration Tests

Integration tests are marked with the `@pytest.mark.integration` decorator and 
are not run by default when running pytest.

To run all integration tests:

```bash
poetry run pytest tests/integration -v -m integration
```

To run a specific integration test file:

```bash
poetry run pytest tests/integration/test_calendar_services.py -v
```

## Test Environment Setup

Integration tests require the following:

1. Valid Google API credentials in the location specified by your `TOKEN_PATH` environment variable
2. Internet connectivity to access Google APIs
3. Appropriate permissions for the services being tested

## Warning

Integration tests interact with real services and may create, modify, or delete data.
Make sure to use test accounts or sandboxed environments whenever possible.
