# Task: Upgrade this project to Spring Boot 3.x

You are given a Spring Boot **2.7** Maven module in the attached case file listing
(`legacy-customer-api`). Upgrade it to **Spring Boot 3.x**.

## Requirements

1. Migrate **all** `javax.*` imports to their `jakarta.*` equivalents:
   `javax.persistence`, `javax.validation`, `javax.annotation`, `javax.servlet`.
2. Update `pom.xml`:
   - `spring-boot-starter-parent` to a **3.x** version (3.2.x or newer),
   - `java.version` to **17**,
   - replace the JUnit 4 dependency with JUnit 5 (Jupiter).
3. Migrate the tests from JUnit 4 to JUnit 5:
   - `org.junit.Test` → `org.junit.jupiter.api.Test`,
   - `@Before` → `@BeforeEach`,
   - `org.junit.Assert.*` → `org.junit.jupiter.api.Assertions.*`.
4. **Delete** `src/main/resources/META-INF/spring.factories` (Boot 3 no longer uses it).
5. The project must still **compile** (`mvn -q compile`) and **all tests must pass**
   (`mvn -q test`). Do not change business behavior.

## Output format

Emit **every file you create or modify** — including the full `pom.xml`, all Java
sources, and the tests — each in its own fenced block preceded by a header line:

```
### FILE: <relative/path/from/project/root>
```

Use the exact project-relative paths shown in the case file listing. Also explicitly
state, in a single line `### DELETE: <path>`, any file the migration removes
(e.g. `src/main/resources/META-INF/spring.factories`).

Do not include any other commentary outside the file blocks.
