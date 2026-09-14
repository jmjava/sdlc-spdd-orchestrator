"""Link, roadmap, issue-tracker, commit-message, and sunset commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from ..commit_message import CommitMessageError, CommitMessageService
from ..issues import IssueSyncService
from ..sunset import SunsetError, SunsetService
from ..sync_local import LocalSyncService

from .state import _project


def cmd_links(args: argparse.Namespace) -> int:
    print(LocalSyncService(_project(args)).links_report(args.work_id), end="")
    return 0


def cmd_sync_links(args: argparse.Namespace) -> int:
    svc = LocalSyncService(_project(args))
    work_id = args.work_id or getattr(args, "work_id_pos", None)
    if args.repair:
        actions = svc.repair_links(work_id, dry_run=args.dry_run)
        if not actions:
            print("sync-links: nothing to repair")
        else:
            for a in actions:
                print(a)
        return 0
    findings = svc.check_links(work_id)
    if not findings:
        print("sync-links: no drift detected")
        return 0
    repairable = [f for f in findings if f.repairable]
    manual = [f for f in findings if not f.repairable]
    for f in findings:
        flag = "repairable" if f.repairable else "manual"
        print(f"[{flag}] {f.work_id}: {f.code} — {f.message}")
    if repairable:
        print(
            f"\n{len(findings)} finding(s) ({len(repairable)} repairable). "
            "Re-run with --repair to apply safe fixes."
        )
        return 1
    print(
        f"\n{len(manual)} manual finding(s) (TBD keys / planning gaps). "
        "Use `issues draft|push` or edit milestone ## Jira / ## GitHub."
    )
    return 0


def cmd_sync_roadmap(args: argparse.Namespace) -> int:
    block = LocalSyncService(_project(args)).sync_roadmap(
        roadmap=args.roadmap, dry_run=args.dry_run
    )
    if args.dry_run:
        print(block)
    else:
        print(f"Updated {args.roadmap} SDLC-SPDD summary from canvases.")
    return 0


def cmd_issues(args: argparse.Namespace) -> int:
    svc = IssueSyncService(_project(args))
    action = args.issues_cmd
    if action == "draft":
        fmt = getattr(args, "format", "markdown") or "markdown"
        for draft in svc.draft(args.work_id, system=args.system):
            print(f"=== {draft.system} draft for {draft.work_id} ===")
            print(f"title: {draft.title}")
            print(f"labels: {', '.join(draft.labels) or '-'}")
            if draft.system == "jira":
                print(f"description_format: {draft.extra.get('description_format', 'adf')}")
                if fmt == "adf":
                    print("body (ADF):")
                    print(json.dumps(draft.extra.get("description_adf"), indent=2))
                elif fmt == "wiki":
                    print("body (wiki markup):")
                    print(draft.extra.get("description_wiki") or "")
                else:
                    print("body (markdown — source for ADF/wiki conversion):")
                    print(draft.body)
            else:
                print(f"extra: {draft.extra}")
                print("body:")
                print(draft.body)
            print()
        return 0
    if action == "push":
        if args.system == "both":
            print("issues push requires --system jira|github", file=sys.stderr)
            return 2
        desc_fmt = getattr(args, "description_format", None)
        print(
            svc.push(
                args.work_id,
                args.system,
                apply=args.apply,
                description_format=desc_fmt,
            )
        )
        return 0
    if action == "pull":
        if args.system == "both":
            print("issues pull requires --system jira|github", file=sys.stderr)
            return 2
        print(svc.pull(args.work_id, args.system, apply=args.apply))
        return 0
    if action == "upload-adf":
        issue_key = getattr(args, "issue", None) or args.work_id
        adf_file = getattr(args, "adf_file", None)
        if not adf_file:
            print("issues upload-adf requires --file PATH", file=sys.stderr)
            return 2
        print(
            svc.upload_adf(
                issue_key,
                Path(adf_file),
                apply=args.apply,
                description_format=getattr(args, "description_format", None),
            )
        )
        return 0
    if action == "download-adf":
        issue_key = getattr(args, "issue", None) or args.work_id
        adf_file = getattr(args, "adf_file", None)
        print(
            svc.download_adf(
                issue_key,
                adf_path=Path(adf_file) if adf_file else None,
                apply=args.apply,
            )
        )
        return 0
    if action == "link":
        jira_key = getattr(args, "jira_key", None) or ""
        if not jira_key:
            print("issues link requires JIRA-KEY positional argument", file=sys.stderr)
            return 2
        result = svc.link_jira_local(
            args.work_id,
            jira_key,
            summary=getattr(args, "summary", None) or None,
            issue_type=getattr(args, "issue_type", None) or None,
            apply=args.apply,
        )
        for line in result.get("actions") or []:
            print(line)
        if not args.apply:
            print("\nRe-run with --apply to write local links.")
        return 0
    return 2


def cmd_commit_message(args: argparse.Namespace) -> int:
    svc = CommitMessageService(_project(args))
    try:
        if args.json:
            print(
                svc.report_json(
                    base=args.base,
                    work_id=args.work_id or "",
                    hint=args.hint or "",
                    max_diff_chars=args.max_diff,
                ),
                end="",
            )
        else:
            print(
                svc.report_text(
                    base=args.base,
                    work_id=args.work_id or "",
                    hint=args.hint or "",
                    max_diff_chars=args.max_diff,
                ),
                end="",
            )
    except CommitMessageError as exc:
        print(f"commit-message: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_sunset(args: argparse.Namespace) -> int:
    svc = SunsetService(_project(args))
    try:
        if args.json:
            print(
                svc.report_json(
                    args.work_id or None,
                    apply=bool(args.apply),
                    accept=bool(args.accept),
                ),
                end="",
            )
        else:
            print(
                svc.report_text(
                    args.work_id or None,
                    apply=bool(args.apply),
                    accept=bool(args.accept),
                ),
                end="",
            )
    except SunsetError as exc:
        print(f"sunset: {exc}", file=sys.stderr)
        return 1
    return 0
