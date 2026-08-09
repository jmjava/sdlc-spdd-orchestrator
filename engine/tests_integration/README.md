# Suite 2 — local integration

Flask `test_client` exercises for the ops console installer API and ADF viewer app.
No browser, no live Jira/GitHub/Guide.

```bash
./scripts/run-test-suites.sh integration
pytest -q engine/tests_integration
```

Requires `pip install -e './engine[dev,viewer]'`.
