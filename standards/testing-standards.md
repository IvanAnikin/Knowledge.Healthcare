# Testing Standards

## Purpose

These standards define the project-wide expectations for testing. Individual applications may have additional testing requirements documented in their own repositories.

> Fill in sections as testing strategies are confirmed.

## General Principles

- **Test behavior, not implementation.** Tests should verify what the system does, not how it does it.
- **Tests are documentation.** A well-named test communicates expected behavior.
- **Failing tests block deployment.** No application should be deployed with known test failures unless explicitly accepted and documented.
- **Test at the right level.** Use unit tests for logic, integration tests for boundaries, and end-to-end tests sparingly for critical paths.

## Test Categories

| Category | Scope | Expectation |
|----------|-------|-------------|
| Unit | Individual functions/classes | <!-- Coverage targets TBD --> |
| Integration | Service boundaries, APIs, database interactions | <!-- Approach TBD --> |
| End-to-End | Critical user workflows | <!-- Scope TBD --> |
| Contract | API contracts between applications | <!-- Approach TBD --> |
| Security | Authentication, authorization, data access | <!-- Approach TBD --> |

## Test Data

- <!-- How is test data managed? -->
- <!-- Are there shared fixtures or factories? -->
- <!-- Rules for using production-like data: TBD -->
- **Never use real patient or user data in tests.** Use synthetic data only.

## CI/CD Integration

- <!-- When do tests run? (PR, merge, deploy) -->
- <!-- What blocks a merge? -->
- <!-- What blocks a deployment? -->

## Cross-Application Testing

- <!-- How are integration points between applications tested? -->
- <!-- Contract testing approach: TBD -->
- <!-- Shared test environments: TBD -->

## Open Questions

- <!-- Testing decisions that need team discussion -->
