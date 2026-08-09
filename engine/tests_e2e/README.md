# Suite 3 — E2E integration

Requires real browsers, network, and/or live infrastructure.

| Test area | Prerequisites |
|-----------|----------------|
| Playwright (console + viewer) | `pip install -e './engine[viewer-e2e]'` + `playwright install chromium` |
| GitHub Issues | `gh auth login` + `GH_TOKEN` or `GITHUB_TOKEN` |
| Guide + Neo4j | `SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh` |

Run:

```bash
./scripts/run-test-suites.sh e2e          # Playwright + GitHub (Guide optional)
./scripts/run-test-suites.sh e2e --guide  # + Guide stack harness
pytest -q engine/tests_e2e                # direct (after deps up)
```
