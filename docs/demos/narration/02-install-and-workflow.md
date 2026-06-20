To adopt SDLC-SPDD, start from this orchestrator repository. Run setup-agent-prompts.sh against your target application with the assistant bundles you need. Then run verify-project-install.sh on that target to confirm the three-part scaffold is in place. Open the target project in Cursor, GitHub Copilot Chat, or Claude Code.

Your first session should stay small. Pick one requirement, bug, refactor, or spike. A good first loop is install, initialize, analysis, plan, architect, code one operation, API test, review, and capture memory. You are proving the loop, not finishing a large feature in one sitting.

The workflow table in the docs gives you the canonical sequence. Step one is setting up prompts and memory. Step two is slash sdlc-spdd-init. Step three maps milestone work when you need it. Step four starts a session with start-agent-session.sh and the Resume Prompt from current-session.md. Step five runs slash sdlc-spdd-analysis on your requirement, then index-spdd-analysis.sh so keywords land in decision memory. Step six is slash sdlc-spdd-plan on the analysis artifact.

Work IDs use prefixes like FEAT, BUG, REF, SPIKE, DOC, TEST, and CHORE. The REASONS Canvas should reach Ready For Coding before you run slash sdlc-spdd-code on an operation.

After install, your target project gets a docs slash sdlc-spdd hub and the same guides under a leaner entry path. The orchestrator docs README remains the full reference for contributors extending the framework itself.
