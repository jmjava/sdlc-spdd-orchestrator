"""sdlc-engine issues."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
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
    iss.add_argument("--file", dest="adf_file", help="For upload-adf/download-adf: path to ADF JSON file")
    iss.add_argument(
        "--issue",
        help="For upload-adf/download-adf: Jira issue key (defaults to work_id positional)",
    )
    iss.add_argument("--summary", default=None, help="For link: optional local Summary bullet")
    iss.add_argument("--issue-type", dest="issue_type", default=None, help="For link: optional local Issue type bullet")
    iss.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually create/update remote issue, write pulled milestone fields, "
            "or overwrite local ADF on download-adf (default is dry-run)"
        ),
    )
    iss.set_defaults(func=run)


def _draft_body(draft, fmt: str) -> list[str]:
    lines = [f"=== {draft.system} draft for {draft.work_id} ===", f"title: {draft.title}"]
    lines.append(f"labels: {', '.join(draft.labels) or '-'}")
    if draft.system != "jira":
        lines.extend([f"extra: {draft.extra}", "body:", draft.body, ""])
        return lines
    lines.append(f"description_format: {draft.extra.get('description_format', 'adf')}")
    if fmt == "adf":
        lines.extend(["body (ADF):", json.dumps(draft.extra.get("description_adf"), indent=2), ""])
    elif fmt == "wiki":
        lines.extend(["body (wiki markup):", draft.extra.get("description_wiki") or "", ""])
    else:
        lines.extend(["body (markdown — source for ADF/wiki conversion):", draft.body, ""])
    return lines


def _draft(svc, args: argparse.Namespace) -> CommandResult:
    fmt = getattr(args, "format", "markdown") or "markdown"
    lines: list[str] = []
    for draft in svc.draft(args.work_id, system=args.system):
        lines.extend(_draft_body(draft, fmt))
    return CommandResult.ok("\n".join(lines).rstrip("\n"))


def _push(svc, args: argparse.Namespace) -> CommandResult:
    if args.system == "both":
        return CommandResult.error("issues push requires --system jira|github", code=2)
    return CommandResult.ok(
        str(svc.push(args.work_id, args.system, apply=args.apply, description_format=getattr(args, "description_format", None)))
    )


def _pull(svc, args: argparse.Namespace) -> CommandResult:
    if args.system == "both":
        return CommandResult.error("issues pull requires --system jira|github", code=2)
    return CommandResult.ok(str(svc.pull(args.work_id, args.system, apply=args.apply)))


def _upload_adf(svc, args: argparse.Namespace) -> CommandResult:
    issue_key = getattr(args, "issue", None) or args.work_id
    adf_file = getattr(args, "adf_file", None)
    if not adf_file:
        return CommandResult.error("issues upload-adf requires --file PATH", code=2)
    return CommandResult.ok(
        str(
            svc.upload_adf(
                issue_key,
                Path(adf_file),
                apply=args.apply,
                description_format=getattr(args, "description_format", None),
            )
        )
    )


def _download_adf(svc, args: argparse.Namespace) -> CommandResult:
    issue_key = getattr(args, "issue", None) or args.work_id
    adf_file = getattr(args, "adf_file", None)
    return CommandResult.ok(
        str(svc.download_adf(issue_key, adf_path=Path(adf_file) if adf_file else None, apply=args.apply))
    )


def _link(svc, args: argparse.Namespace) -> CommandResult:
    jira_key = getattr(args, "jira_key", None) or ""
    if not jira_key:
        return CommandResult.error("issues link requires JIRA-KEY positional argument", code=2)
    result = svc.link_jira_local(
        args.work_id,
        jira_key,
        summary=getattr(args, "summary", None) or None,
        issue_type=getattr(args, "issue_type", None) or None,
        apply=args.apply,
    )
    lines = list(result.get("actions") or [])
    if not args.apply:
        lines.append("\nRe-run with --apply to write local links.")
    return CommandResult.ok("\n".join(lines))


def run(args: argparse.Namespace) -> CommandResult:
    from ..issues import IssueSyncService

    svc = IssueSyncService(project_from(args))
    handlers = {
        "draft": _draft,
        "push": _push,
        "pull": _pull,
        "upload-adf": _upload_adf,
        "download-adf": _download_adf,
        "link": _link,
    }
    handler = handlers.get(args.issues_cmd)
    if handler is None:
        return CommandResult(exit_code=2)
    return handler(svc, args)
