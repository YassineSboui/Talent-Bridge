# Tests

Integration, smoke, and fixture tests for the modular Talent Bridge architecture.

Current tests:

```text
Tests/smoke/test_demo_logic.py
Tests/smoke/test_platform_workflows.py
Tests/integration/test_sql_ml_views.py
```

Run all current validation checks:

```bash
python -m compileall -q Backend/TalentBridgeAPI NLP DocumentAI Recommendation MachineLearning Tests
python Tests/smoke/test_demo_logic.py
python Tests/smoke/test_platform_workflows.py
python Tests/integration/test_sql_ml_views.py
```

The legacy backend script path may still exist for compatibility, but the repository-level tests above are the canonical validation commands.
