# Scorer fixtures (never shown to models)

`r1_hidden_tests/` — the R1 input module's own unit tests, migrated to JUnit 5
(generated with `tests/r1_reference.py`). The R1 scorer runs them against the
model's migrated main code to check that business behavior survived the
migration. A model that rewrites or invents classes instead of migrating them
fails here even if its own tests pass.
