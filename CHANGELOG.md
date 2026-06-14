# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Claude Code support as a third assistant adapter: `templates/claude/` command pack
  and `CLAUDE.md`, `scripts/install-claude-commands.sh`, `--claude` flags on
  setup/init/upgrade, `--require-claude` install verification, Claude command-pack
  parity validation, CI path coverage, and `docs/claude-usage.md`
- Always-on Cursor operating-model rule (`templates/cursor/rules/sdlc-spdd.mdc`,
  installed to `.cursor/rules/`) giving Cursor the same whole-ecosystem grounding
  as Copilot's `copilot-instructions.md` and Claude's `CLAUDE.md`
- Whole-ecosystem grounding norm enforced in CI: `validate-command-adapters.sh`
  asserts every assistant's always-on grounding file covers Planning + SPDD + SDLC
- Adapter install/upgrade regression harness (`tests/test-adapter-install.sh`) and
  `test-adapter-install` CI workflow proving Cursor/Copilot are not regressed,
  no-flag defaults remain backward compatible, and existing `CLAUDE.md` content
  is preserved on upgrade
- Initial repository structure per STARTER-SPEC.md
- REASONS Canvas templates (feature, bugfix, refactor, spike)
- Eight Cursor command templates for SDLC-SPDD lifecycle
- Shell scripts: init, install commands, create feature, validate canvas, detect stack, sync context
- Stack rules for Java/Spring Boot, Gradle, Maven, Kubernetes, Tekton, Python, Node, Docker
- Agent overlays, playbooks, memory, and harness files
- Spring Boot order API example workflow
- Tekton pipeline demo layout
- GitHub issue and pull request templates
- GitHub Actions workflow for canvas validation
- Project documentation under `docs/`
