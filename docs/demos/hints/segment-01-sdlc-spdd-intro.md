---
docgen:
  segment:
    create: true
    id: "01"
    stem: 01-sdlc-spdd-intro
  wiring:
    narration:
      hints:
        - >-
          Open with the core problem: AI coding context lives in chat and disappears. SDLC-SPDD
          moves requirements, REASONS canvases, tasks, reviews, memory, and session handoffs
          into version-controlled files so a new agent session can resume from artifacts.
        - >-
          Explain the three parts: Planning (roadmap, milestones, session notes) informs and
          summarizes; SPDD (REASONS Canvas) governs what artifact owns the work; SDLC Agents
          supplies role-separated lifecycle and session handoffs.
        - >-
          Introduce the REASONS Canvas briefly — Requirements, Entities, Approach, Structure,
          Operations, Norms, Safeguards — as the fixed prompt contract before code.
        - >-
          Close by pointing to segment 02 for installing into a target project and the daily
          workflow sequence.
      context:
        paths:
          - README.md
          - docs/ten-thousand-foot-view.md
          - docs/what-spdd-brings.md
          - docs/three-part-operating-path.md
    visual:
      type: manim
      class: SdlcSpddIntroScene
    manim_scene:
      hints:
        - >-
          Open with centred title "SDLC-SPDD Orchestrator", then shrink to top edge.
          Reveal three horizontal boxes: Planning, SPDD, SDLC Agents — one FadeIn each.
        - >-
          Below, show a REASONS Canvas label and a row of single-letter pills R-E-A-S-O-N-S.
          Use orchestrator palette (accent #667eea, green #42b883, teal #26c6da).
        - >-
          One reveal per mobject; stay inside safe content width. Pace to timing.json when present.
---

# Segment 01 — SDLC-SPDD intro and REASONS loop (editorial notes, not narrated)

Anchor on docs/ten-thousand-foot-view.md and what-spdd-brings.md. Keep under ~90 seconds
spoken. Manim visual: SdlcSpddIntroScene.
