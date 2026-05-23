# Retro: FEAT-001-order-status-api

## Summary

Small Spring Boot read endpoint delivered in two coding operations with clear layer boundaries.

## Lessons Learned

- Task-sized operations made review straightforward
- WebMvcTest caught validation behavior early

## Reusable Patterns

- T01 service/repository before T02 controller
- Explicit email validation at controller edge

## Mistakes To Avoid

- Skipping architect review for "simple" endpoints

## Suggested Future Safeguards

- Require documentation operation before marking feature complete
