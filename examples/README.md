# Examples (storage v3)

Minimal sample layouts for docs and CI. They use the v3 contract paths only —
no `agent-context/memory/` indexes or `agent-context/features/` mirrors.

| Example | Purpose |
|---------|---------|
| [`spring-boot-order-api/`](spring-boot-order-api/) | End-to-end command flow sample; canvas validated in CI |

Install targets get their own `requirements/`, `spdd/`, and `harness/` trees —
see [docs/installing-into-your-project.md](../docs/installing-into-your-project.md).

Legacy SPIKE-001 retrieval fixtures (`retrieval-fixture/`, markdown index gold
tests) were removed — retrieval is ledger-first plus optional Guide MCP; see
[docs/storage-v3.md](../docs/storage-v3.md).
