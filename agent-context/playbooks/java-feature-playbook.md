# Java Feature Playbook

1. From the orchestrator repo, run `./scripts/setup-agent-prompts.sh --target /path/to/project --all` if the project is not initialized.
2. Start or resume context with `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase plan`.
3. Capture the requirement under `requirements/`.
4. Run `/sdlc-spdd-plan` against the requirement, including skill directives such as `#java` or `#TDD` when relevant.
5. Run `/sdlc-spdd-architect` until readiness is **Ready For Coding**.
6. Before each new agent session, run `./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only`.
7. Implement one operation at a time with `/sdlc-spdd-code`.
8. Run `/sdlc-spdd-review` after each meaningful change set.
9. Run `/sdlc-spdd-retro` when the work is complete.
10. Run `/sdlc-spdd-sync` to reconcile canvas and code.
11. Persist memory with `./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --next "<next command>"`.

Apply `templates/stack-rules/java-spring-boot.md` during planning and coding.
