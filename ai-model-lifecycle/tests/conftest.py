"""Shared pytest setup.

MLflow is optional (requirements-mlflow.txt). Without it, its tests are left out
of collection instead of reported as skipped: RUN_AT_HOME.md treats any skip as
a broken Docker/Postgres setup.
"""

import importlib.util

collect_ignore = [] if importlib.util.find_spec("mlflow") else ["test_mlflow_export.py"]
