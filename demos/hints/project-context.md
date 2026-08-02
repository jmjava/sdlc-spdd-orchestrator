---
docgen:
  project:
    env_file: ../../.env
    narration_from_source:
      hints:
        - >-
          Audience: SDLC-SPDD framework contributors and adopters evaluating or extending the
          orchestrator repo — not operators of a target application install.
        - >-
          Product: sdlc-spdd-orchestrator — a hybrid Planning + SPDD + SDLC Agents scaffolding
          system. Prose canon lives under docs/; do not contradict ten-thousand-foot-view.md
          or workflow.md.
        - >-
          Demo bundle includes Manim visuals and composed segment recordings (CHORE-002).
          Plain spoken paragraphs suitable for TTS; no markdown headings in narration output.
        - >-
          Emphasize the REASONS Canvas, Work IDs, and the three-part operating path (Planning,
          SPDD, SDLC). Target projects receive templates and docs/sdlc-spdd/ — not Guide RAG
          or this docgen bundle.
      context:
        paths:
          - README.md
          - docs/ten-thousand-foot-view.md
          - docs/what-spdd-brings.md
          - docs/workflow.md
          - docs/installing-into-your-project.md
          - docs/first-day-with-sdlc-spdd.md
          - docs/guide-rag-research-and-dogfooding.md
---

# Project context (SDLC-SPDD orchestrator docgen)

Body text is optional; **`docgen yaml-generate`** reads the YAML above and merges it into
`docs/demos/docgen.yaml` (`env_file`, `narration_from_source.hints`, and
`narration_from_source.context.paths`).

Re-run **`docgen yaml-generate --merge-defaults`** after editing this file or any
`segment-NN-*.md` hint.
