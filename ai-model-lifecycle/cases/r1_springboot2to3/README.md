# R1 — Spring Boot 2.7 → 3.x migration

**Status: FROZEN.** Do not edit the input module; it is the golden input for Gate 1.

## What this case is

A minimal but representative Spring Boot **2.7** Maven module (`legacy-customer-api`)
that is written against the **`javax.*`** namespaces. The candidate model must
upgrade it to **Spring Boot 3.x**.

## Input shape

```
pom.xml                                   # Boot 2.7.18, Java 11, JUnit 4
src/main/java/com/example/demo/
  LegacyCustomerApiApplication.java
  entity/Customer.java                    # javax.persistence.*, javax.validation.*
  repo/CustomerRepository.java            # Spring Data JPA (javax-agnostic)
  service/CustomerService.java            # javax.annotation.{PostConstruct,PreDestroy}
  web/CustomerController.java             # javax.validation.Valid
  web/ApiExceptionHandler.java            # javax.validation.ConstraintViolationException
  config/WebConfig.java                   # javax.servlet.*
  config/FeatureProperties.java           # javax.annotation.PostConstruct
src/main/resources/
  application.properties
  META-INF/spring.factories               # legacy auto-config registration
src/test/java/com/example/demo/
  CustomerTest.java                       # JUnit 4
  service/CustomerServiceTest.java        # JUnit 4 + Mockito
```

## Expected migrated result (golden outcome)

1. **`javax.*` → `jakarta.*`** everywhere it appears:
   - `javax.persistence.*` → `jakarta.persistence.*`
   - `javax.validation.*` → `jakarta.validation.*`
   - `javax.annotation.*` → `jakarta.annotation.*`
   - `javax.servlet.*` → `jakarta.servlet.*`
2. **`pom.xml`** on **Spring Boot 3.x**:
   - `spring-boot-starter-parent` version `3.2.x` or newer (3.x line).
   - `java.version` bumped to **17** (Boot 3 minimum).
   - JUnit 4 removed; tests run on **JUnit 5 / Jupiter** (`org.junit.jupiter.*`,
     `@BeforeEach`, `@Test`, assertions from `org.junit.jupiter.api.Assertions`).
3. **`src/main/resources/META-INF/spring.factories` removed.** Boot 3 uses
   `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`
   (or plain `@Configuration` discovery) instead.
4. Project still **compiles** (`mvn -q compile`) and **all tests pass**
   (`mvn -q test`).
5. No remaining `javax.` imports in `src/`.

## Pass criteria (automated — see `scorers/r1_scorer.py`)

| Check | Rule |
|---|---|
| compile | `mvn -q compile` exit 0 |
| tests | `mvn test` exit 0 (all green) |
| tests executed | at least as many tests run as the input defines (4) — JUnit 4 tests silently run 0 times under Boot's Jupiter-only starter |
| hidden tests | the input's own tests, migrated to JUnit 5 (`scorers/fixtures/r1_hidden_tests/`, never shown to models), pass against the model's main code |
| javax free | no code use of `javax.{persistence,validation,annotation,servlet}` under `src/` (comments and JDK packages like `javax.sql` are fine) |
| factories gone | no `spring.factories` under `src/main/resources` |
| boot 3 pom | `spring-boot-starter-parent` version starts with `3.` |

The model's output is applied as a patch: the input module is copied, `### DELETE:`
paths removed, emitted files written on top. Maven runs locally if installed,
otherwise in a `maven:3.9-eclipse-temurin-17` container. With neither, the build
checks are **unverified and the case fails**.

**Score = pass / fail** (all checks must pass).

### Input fix (2026-10-09)

`WebConfig.java` imported `javax.servlet.FilterRegistrationBean`, which does not
exist (it is `org.springframework.boot.web.servlet.FilterRegistrationBean`), so
the input never compiled and a literal javax→jakarta migration could not either.
The import was corrected; `javax.servlet.Filter` is still there to migrate.
