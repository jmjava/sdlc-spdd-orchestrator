"""Argparse surface for sdlc-engine."""

from __future__ import annotations

import argparse

from .cli_commands import (
    cmd_next,
    cmd_status,
    cmd_resume,
    cmd_advance,
    cmd_gate,
    cmd_skip,
    cmd_shelf,
    cmd_sync,
    cmd_list_shelved,
    cmd_claim,
    cmd_release,
    cmd_team,
    cmd_list_work,
    cmd_sync_team,
    cmd_archive,
    cmd_pointer,
    cmd_context,
    cmd_storage,
    cmd_agent_context,
    cmd_version,
    cmd_shell,
    cmd_links,
    cmd_sync_links,
    cmd_sync_roadmap,
    cmd_issues,
    cmd_commit_message,
    cmd_sunset,
    cmd_db,
    cmd_quick,
    cmd_local,
    cmd_work,
    cmd_viewer,
    cmd_installer,
    cmd_template,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-engine",
        description="SDLC-SPDD Python orchestration engine (v2)",
    )
    p.add_argument(
        "--root",
        "--target",
        dest="root",
        help="Project root (default: SDLC_ROOT or git toplevel). --target is an alias.",
    )
    p.add_argument("--version", action="store_true", help="Print engine version")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("next", help="Show what to do now").set_defaults(func=cmd_next)

    qk = sub.add_parser(
        "quick",
        help='Start a LOCAL-* offline session from intent (zero ceremony)',
    )
    qk.add_argument("intent", help='One-line why this scratch work exists')
    qk.set_defaults(func=cmd_quick)

    st = sub.add_parser("status", help="Show workflow status")
    st.add_argument("--json", action="store_true")
    st.add_argument("--work-id")
    st.set_defaults(func=cmd_status)

    rs = sub.add_parser("resume", help="Resume a Work ID")
    rs.add_argument("work_id")
    rs.add_argument("--phase")
    rs.add_argument("--force", action="store_true")
    rs.set_defaults(func=cmd_resume)

    adv = sub.add_parser("advance", help="Advance workflow phase (gated; --force bypasses)")
    adv.add_argument("--to")
    adv.add_argument(
        "--force",
        action="store_true",
        help="Bypass gate checks (a human decision, never the agent's)",
    )
    adv.set_defaults(func=cmd_advance)

    gt = sub.add_parser(
        "gate",
        help="Check prerequisites to enter a phase (exit 0 ok / 1 blocked)",
    )
    gt.add_argument("--phase", required=True)
    gt.add_argument("--work-id", help="Work ID (default: active pointer)")
    gt.add_argument("--json", action="store_true")
    gt.set_defaults(func=cmd_gate)

    sk = sub.add_parser("skip", help="Skip a phase")
    sk.add_argument("phase")
    sk.add_argument("--reason", default="manual skip")
    sk.set_defaults(func=cmd_skip)

    sh = sub.add_parser("shelf", help="Shelf active work")
    sh.add_argument("--reason", default="manual shelf")
    sh.set_defaults(func=cmd_shelf)

    sy = sub.add_parser("sync", help="Sync workflow state from artifacts")
    sy.add_argument("--work-id")
    sy.set_defaults(func=cmd_sync)

    sub.add_parser("list-shelved", help="List shelved work").set_defaults(func=cmd_list_shelved)

    cl = sub.add_parser("claim", help="Claim a Work ID")
    cl.add_argument("work_id")
    cl.add_argument("--force", action="store_true")
    cl.add_argument("--phase")
    cl.add_argument("--branch")
    cl.add_argument("--pr")
    cl.add_argument("--jira", help="Override; default auto-reads ## Jira Key from milestone requirement")
    cl.add_argument("--note")
    cl.set_defaults(func=cmd_claim)

    lk = sub.add_parser("links", help="Show Jira/GitHub/registry/canvas link map")
    lk.add_argument("work_id", nargs="?")
    lk.set_defaults(func=cmd_links)

    sl = sub.add_parser(
        "sync-links",
        help="Check or repair drift across milestones, canvas Metadata, and registry",
    )
    sl.add_argument("work_id_pos", nargs="?", help="Optional Work ID (same as --work-id)")
    sl.add_argument("--work-id")
    sl.add_argument("--repair", action="store_true")
    sl.add_argument("--dry-run", action="store_true")
    sl.set_defaults(func=cmd_sync_links)

    sr = sub.add_parser("sync-roadmap", help="Refresh ROADMAP.md managed summary from canvases")
    sr.add_argument("--roadmap", default="ROADMAP.md")
    sr.add_argument("--dry-run", action="store_true")
    sr.set_defaults(func=cmd_sync_roadmap)

    iss = sub.add_parser(
        "issues",
        help=(
            "Draft/push/pull/link/upload-adf/download-adf for Jira or GitHub "
            "(explicit CLI; never auto-sync)"
        ),
    )
    iss.add_argument(
        "issues_cmd",
        choices=["draft", "push", "pull", "link", "upload-adf", "download-adf"],
    )
    iss.add_argument(
        "work_id",
        help=(
            "Work ID for draft/push/pull/link, Jira key for link second arg, "
            "or Jira issue key for upload-adf/download-adf"
        ),
    )
    iss.add_argument(
        "jira_key",
        nargs="?",
        default=None,
        help="For link: manually created Jira issue key (PROJECT-123)",
    )
    iss.add_argument(
        "--system",
        default="both",
        choices=["jira", "github", "both"],
        help="Target system (push/pull require jira|github)",
    )
    iss.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "adf", "wiki"],
        help="For `issues draft --system jira`: render body as markdown, ADF JSON, or wiki markup",
    )
    iss.add_argument(
        "--description-format",
        choices=["adf", "wiki"],
        default=None,
        help=(
            "For push/upload-adf: send raw ADF (default on Cloud v3) or run the "
            "optional ADF→wiki shim. Env: JIRA_DESCRIPTION_FORMAT. "
            "Auto-fallback ADF→wiki is off unless JIRA_DESCRIPTION_FALLBACK=1."
        ),
    )
    iss.add_argument(
        "--file",
        dest="adf_file",
        help="For upload-adf/download-adf: path to ADF JSON file",
    )
    iss.add_argument(
        "--issue",
        help=(
            "For upload-adf/download-adf: Jira issue key "
            "(defaults to work_id positional)"
        ),
    )
    iss.add_argument(
        "--summary",
        default=None,
        help="For link: optional local Summary bullet",
    )
    iss.add_argument(
        "--issue-type",
        dest="issue_type",
        default=None,
        help="For link: optional local Issue type bullet",
    )
    iss.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually create/update remote issue, write pulled milestone fields, "
            "or overwrite local ADF on download-adf (default is dry-run)"
        ),
    )
    iss.set_defaults(func=cmd_issues)

    loc = sub.add_parser(
        "local",
        help="Local/offline work sessions (machine-private until promoted)",
    )
    loc_sub = loc.add_subparsers(dest="local_cmd", required=True)

    ls = loc_sub.add_parser("start", help="Start a LOCAL-* offline session and set pointer")
    ls.add_argument("--name", help="Slug fragment (default from title/intent)")
    ls.add_argument("--title", help="Human title")
    ls.add_argument("--intent", help="One-line why this scratch work exists")
    ls.add_argument("--branch", help="Optional git branch name note")
    ls.set_defaults(func=cmd_local)

    ll = loc_sub.add_parser("list", help="List local/offline sessions on this machine")
    ll.add_argument("--all", action="store_true", help="Include promoted/abandoned")
    ll.set_defaults(func=cmd_local)

    lst = loc_sub.add_parser("status", help="Show active or named local session")
    lst.add_argument("--session", help="LOCAL-* id (default: pointer)")
    lst.set_defaults(func=cmd_local)

    lc = loc_sub.add_parser("capture", help="Append a note into the local session")
    lc.add_argument("--summary", required=True)
    lc.add_argument("--session")
    lc.set_defaults(func=cmd_local)

    lsh = loc_sub.add_parser("shelf", help="Park a local session (clear pointer)")
    lsh.add_argument("--reason", default="manual shelf")
    lsh.add_argument("--session")
    lsh.set_defaults(func=cmd_local)

    lr = loc_sub.add_parser("resume", help="Resume a shelved local session")
    lr.add_argument("session_id")
    lr.set_defaults(func=cmd_local)

    la = loc_sub.add_parser("abandon", help="Mark a local session abandoned")
    la.add_argument("--session")
    la.add_argument("--force", action="store_true")
    la.set_defaults(func=cmd_local)

    lp = loc_sub.add_parser(
        "promote",
        help="Promote LOCAL session into a documented Work ID (canvas + requirement)",
    )
    lp.add_argument("--type", default="feature", help="feature|spike|bug|refactor|chore|...")
    lp.add_argument("--name", help="Title/slug for the new Work ID (default: session title)")
    lp.add_argument("--session")
    lp.add_argument("--milestone", help="Optional milestone-*.md to append Linked Work")
    lp.add_argument("--no-claim", action="store_true", help="Create artifacts without claiming")
    lp.add_argument("--dry-run", action="store_true")
    lp.add_argument(
        "--from-git",
        help="Backfill session notes from git log range before promote (e.g. main..HEAD)",
    )
    lp.set_defaults(func=cmd_local)

    work = sub.add_parser(
        "work",
        help="Create / bootstrap Work IDs (engine-backed helpers)",
    )
    work_sub = work.add_subparsers(dest="work_cmd", required=True)
    wia = work_sub.add_parser(
        "init-from-adf",
        help="Create draft REASONS canvas + requirement from a local ADF file",
    )
    wia.add_argument("--path", required=True, help="Path to .adf.json / ADF JSON file")
    wia.add_argument("--type", default="feature", help="feature|spike|bug|refactor|chore|...")
    wia.add_argument("--title", help="Override title (default: first ADF heading or filename)")
    wia.add_argument("--work-id", help="Explicit Work ID (default: auto FEAT-NNN-slug)")
    wia.add_argument("--no-claim", action="store_true", help="Create artifacts without claiming")
    wia.add_argument("--dry-run", action="store_true")
    wia.set_defaults(func=cmd_work)

    cm = sub.add_parser(
        "commit-message",
        help="Collect staged/unstaged/ahead-of-base diff for drafting a commit message (does not commit)",
    )
    cm.add_argument("--hint", help="Optional short intent for the draft")
    cm.add_argument("--work-id", help="Optional Work ID (default: active pointer)")
    cm.add_argument("--base", help="Preferred base ref (default: origin/main)")
    cm.add_argument(
        "--max-diff",
        type=int,
        default=80_000,
        help="Truncate unified diff text to this many characters (default: 80000)",
    )
    cm.add_argument("--json", action="store_true", help="Emit DiffSnapshot JSON")
    cm.set_defaults(func=cmd_commit_message)

    sun = sub.add_parser(
        "sunset",
        help=(
            "Collect GitHub PR, GitHub issue, commit, and Jira state for a Work ID "
            "and optionally stage it into the lesson ledger"
        ),
    )
    sun.add_argument("--work-id", help="Work ID (default: active pointer)")
    sun.add_argument(
        "--apply",
        action="store_true",
        help="Stage a session record (source=sunset) in the gitignored ledger",
    )
    sun.add_argument(
        "--accept",
        action="store_true",
        help="Promote the sunset record into the committed ledger (implies --apply)",
    )
    sun.add_argument("--json", action="store_true", help="Emit SunsetSnapshot JSON")
    sun.set_defaults(func=cmd_sunset)

    db = sub.add_parser(
        "db",
        help="Local regenerable SQLite index (query cache before GUIDE/Neo4j)",
    )
    db_sub = db.add_subparsers(dest="db_cmd", required=True)

    db_sub.add_parser("rebuild", help="Rebuild .sdlc/index.sqlite from repo artifacts").set_defaults(
        func=cmd_db
    )
    db_sub.add_parser("status", help="Show index path, counts, rebuild metadata").set_defaults(
        func=cmd_db
    )
    db_sub.add_parser("path", help="Print absolute path to the SQLite file").set_defaults(func=cmd_db)

    dq = db_sub.add_parser("query", help="Query work_items (filters or read-only SQL SELECT)")
    dq.add_argument("sql", nargs="?", help="Optional SELECT … (read-only)")
    dq.add_argument("--work-id")
    dq.add_argument("--status", help="Match registry_status, canvas_status, or final_status")
    dq.add_argument("--search", help="Full-text (FTS5) or LIKE search")
    dq.add_argument("--limit", type=int, default=50)
    dq.add_argument("--columns", help="Comma-separated columns for table output")
    dq.add_argument("--json", action="store_true")
    dq.set_defaults(func=cmd_db)

    dl = db_sub.add_parser(
        "lookup",
        help="Machine-readable Work ID snapshot for session briefs (JSON or markdown)",
    )
    dl.add_argument("--work-id", required=True, help="Work ID to look up")
    dl.add_argument("--search", default="", help="Optional related FTS/LIKE hits")
    dl.add_argument("--limit", type=int, default=5, help="Max related search hits (default: 5)")
    dl.add_argument(
        "--markdown",
        action="store_true",
        help="Emit markdown section for embedding into a session brief",
    )
    dl.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON (default when --markdown is not set)",
    )
    dl.set_defaults(func=cmd_db)

    de = db_sub.add_parser("export", help="Export index as JSON or SQL dump (not for live multi-user sync)")
    de.add_argument("--format", choices=["json", "sql"], default="json")
    de.add_argument("--output", "-o", help="Write to file (default: stdout)")
    de.set_defaults(func=cmd_db)

    rel = sub.add_parser("release", help="Release/shelf active claim")
    rel.add_argument("--reason", default="released")
    rel.set_defaults(func=cmd_release)

    sub.add_parser("team", help="Show team registry").set_defaults(func=cmd_team)
    sub.add_parser("list-work", help="List Work IDs").set_defaults(func=cmd_list_work)
    sub.add_parser("sync-team", help="Refresh done/cancelled from canvases").set_defaults(func=cmd_sync_team)

    ar = sub.add_parser("archive", help="Archive completed/cancelled work")
    ar.add_argument("work_id", nargs="?")
    ar.add_argument("--all", action="store_true")
    ar.add_argument("--dry-run", action="store_true")
    ar.add_argument("--force", action="store_true")
    ar.set_defaults(func=cmd_archive)

    ptr = sub.add_parser("pointer", help="Pointer get/set/reset")
    ptr.add_argument("pointer_cmd", choices=["get", "set", "reset"])
    ptr.add_argument("work_id", nargs="?")
    ptr.set_defaults(func=cmd_pointer)

    ctx = sub.add_parser(
        "context",
        help="Ledger-first context store (git ledger + optional SQLite + Guide)",
    )
    ctx_sub = ctx.add_subparsers(dest="context_cmd", required=True)
    from .lessons_ledger import LEDGER_KINDS as _LEDGER_KINDS

    cpl = ctx_sub.add_parser(
        "persist-lesson",
        help="Stage or accept a lesson record in the ledger",
    )
    cpl.add_argument("--kind", required=True, choices=list(_LEDGER_KINDS))
    cpl.add_argument(
        "--work-id",
        default="",
        help="Work ID (optional when --area is set; omit on an ad hoc day)",
    )
    cpl.add_argument("--body", required=True, help="Body text or '-' for stdin")
    cpl.add_argument("--title", default="")
    cpl.add_argument(
        "--area",
        default="",
        help="Code area (required when --work-id is omitted)",
    )
    cpl.add_argument("--source", default="cli")
    cpl.add_argument("--phase", default="")
    cpl.add_argument("--keywords", default="", help="Comma-separated keywords")
    cpl.add_argument("--accept", action="store_true", help="Land directly in committed ledger")
    cpl.add_argument("--no-guide", action="store_true", help="Skip Guide projection fan-out")
    cpl.set_defaults(func=cmd_context)
    cpe = ctx_sub.add_parser(
        "persist-entry",
        help="Deprecated alias for persist-lesson",
    )
    cpe.add_argument("--kind", required=True)
    cpe.add_argument("--work-id", default="")
    cpe.add_argument("--body", required=True)
    cpe.add_argument("--area", default="")
    cpe.add_argument("--phase", default="")
    cpe.add_argument("--source", default="cli")
    cpe.add_argument("--no-guide", action="store_true")
    cpe.set_defaults(func=cmd_context)
    cacc = ctx_sub.add_parser("accept", help="Promote staged lessons to committed ledger")
    cacc.add_argument("--work-id", default="")
    cacc.add_argument("--ids", default="", help="Comma-separated record ids")
    cacc.add_argument("--discard-rest", action="store_true")
    cacc.add_argument("--no-guide", action="store_true")
    cacc.set_defaults(func=cmd_context)
    cshow = ctx_sub.add_parser("show", help="Show one lesson record by id")
    cshow.add_argument("record_id")
    cshow.set_defaults(func=cmd_context)
    cpar = ctx_sub.add_parser("parity", help="Diff ledger vs SQLite/Guide; optional repair")
    cpar.add_argument("--repair", action="store_true")
    cpar.set_defaults(func=cmd_context)
    cdig = ctx_sub.add_parser("digest", help="Bounded session-start digest")
    cdig.add_argument("--work-id", default="")
    cdig.add_argument("--areas", default="", help="Comma-separated areas")
    cdig.add_argument("--keywords", default="", help="Comma-separated keywords")
    cdig.add_argument("--limit", type=int, default=8)
    cdig.set_defaults(func=cmd_context)
    cre = ctx_sub.add_parser("retrieve", help="Assemble retrieve from ledger + projections")
    cre.add_argument("--work-id", default="")
    cre.add_argument("--area", default="")
    cre.add_argument("--kind", default="")
    cre.add_argument("--keyword", default="")
    cre.add_argument("--limit", type=int, default=50)
    cre.add_argument("--no-staged", action="store_true")
    cre.set_defaults(func=cmd_context)
    ctx_sub.add_parser(
        "coverage", help="Report CONTEXT_KINDS capability coverage in SQLite"
    ).set_defaults(func=cmd_context)
    cb = ctx_sub.add_parser(
        "backends",
        help="Show or set CONTEXT_BACKENDS persistence options",
    )
    cb.add_argument(
        "--set",
        dest="set_backends",
        default=None,
        help="Comma-separated backends: git-pointers,sqlite,guide-dice",
    )
    cb.add_argument("--guide-base-url", default=None)
    cb.add_argument("--notes", default=None)
    cb.set_defaults(func=cmd_context)
    cgq = ctx_sub.add_parser(
        "guide-query",
        help="Delegate a retrieval question to Guide spdd_* tools (HTTP parity with MCP)",
    )
    cgq.add_argument("--work-id", default="", help="Active Work ID → spdd_workSubgraph")
    cgq.add_argument("--area", default="", help="Code area → spdd_areaLessons")
    cgq.add_argument("--lesson-id", default="", help="Lesson entity id → spdd_getLesson")
    cgq.add_argument("--label", default="", help="Entity label → spdd_findByLabel")
    cgq.add_argument(
        "--question",
        default="",
        help="Natural-language hint (routes to work/area/stats when flags omitted)",
    )
    cgq.add_argument("--stats", action="store_true", help="Projection freshness counts")
    cgq.add_argument("--tool", default="", help="Explicit spdd_* tool name")
    cgq.add_argument("--tool-json", default="", help="JSON object of tool arguments")
    cgq.add_argument("--limit", type=int, default=20)
    cgq.add_argument("--guide-url", default="", help="Override GUIDE_BASE_URL")
    cgq.add_argument("--timeout", type=float, default=30.0)
    cgq.add_argument(
        "--text",
        action="store_true",
        help="Human-readable answer for Cursor/Copilot chat (default: JSON)",
    )
    cgq.set_defaults(func=cmd_context)
    cmc = ctx_sub.add_parser(
        "mcp-call",
        help="Call one Guide spdd_* MCP tool by name (REST parity; for agents/scripts)",
    )
    cmc.add_argument(
        "--tool",
        required=True,
        help="spdd_workSubgraph | spdd_areaLessons | spdd_findByLabel | spdd_projectionStats | spdd_getLesson",
    )
    cmc.add_argument(
        "--json",
        default="{}",
        help='Tool arguments JSON, e.g. {"workId":"FEAT-001-order-status-api"}',
    )
    cmc.add_argument("--guide-url", default="")
    cmc.add_argument("--timeout", type=float, default=30.0)
    cmc.set_defaults(func=cmd_context)

    st = sub.add_parser("storage", help="Storage v3 migration and status")
    st_sub = st.add_subparsers(dest="storage_cmd", required=True)
    st_sub.add_parser("status", help="Detect legacy layout / migration state").set_defaults(
        func=cmd_storage
    )
    stm = st_sub.add_parser("migrate", help="Migrate legacy agent-context to ledger v3")
    stm.add_argument("--dry-run", action="store_true")
    stm.set_defaults(func=cmd_storage)

    ac = sub.add_parser(
        "agent-context",
        help="Upgrade/re-init noisy agent-context runtime + quiet mode (#80/#91)",
    )
    ac_sub = ac.add_subparsers(dest="agent_context_cmd", required=True)
    ac_sub.add_parser("detect", help="Detect legacy sessions/features noise").set_defaults(
        func=cmd_agent_context
    )
    acu = ac_sub.add_parser(
        "upgrade",
        help="Archive sessions/features to .sdlc/legacy-export and seed lean runtime",
    )
    acu.add_argument("--dry-run", action="store_true")
    acu.add_argument("--no-rebuild", action="store_true")
    acu.set_defaults(func=cmd_agent_context)
    aqs = ac_sub.add_parser("quiet-status", help="Show quiet/product-test mode status")
    aqs.add_argument("--quiet", action="store_true", help="Treat as --quiet flag set")
    aqs.add_argument("--guide-live", action="store_true")
    aqs.set_defaults(func=cmd_agent_context)

    shell = sub.add_parser("shell", help="Run a v1 scripts/*.sh via bridge")
    shell.add_argument("script")
    shell.add_argument("script_args", nargs=argparse.REMAINDER)
    shell.set_defaults(func=cmd_shell)

    sub.add_parser("version", help="Print version").set_defaults(func=cmd_version)

    vw = sub.add_parser(
        "viewer",
        help="ADF WYSIWYG ticket viewer (Flask; requires optional [viewer] extra)",
    )
    vw.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
    vw.add_argument("--port", type=int, default=5050)
    vw.add_argument("--debug", action="store_true")
    vw.add_argument(
        "--lan",
        action="store_true",
        help="Bind 0.0.0.0 for LAN access (opt-in)",
    )
    vw.set_defaults(func=cmd_viewer)

    def _add_console_parser(name: str, help_text: str) -> None:
        inst = sub.add_parser(name, help=help_text)
        inst.add_argument(
            "--target",
            default=None,
            help="Default target project path shown in the UI (default: --root / cwd)",
        )
        inst.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
        inst.add_argument("--port", type=int, default=5051)
        inst.add_argument("--debug", action="store_true")
        inst.add_argument(
            "--lan",
            action="store_true",
            help="Bind 0.0.0.0 for LAN access (opt-in)",
        )
        inst.add_argument(
            "--no-browser",
            action="store_true",
            help="Do not open a browser tab automatically",
        )
        inst.add_argument(
            "--playground",
            action="store_true",
            help="Seed a disposable SPDD tree and open the console against it "
            "(no consumer install)",
        )
        inst.add_argument(
            "--playground-dir",
            default=None,
            help="Playground dest (default: <orchestrator>/.sdlc/console-playground)",
        )
        inst.set_defaults(func=cmd_installer)

    _add_console_parser(
        "installer",
        "EXPERIMENTAL ops console: install/upgrade, SQLite, rollback, Guide "
        "(Flask; [viewer] extra) — not a stable consumer install path",
    )
    _add_console_parser(
        "console",
        "EXPERIMENTAL alias for installer — ops console UI",
    )
    _add_console_parser(
        "dashboard",
        "EXPERIMENTAL alias for installer — ops console UI",
    )

    tmpl = sub.add_parser(
        "template",
        help="ADF template library: list/render/validate combos (header/body/footer)",
    )
    tmpl_sub = tmpl.add_subparsers(dest="template_cmd", required=True)
    tl = tmpl_sub.add_parser("list", help="List stock combo manifests")
    tl.add_argument("--json", action="store_true")
    tl.set_defaults(func=cmd_template)
    tmpl_sub.add_parser(
        "validate", help="Validate stock combo manifests + ADF schema"
    ).set_defaults(func=cmd_template)
    tr = tmpl_sub.add_parser(
        "render",
        help="Render planning artifacts for a Work ID into ADF JSON",
    )
    tr.add_argument("--work-id", required=True, help="Work ID to bind variables from")
    tr.add_argument(
        "--combo",
        default="",
        help="Combo id (feature|spike|bug); default: infer from Work ID prefix",
    )
    tr.add_argument(
        "--type",
        default="",
        help="Optional work-type override (feature|spike|bug|…)",
    )
    tr.add_argument(
        "-o",
        "--output",
        help="Write ADF JSON to this path (relative to --root unless absolute)",
    )
    tr.add_argument("--json", action="store_true", help="Emit full RenderResult JSON")
    tr.set_defaults(func=cmd_template)

    return p
