# Diagrams (generated)

Images in this folder are generated from Mermaid blocks in the Markdown docs.
Do not edit them by hand. Regenerate after changing a diagram:

    ./scripts/render-diagrams.sh

Naming: `<source-path-slug>-<n>.<ext>` (for example, `README-1.svg` and
`README-1.png` are the first Mermaid diagram in the top-level `README.md`).
Each diagram is exported as both SVG and PNG by default.

These exports are useful where Mermaid does not render (PDF exports, some
Markdown viewers). To validate diagrams without writing files (for CI), run:

    ./scripts/render-diagrams.sh --check
