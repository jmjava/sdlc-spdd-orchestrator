---
docgen:
  segment:
    create: true
    id: "02"
    stem: 02-install-and-workflow
  wiring:
    narration:
      hints:
        - >-
          Walk the adoption path: clone the orchestrator, run setup-agent-prompts.sh against a
          target app, verify with verify-project-install.sh, then open the target in Cursor,
          Copilot, or Claude Code.
        - >-
          Cover the first-session loop from first-day-with-sdlc-spdd.md: init, analysis, plan,
          architect, code one operation, API test, review, capture memory — one small increment.
        - >-
          Reference workflow.md steps 1–6: set up prompts, initialize, map milestone work,
          start session with Resume Prompt, run analysis with index-spdd-analysis.sh, then plan.
        - >-
          Mention Work ID prefixes (FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE) and that canvases
          must reach Ready For Coding before /sdlc-spdd-code.
        - >-
          Close by noting deeper guides live in docs/README.md and docs/sdlc-spdd/ in target
          projects after install.
      context:
        paths:
          - docs/first-day-with-sdlc-spdd.md
          - docs/installing-into-your-project.md
          - docs/workflow.md
          - docs/initialization-and-invocation.md
    visual:
      type: manim
      class: InstallWorkflowScene
    manim_scene:
      hints:
        - >-
          Title card "Install & Daily Workflow" at top. Vertical stack of five labelled boxes:
          Clone orchestrator, setup-agent-prompts, verify install, Resume Prompt session,
          analysis → plan → code.
        - >-
          Reveal one box at a time with FadeIn. Blue/green/teal/orange palette consistent with segment 01.
        - >-
          Pace to timing.json when present; fallback ~14s hold if no timestamps yet.
---

# Segment 02 — Install and daily workflow (editorial notes, not narrated)

Hands-on tone. Map to workflow table steps 1–6. Manim visual: InstallWorkflowScene.
