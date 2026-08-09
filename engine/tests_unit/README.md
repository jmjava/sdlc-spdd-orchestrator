# Suite 1 — unit

Fast, isolated tests: `tmp_path`, mocks, no Flask server, no browser, no network.

```bash
./scripts/run-test-suites.sh unit
pytest -q engine/tests_unit
```

Default CI gate and default `pyproject.toml` `testpaths`.
