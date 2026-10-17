"""sdlc-engine context."""

from __future__ import annotations

import argparse
import json
import sys

from .result import CommandResult
from .util import arg_flag, arg_int, arg_list, arg_str, project_from


def _optional_nonneg_int(value: str) -> int:
    from ..metrics import parse_nonneg_int

    try:
        return parse_nonneg_int(value, name="value")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def register(sub: argparse._SubParsersAction) -> None:
    from ..lessons_ledger import LEDGER_KINDS
    from ..metrics import CAPTURE_CONSTRUCTS, NON_CAPTURE_CONSTRUCTS

    ctx = sub.add_parser(
        "context",
        help="Ledger-first context store (git ledger + optional SQLite + Guide)",
    )
    ctx_sub = ctx.add_subparsers(dest="context_cmd", required=True)
    _register_persist(ctx_sub, LEDGER_KINDS)
    _register_read(ctx_sub, CAPTURE_CONSTRUCTS, NON_CAPTURE_CONSTRUCTS)
    _register_guide(ctx_sub)


def _register_persist(ctx_sub, ledger_kinds) -> None:
    cpl = ctx_sub.add_parser("persist-lesson", help="Stage or accept a lesson record in the ledger")
    cpl.add_argument("--kind", required=True, choices=list(ledger_kinds))
    cpl.add_argument("--work-id", default="", help="Work ID (optional when --area is set; omit on an ad hoc day)")
    cpl.add_argument("--body", required=True, help="Body text or '-' for stdin")
    cpl.add_argument("--title", default="")
    cpl.add_argument("--area", default="", help="Code area (required when --work-id is omitted)")
    cpl.add_argument("--source", default="cli")
    cpl.add_argument("--phase", default="")
    cpl.add_argument("--keywords", default="", help="Comma-separated keywords")
    cpl.add_argument("--accept", action="store_true", help="Land directly in committed ledger")
    cpl.add_argument("--no-guide", action="store_true", help="Skip Guide projection fan-out")
    cpl.add_argument("--readiness", default="", help="Capture metric: canvas readiness")
    cpl.add_argument("--review-result", default="", help="Capture metric: pass|fail|mixed|blocked")
    cpl.add_argument("--rework", type=_optional_nonneg_int, default=None, help="Capture metric: repair count (C-REWORK)")
    cpl.add_argument("--context-files", type=_optional_nonneg_int, default=None, dest="context_files")
    cpl.add_argument("--validate-cycles", type=_optional_nonneg_int, default=None, dest="validate_cycles")
    cpl.add_argument("--review-cycles", type=_optional_nonneg_int, default=None, dest="review_cycles")
    cpl.set_defaults(func=run)
    cpe = ctx_sub.add_parser("persist-entry", help="Deprecated alias for persist-lesson")
    cpe.add_argument("--kind", required=True)
    cpe.add_argument("--work-id", default="")
    cpe.add_argument("--body", required=True)
    cpe.add_argument("--area", default="")
    cpe.add_argument("--phase", default="")
    cpe.add_argument("--source", default="cli")
    cpe.add_argument("--no-guide", action="store_true")
    cpe.set_defaults(func=run)
    cacc = ctx_sub.add_parser("accept", help="Promote staged lessons to committed ledger")
    cacc.add_argument("--work-id", default="")
    cacc.add_argument("--ids", default="", help="Comma-separated record ids")
    cacc.add_argument("--discard-rest", action="store_true")
    cacc.add_argument("--no-guide", action="store_true")
    cacc.set_defaults(func=run)


