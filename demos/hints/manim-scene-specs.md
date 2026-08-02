# Manim declarative scene specs (SDLC-SPDD demos)

**Default path:** `animations/specs/*.scene.yaml` via `docgen scene-spec-generate`
(or first `generate-all`, which auto-generates missing specs). Do **not** hand-edit
generated classes between `BEGIN/END GENERATED SCENE` markers in `scenes.py` —
edit the YAML (or re-generate) and recompile.

Constraints:

- **Spoken labels only:** every paced box `label` must be a short phrase that appears
  in the segment narration / `timing.json` words (or set `pace: none` to opt out).
  Invented slogans that are never spoken will fail scene-spec-generate / retime.
  Hyphenated compounds and script names (`version-controlled`, `setup-agent-prompts.sh`)
  are fine — Whisper often emits them as one word; docgen retimes by gluing split tokens.
- **Pages, not shrinking:** use top-level **`pages`** when the story needs more boxes
  than fit on one screen (~3 rows/page; compact `height` ~0.72–0.9).
- **Palette tokens only:** `C_BG`, `C_ACCENT`, `C_GREEN`, `C_ORANGE`, `C_BLUE`,
  `C_RED`, `C_TEAL`, `C_PURPLE`, `C_WHITE`.
- **ASCII labels:** no smart punctuation; use `->` or hyphen.
- **Subject-beat coverage:** hold the board while consecutive sentences share a topic;
  when the topic shifts, add a spoken-phrase label for that beat.
- See library dogfood notes: documentation-generator `docs/demos/hints/manim-scene-specs.md`.
