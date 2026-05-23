# Requirement: Order Status Search API

## Summary

Add a REST endpoint to search orders by customer email in a Spring Boot order service.

## User Story

As an operations user, I want to search orders by customer email so I can quickly answer support requests.

## Acceptance Criteria

- [ ] `GET /api/orders?email=` returns matching orders
- [ ] Invalid email format returns 400
- [ ] Empty result returns 200 with empty list
- [ ] Service layer owns lookup logic
- [ ] Controller remains thin
- [ ] Tests cover happy path and validation failure

## Non-Goals

- Pagination
- Authentication changes
- Database schema changes beyond existing order table