def _register_read(ctx_sub, capture_constructs, non_capture) -> None:
    cshow = ctx_sub.add_parser("show", help="Show one lesson record by id")
    cshow.add_argument("record_id")
    cshow.set_defaults(func=run)
    cpar = ctx_sub.add_parser("parity", help="Diff ledger vs SQLite/Guide; optional repair")
    cpar.add_argument("--repair", action="store_true")
    cpar.set_defaults(func=run)
    cdig = ctx_sub.add_parser("digest", help="Bounded session-start digest")
    cdig.add_argument("--work-id", default="")
    cdig.add_argument("--areas", default="", help="Comma-separated areas")
    cdig.add_argument("--keywords", default="", help="Comma-separated keywords")
    cdig.add_argument("--limit", type=int, default=8)
    cdig.set_defaults(func=run)
    cre = ctx_sub.add_parser("retrieve", help="Assemble retrieve from ledger + projections")
    cre.add_argument("--work-id", default="")
    cre.add_argument("--area", default="")
    cre.add_argument("--kind", default="")
    cre.add_argument("--keyword", default="")
    cre.add_argument("--query", default="", help="Free-text query for title-body ranking (FEAT-017)")
    cre.add_argument("--rank", default="", choices=["", "keyword-list", "title-body"])
    cre.add_argument("--limit", type=int, default=50)
    cre.add_argument("--no-staged", action="store_true")
    cre.set_defaults(func=run)
    cmet = ctx_sub.add_parser("metrics", help="Query structured capture metrics (FEAT-015; does not parse session.body)")
    cmet.add_argument("--work-id", default="")
    cmet.add_argument("--phase", default="")
    cmet.add_argument(
        "--construct",
        default="",
        help="DOC-001 construct: " + "|".join(capture_constructs + non_capture) + " (omit for all capture constructs)",
    )
    cmet.add_argument("--no-staged", action="store_true")
    cmet.set_defaults(func=run)
    cev = ctx_sub.add_parser("eval-retrieve", help="Run keyword-list vs title-body IR eval on a qrel fixture (FEAT-017)")
    cev.add_argument("--fixture", required=True, help="JSON qrel fixture path")
    cev.set_defaults(func=run)
    ctx_sub.add_parser("coverage", help="Report CONTEXT_KINDS capability coverage in SQLite").set_defaults(func=run)
    cb = ctx_sub.add_parser("backends", help="Show or set CONTEXT_BACKENDS persistence options")
    cb.add_argument("--set", dest="set_backends", default=None, help="Comma-separated backends: git-pointers,sqlite,guide-dice")
    cb.add_argument("--guide-base-url", default=None)
    cb.add_argument("--notes", default=None)
    cb.set_defaults(func=run)


def _register_guide(ctx_sub) -> None:
    cgq = ctx_sub.add_parser(
        "guide-query",
        help="Delegate a retrieval question to Guide spdd_* tools (HTTP parity with MCP)",
    )
    cgq.add_argument("--work-id", default="")
    cgq.add_argument("--area", default="")
    cgq.add_argument("--lesson-id", default="")
    cgq.add_argument("--label", default="")
    cgq.add_argument("--question", default="")
    cgq.add_argument("--stats", action="store_true")
    cgq.add_argument("--tool", default="")
    cgq.add_argument("--tool-json", default="")
    cgq.add_argument("--limit", type=int, default=20)
    cgq.add_argument("--guide-url", default="")
    cgq.add_argument("--timeout", type=float, default=30.0)
    cgq.add_argument("--text", action="store_true")
    cgq.set_defaults(func=run)
    cmc = ctx_sub.add_parser("mcp-call", help="Call one Guide spdd_* MCP tool by name (REST parity; for agents/scripts)")
    cmc.add_argument("--tool", required=True)
    cmc.add_argument("--json", default="{}", help='Tool arguments JSON, e.g. {"workId":"FEAT-001-order-status-api"}')
    cmc.add_argument("--guide-url", default="")
    cmc.add_argument("--timeout", type=float, default=30.0)
    cmc.set_defaults(func=run)


def _body(args: argparse.Namespace) -> str:
    body = args.body
    return sys.stdin.read() if body == "-" else body


