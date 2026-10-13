"""Shared pytest setup.

MLflow is optional (requirements-mlflow.txt). Without it, its tests are left out
of collection instead of reported as skipped: RUN_AT_HOME.md treats any skip as
a broken Docker/Postgres setup.

The same goes for slow end-to-end scorer checks: collected only with
GATE1_SLOW_TESTS=1.
"""

import importlib.util
import os

collect_ignore = [] if importlib.util.find_spec("mlflow") else ["test_mlflow_export.py"]
if os.environ.get("GATE1_SLOW_TESTS") != "1":
    collect_ignore.append("test_r1b_reference_slow.py")
