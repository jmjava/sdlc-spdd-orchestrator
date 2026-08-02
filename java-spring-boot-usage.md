# Java / Spring Boot Usage

This scaffold works well for Spring Boot projects because norms and safeguards can encode:

- Controller / service / repository boundaries
- DTO and validation conventions
- Transaction and persistence rules
- Test strategy (unit, slice, integration)

## Stack Rules

Use `templates/stack-rules/java-spring-boot.md` during planning and architect review.

## Playbook

Follow `agent-context/playbooks/java-feature-playbook.md`.

## Example

See `examples/spring-boot-order-api/` for a sample requirement-to-review flow.

## Validation Commands

Gradle:

    ./gradlew test

Maven:

    ./mvnw test

Document any tests that could not be run in the progress log.
