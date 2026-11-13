# Scorer fixtures (never shown to models)

`r1_hidden_tests/` — the R1 input module's own unit tests, migrated to JUnit 5
(generated with `tests/r1_reference.py`). The R1 scorer runs them against the
model's migrated main code to check that business behavior survived the
migration. A model that rewrites or invents classes instead of migrating them
fails here even if its own tests pass.

`r1b_hidden_tests/` — the JHipster sample app's own test suite (`src/test/java`
and `src/test/resources` of jhipster-sample-app v7.9.3: 52 unit tests and 140
integration tests), migrated to Spring Boot 3. The R1b scorer swaps it in for
the project's test sources. The changes from upstream are only the ones Boot 3
forces, plus two made so that framework wording and machine speed can't fail a
correct answer:

* `javax.{persistence,validation,servlet,mail}` → `jakarta.*`;
* `config/application*.yml`: `CamelCaseToUnderscoresNamingStrategy` (Boot 3
  dropped `SpringPhysicalNamingStrategy`), `PostgreSQLDialect` (Hibernate 6
  dropped JHipster's `FixedPostgreSQL10Dialect`), no
  `hibernate.id.new_generator_mappings` (removed in Hibernate 6), no
  `jhipster.logging.logstash.queue-size` (removed in JHipster 8, which binds
  strictly);
* `logback.xml`: `<root level="WARN">` (Logback 1.4 rejects a nested `<level>`);
* `TechnicalStructureTest`: ArchUnit 1.x API (`consideringAllDependencies()`,
  which keeps the 0.x behavior). The task prompt says the suite needs ArchUnit 1.x;
* `ExceptionTranslatorIT.testMethodNotSupported`: accepts Spring 6's wording
  ("Request method 'POST' is not supported") as well as Spring 5's;
* `junit-platform.properties`: 60 s per-test timeout instead of 15 s (on a
  2-CPU box the first mail test took 15.7 s in a full run and 3 s on its own).

Validated on 2026-10-13 against a reference migration (Spring Boot 3.1.5,
JHipster 8.0.0, Hibernate 6.2, problem-spring-web 0.29.1): `mvn -P-webapp
verify` passes all 52 + 140 with checkstyle and modernizer. The unmigrated
v7.9.3 project with its original tests passes the same 52 + 140 on Boot 2.7.
A committed known-good answer, `tests/r1b_reference_answer.txt` (Opus 5.5's
answer plus three hand fixes, see `cases/r1b_jhipster_boot3/NEAR_MISS.md`),
passes every stage including the 54 Cypress tests:
`GATE1_SLOW_TESTS=1 pytest -q tests/test_r1b_reference_slow.py`.

`r2_parity/` — 8 Playwright tests ported from the GWTP carstore's Cucumber
features, with the original Selenium page objects' selectors. Validated on
2026-10-13: the original GWT app passes 8/8 (`python -m scorers.r2_scorer
--baseline`), and so does an Angular port (Claude Haiku 5.5's answer from run
20261013T020049Z with its four `/api/manufacturer` URLs corrected to the
contract's `/api/manufacturers`). The unmodified answers of Haiku 4.5 and 5.5
fail on genuine mistakes: wrong REST paths, and a missing debug id
(`create-manufacturer`).

`r7_hidden_tests/` — shogun-core-main's own test suite (56 JUnit 4 classes,
776 tests on H2) migrated to JUnit 5 and Hibernate 6, plus `QueryRestrictionDaoTest`
(16 tests of the prompt's replacement for Hibernate's legacy Criteria). It is
the reference migration's `src/test`: Opus 5.5 at high thinking, in the sandbox
with a 3-hour limit (it finished in 54.9 min), track `r7-reference`, run
20261113T143615Z; the record under `runs/opus-5.5-cc-vs-glm-5.3/agentic/` rebuilds
the whole project (`python -m scorers.r7_scorer --tree-from-record <record> <dir>`).
Two of its added tests were left out because they test how it rewrote the SQL
dialects, which the prompt does not specify (`ShogunPostgresqlDialectTest`,
`ShogunCoreOracleDialectTest`), and one test was narrowed to the behaviour the
prompt states (a `null` restriction array means no restriction). The test
resources (Spring contexts, H2 settings) are the project's own, unchanged.
`SUITE.json` records the count the scorer requires (792).

Checks that keep it fair (`tests/test_r7_scorer.py`): every shogun-core class
it imports exists in the original project or is one of the prompt's two new
types; and every public or protected method of the original keeps its
signature in the reference except the protected `createDistinctRootEntityCriteria`,
which the prompt lets go. Validated on 2026-11-13: the reference passes all 9
checks (`python -m scorers.r7_scorer --baseline`: own tests 797, grading 792).

