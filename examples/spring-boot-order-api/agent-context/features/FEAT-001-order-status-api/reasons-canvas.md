# REASONS Canvas: FEAT-001-order-status-api - Order Status Search API

## Metadata

- Work ID: FEAT-001-order-status-api
- Work Type: Feature
- Status: Ready For Coding
- Created: 2026-05-23
- Updated: 2026-05-23
- Owner: example
- Target Project: spring-boot-order-api
- Stack: Java, Spring Boot, Gradle/Maven
- Related Issue:
- Related PR:

## R - Requirements

### User Goal

Search orders by customer email via REST API.

### Business / Product Goal

Reduce support response time for order lookup requests.

### Acceptance Criteria

- [ ] `GET /api/orders?email=` returns matching orders
- [ ] Invalid email format returns 400
- [ ] Empty result returns 200 with empty list
- [ ] Tests cover service and controller behavior

### Non-Goals

- Pagination
- Auth changes
- Schema migration

### Assumptions

- Order entity already has `customerEmail` field
- Existing repository pattern can add finder method

### Open Questions

- None for example

## E - Entities

### Domain Entities

- Order

### Application Components

- Controller: `OrderController`
- Service: `OrderService`
- Repository: `OrderRepository`
- Tests: unit + WebMvcTest

### Files Likely Affected

- `src/main/java/.../OrderController.java`
- `src/main/java/.../OrderService.java`
- `src/main/java/.../OrderRepository.java`
- `src/test/java/...`

## A - Approach

### Proposed Approach

Add repository finder by email, service method, and GET endpoint with email validation.

### Alternatives Considered

1. Specification API query — rejected as heavier than needed

### Trade-Offs

- Simple query parameter vs dedicated search resource

### Risks

- Email case sensitivity

### Failure Modes

- Repository called directly from controller

## S - Structure

### Files To Add

- `OrderSearchResponse` DTO if not present

### Files To Modify

- Controller, service, repository, tests

### Test Structure

- Service unit test for lookup
- WebMvcTest for endpoint and validation

## O - Operations

### T01 - Add repository and service lookup

- Status: Complete
- Description: Add `findByCustomerEmail` and service method
- Files: repository, service, service test
- Tests: service unit test
- Validation: unit tests pass

### T02 - Add REST endpoint

- Status: Complete
- Description: Expose GET `/api/orders?email=` with validation
- Files: controller, controller test
- Tests: WebMvcTest
- Validation: controller tests pass

### T03 - Document API behavior

- Status: Not Started
- Description: Update README or OpenAPI if project uses it
- Files: docs
- Tests: n/a
- Validation: docs review

## N - Norms

### General

- Follow existing project conventions
- One operation per coding session

### Java / Spring Boot

- Constructor injection
- No business logic in controller
- Preserve package boundaries

### Testing

- Add tests for behavior changes

## S - Safeguards

- Do not change auth behavior
- Do not change unrelated API endpoints
- Do not add dependencies without justification

## Review Checklist

- [x] Requirements satisfied for T01-T02
- [x] Entities updated correctly
- [x] Norms followed
- [x] Tests added
- [ ] Documentation updated (T03 pending)

## Sync Notes

Example canvas for reference; T03 remains open.

## Final Status

- Status: In Progress
- Completed Date:
- PR:
- Follow-Up Tasks: T03 documentation

## Architecture Notes

- Readiness: Ready For Coding
- Required tests: service unit + WebMvcTest
- Risk: normalize email casing in service if product requires case-insensitive search
