This repository does more than publish a framework for other teams. We use the same SPDD workflow, docgen tooling, and Guide research stack to improve the orchestrator itself. That is intentional dogfooding.

During slash sdlc-spdd-analysis, contributors need grounded context without pasting huge documents into every prompt. Embabel Guide plus Neo4j is an optional local backend. Markdown files stay canonical. Availability is resolved at runtime — when Guide is down, commands keep using file indexes. That is normal, not an error.

SPIKE zero zero one has a provisional go on main for field confirmation. The Guide checkout pins to tag sdlc-spdd-projection-v1. From the experimental ops console Guide tab, you can start Neo4j and Guide, load the typed entity projection, and run ingest operators for dogfood.

Ingest works in two complementary shapes. First, RAG chunks for similarity search. Second, typed domain entities — Work I D, Canvas, Area, Decision, Pitfall, Pattern — connected by named edges. MCP tools expose docs vector Search and docs text Search for discovery, and spdd underscore tools for Work I D subgraphs and area lessons.

The corpus can still be layered with menke profiles when you want broader research material — code repos, SPDD references, framework depth, and docgen sources — as append passes on the same store, typically on port twenty-one thousand three hundred thirty-seven.

On this repo we dogfood SPDD on ourselves, docgen with this narration bundle, and Guide for research. A posture guard keeps internal development language out of shipped templates. The ADF Viewer is a separate local UI for ticket ADF editing and Jira sync. It does not talk to Guide.

None of that research infrastructure ships to target projects. Guide YAML, Neo4j data, MCP wiring, the local venv, and regenerable audio and video stay on the orchestrator side. Targets opt in only with a guide-dice harness marker via install --with-guide. For the flow diagram see guide-flow in docs. For setup, see the dice projection runbook.