def _persist_lesson(store, args: argparse.Namespace) -> CommandResult:
    work_id = arg_str(args, "work_id")
    area = arg_str(args, "area")
    if not work_id and not area:
        return CommandResult.error("persist-lesson: --work-id or --area is required", code=2)
    try:
        result = store.persist_lesson(
            kind=args.kind,
            work_id=work_id,
            body=_body(args),
            title=arg_str(args, "title"),
            area=area,
            source=arg_str(args, "source", "cli"),
            phase=arg_str(args, "phase"),
            keywords=arg_list(args, "keywords") or None,
            accept=arg_flag(args, "accept"),
            project_guide=not arg_flag(args, "no_guide"),
            readiness=arg_str(args, "readiness") or None,
            review_result=arg_str(args, "review_result") or None,
            rework=getattr(args, "rework", None),
            context_files=getattr(args, "context_files", None),
            validate_cycles=getattr(args, "validate_cycles", None),
            review_cycles=getattr(args, "review_cycles", None),
        )
    except ValueError as exc:
        return CommandResult.error(f"persist-lesson: {exc}", code=2)
    return CommandResult(exit_code=0 if result.git.get("ok") else 1, stdout=json.dumps(result.as_dict(), indent=2) + "\n")


def _persist_entry(store, args: argparse.Namespace) -> CommandResult:
    from ..lessons_ledger import LEDGER_KINDS

    result = store.persist_lesson(
        kind=args.kind if args.kind in LEDGER_KINDS else "decision",
        work_id=arg_str(args, "work_id"),
        body=_body(args),
        area=arg_str(args, "area"),
        source=arg_str(args, "source", "cli"),
        phase=arg_str(args, "phase"),
        project_guide=not arg_flag(args, "no_guide"),
    )
    return CommandResult(
        exit_code=0 if result.git.get("ok") else 1,
        stdout=json.dumps(result.as_dict(), indent=2) + "\n",
        stderr="warning: persist-entry is deprecated; use context persist-lesson\n",
    )


def _accept(store, args: argparse.Namespace) -> CommandResult:
    out = store.accept(
        work_id=arg_str(args, "work_id"),
        ids=arg_list(args, "ids") or None,
        discard_rest=arg_flag(args, "discard_rest"),
        project_guide=not arg_flag(args, "no_guide"),
    )
    return CommandResult.ok(json.dumps(out, indent=2))


def _show(store, args: argparse.Namespace) -> CommandResult:
    rec = store.show(args.record_id)
    if rec is None:
        return CommandResult(exit_code=1, stdout=json.dumps({"error": "not found", "id": args.record_id}, indent=2) + "\n")
    return CommandResult.ok(json.dumps(rec, indent=2))


def _parity(store, args: argparse.Namespace) -> CommandResult:
    out = store.parity(repair=arg_flag(args, "repair"))
    return CommandResult(exit_code=0 if out.get("ok") else 1, stdout=json.dumps(out, indent=2) + "\n")


def _digest(store, args: argparse.Namespace) -> CommandResult:
    payload = store.digest(
        work_id=arg_str(args, "work_id"),
        areas=arg_list(args, "areas") or None,
        keywords=arg_list(args, "keywords") or None,
        limit=arg_int(args, "limit", 8),
    )
    return CommandResult.ok(json.dumps(payload, indent=2))


def _retrieve(store, args: argparse.Namespace) -> CommandResult:
    payload = store.retrieve(
        work_id=arg_str(args, "work_id"),
        area=arg_str(args, "area"),
        kind=arg_str(args, "kind"),
        keyword=arg_str(args, "keyword"),
        query=arg_str(args, "query"),
        rank=arg_str(args, "rank"),
        include_staged=not arg_flag(args, "no_staged"),
        limit=arg_int(args, "limit", 50),
    )
    return CommandResult.ok(json.dumps(payload, indent=2))


def _eval_retrieve(_store, args: argparse.Namespace) -> CommandResult:
    from pathlib import Path

    from ..retrieve import load_and_evaluate

    fixture = Path(args.fixture)
    if not fixture.is_file():
        return CommandResult.error(f"eval-retrieve: fixture not found: {fixture}", code=2)
    return CommandResult.ok(json.dumps(load_and_evaluate(fixture), indent=2))


def _metrics(store, args: argparse.Namespace) -> CommandResult:
    try:
        payload = store.metrics_query(
            construct=arg_str(args, "construct"),
            work_id=arg_str(args, "work_id"),
            phase=arg_str(args, "phase"),
            include_staged=not arg_flag(args, "no_staged"),
        )
    except ValueError as exc:
        return CommandResult.error(f"metrics: {exc}", code=2)
    return CommandResult.ok(json.dumps(payload, indent=2))


