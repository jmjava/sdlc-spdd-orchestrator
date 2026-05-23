# Java / Spring Boot Stack Rules

## Defaults

- Use the Java version configured by the project.
- Use the Spring Boot version configured by the project.
- Do not upgrade Java, Spring Boot, Gradle, Maven, or dependencies unless the task explicitly requires it.
- Follow existing package structure.
- Prefer minimal diffs.

## Architecture

- Controllers handle HTTP mapping, request validation handoff, and response shaping.
- Services own business/use-case logic.
- Repositories own persistence.
- Clients own external API calls.
- Configuration classes own Spring configuration.
- Domain models should not depend on web layer classes.
- DTOs should not leak persistence entities unless the project already does this.
- Package boundaries should remain consistent.

## Dependency Injection

- Prefer constructor injection.
- Avoid field injection.
- Do not introduce global mutable state.
- Do not introduce static service locators.

## Persistence

- Follow existing JPA/JDBC/MyBatis conventions.
- Do not modify schema without migration notes.
- Add indexes only when justified.
- Avoid N+1 query patterns.
- Preserve transaction boundaries.

## API

- Preserve existing response formats unless explicitly changed.
- Preserve existing error handling conventions.
- Add OpenAPI annotations only if the project already uses them.
- Keep validation consistent with existing usage.

## Testing

- Use JUnit 5 unless the project uses another test framework.
- Use Mockito only where existing test style supports it.
- Use SpringBootTest only when needed.
- Use WebMvcTest for controller slice tests where appropriate.
- Use DataJpaTest for repository tests where appropriate.
- Use Testcontainers for database integration tests if already used or explicitly requested.
- Add ArchUnit tests if architecture boundaries are important.

## Build

- If Gradle wrapper exists, use `./gradlew test`.
- If Maven wrapper exists, use `./mvnw test`.
- If no wrapper exists, use `mvn test` or `gradle test` only when appropriate.
- Document any tests that could not be run.
