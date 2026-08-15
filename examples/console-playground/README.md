# Vue ops console playground

This directory is documentation only. The live tree is generated (and
regenerated) at `<orchestrator>/.sdlc/console-playground` — gitignored.

```bash
./scripts/sdlc.sh console --playground
```

Seeds three Work IDs (feature / spike / bug), a pointer, ledger + staged
capture, registry, sample ADF, a fake upgrade backup, and persistence /
integrations config. Guide, Jira, and GitHub stay mocked or DOWN.

Do not install this tree into a real app. Click around; wipe by re-running
`--playground`.