def _coverage(_store, args: argparse.Namespace) -> CommandResult:
    from ..db import LocalIndex

    return CommandResult.ok(json.dumps(LocalIndex(project_from(args)).capability_coverage(), indent=2))


def _backends(_store, args: argparse.Namespace) -> CommandResult:
    from ..persistence import load_config, save_config, status_dict

    project = project_from(args)
    if getattr(args, "set_backends", None) is None:
        return CommandResult.ok(json.dumps(status_dict(project), indent=2))
    raw = arg_str(args, "set_backends").strip()
    if not raw:
        return CommandResult.error("error: --set requires a non-empty backend list", code=2)
    backends = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    cfg = load_config(project)
    cfg["backends"] = backends
    if getattr(args, "guide_base_url", None):
        cfg["guide_base_url"] = args.guide_base_url
    if getattr(args, "notes", None) is not None:
        cfg["notes"] = args.notes
    try:
        return CommandResult.ok(json.dumps(save_config(project, cfg), indent=2))
    except ValueError as exc:
        return CommandResult.error(f"error: {exc}", code=2)


def _guide_client(args: argparse.Namespace):
    from ..guide_client import GuideClient, resolve_guide_base_url
    from ..persistence import load_config as load_persist_cfg

    cfg = load_persist_cfg(project_from(args))
    base = resolve_guide_base_url(
        explicit=arg_str(args, "guide_url") or None,
        project_url=str(cfg.get("guide_base_url") or ""),
    )
    return GuideClient(base, timeout=float(getattr(args, "timeout", None) or 30))


def _guide_query(_store, args: argparse.Namespace) -> CommandResult:
    from ..guide_query import format_guide_answer, run_guide_query

    client = _guide_client(args)
    tool_json = arg_str(args, "tool_json")
    tool_args = json.loads(tool_json) if tool_json else {}
    try:
        payload = run_guide_query(
            client,
            work_id=arg_str(args, "work_id"),
            area=arg_str(args, "area"),
            lesson_id=arg_str(args, "lesson_id"),
            label=arg_str(args, "label"),
            question=arg_str(args, "question"),
            stats=arg_flag(args, "stats"),
            tool=arg_str(args, "tool"),
            tool_args=tool_args,
            limit=arg_int(args, "limit", 20),
        )
    except ValueError as exc:
        return CommandResult.error(f"error: {exc}", code=2)
    text = format_guide_answer(payload) if arg_flag(args, "text") else json.dumps(payload, indent=2)
    return CommandResult(exit_code=0 if payload.get("ok") else 1, stdout=text + ("" if text.endswith("\n") else "\n"))


def _mcp_call(_store, args: argparse.Namespace) -> CommandResult:
    client = _guide_client(args)
    tool = arg_str(args, "tool").strip()
    if not tool:
        return CommandResult.error("error: --tool required (spdd_workSubgraph, …)", code=2)
    raw = arg_str(args, "json") or arg_str(args, "tool_json") or "{}"
    try:
        arguments = json.loads(raw)
    except json.JSONDecodeError as exc:
        return CommandResult.error(f"error: invalid JSON arguments: {exc}", code=2)
    payload = client.call_mcp_tool(tool, arguments)
    return CommandResult(exit_code=0 if payload.get("ok") else 1, stdout=json.dumps(payload, indent=2) + "\n")


def run(args: argparse.Namespace) -> CommandResult:
    from ..context_store import ContextStore

    store = ContextStore(project_from(args))
    handlers = {
        "persist-lesson": _persist_lesson,
        "persist-entry": _persist_entry,
        "accept": _accept,
        "show": _show,
        "parity": _parity,
        "digest": _digest,
        "retrieve": _retrieve,
        "eval-retrieve": _eval_retrieve,
        "metrics": _metrics,
        "coverage": _coverage,
        "backends": _backends,
        "guide-query": _guide_query,
        "mcp-call": _mcp_call,
    }
    handler = handlers.get(args.context_cmd)
    if handler is None:
        return CommandResult(exit_code=2)
    return handler(store, args)
