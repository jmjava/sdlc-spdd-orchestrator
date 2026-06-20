# Narration scripts (TTS source)

These Markdown files are the spoken script for demo segments.
`docgen tts` turns them into `audio/*.mp3`.

## Voice-first editing

TTS reads what you write literally. Tips:

- Use spoken URLs: "GET slash api slash data" not `GET /api/data`
- Spell out abbreviations the first time
- No markdown formatting — plain spoken English only
- Run `docgen lint` to check for leaked metadata before TTS

## After edits

```bash
docgen tts                     # regenerate audio
docgen rebuild-after-audio     # re-render visuals + compose + validate + concat
```
