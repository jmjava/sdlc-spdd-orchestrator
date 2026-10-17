"""sdlc-engine template."""

from __future__ import annotations

import argparse
import json

from .result import CommandResult
from .util import project_from


def register(sub: argparse._SubParsersAction) -> None:
    tmpl = sub.add_parser("template", help="ADF template library: list/render/validate combos (header/body/footer)")
    tmpl_sub = tmpl.add_subparsers(dest="template_cmd", required=True)
    tl = tmpl_sub.add_parser("list", help="List stock combo manifests")
    tl.add_argument("--json", action="store_true")
    tl.set_defaults(func=run)
    tmpl_sub.add_parser("validate", help="Validate stock combo manifests + ADF schema").set_defaults(func=run)
    tr = tmpl_sub.add_parser("render", help="Render planning artifacts for a Work ID into ADF JSON")
    tr.add_argument("--work-id", required=True, help="Work ID to bind variables from")
    tr.add_argument("--combo", default="", help="Combo id (feature|spike|bug); default: infer from Work ID prefix")
    tr.add_argument("--type", default="", help="Optional work-type override (feature|spike|bug|…)")
    tr.add_argument("-o", "--output", help="Write ADF JSON to this path (relative to --root unless absolute)")
    tr.add_argument("--json", action="store_true", help="Emit full RenderResult JSON")
    tr.set_defaults(func=run)


def _list(lib, args: argparse.Namespace) -> CommandResult:
    combos = [c.to_dict() for c in lib.list_combos()]
    if args.json:
        return CommandResult.ok(json.dumps({"ok": True, "combos": combos}, indent=2))
    if not combos:
        return CommandResult()
    lines = [f"{c['id']}\t{c['title']}\tparts={','.join(c['parts'])}" for c in combos]
    return CommandResult.ok("\n".join(lines))


def _validate(lib, _args: argparse.Namespace) -> CommandResult:
    from ..adf_templates import TemplateError

    combos = lib.list_combos()
    errors: list[str] = []
    for combo in combos:
        try:
            lib.load_combo(combo.id)
        except TemplateError as exc:
            errors.append(str(exc))
    try:
        sample = {"type": "doc", "version": 1, "content": [{"type": "paragraph"}]}
        errors.extend(lib.validate_adf(sample))
    except TemplateError as exc:
        errors.append(str(exc))
    if errors:
        return CommandResult(exit_code=1, stdout=json.dumps({"ok": False, "errors": errors}, indent=2) + "\n")
    return CommandResult.ok(json.dumps({"ok": True, "combos": len(combos)}, indent=2))


def _render(lib, args: argparse.Namespace) -> CommandResult:
    work_id = (args.work_id or "").strip()
    if not work_id:
        return CommandResult.error("template render requires --work-id")
    combo_id = (args.combo or "").strip() or lib.suggest_combo(work_id, getattr(args, "type", "") or "")
    result = lib.render(
        project_from(args),
        work_id,
        combo_id,
        work_type=getattr(args, "type", "") or "",
        output=args.output,
    )
    if args.json:
        return CommandResult.ok(json.dumps(result.to_dict(), indent=2))
    if args.output:
        return CommandResult.ok(str(result.output_path))
    return CommandResult.ok(json.dumps(result.adf, indent=2))


def run(args: argparse.Namespace) -> CommandResult:
    from ..adf_templates import AdfTemplateLibrary, TemplateError

    lib = AdfTemplateLibrary()
    handlers = {"list": _list, "validate": _validate, "render": _render}
    handler = handlers.get(args.template_cmd)
    if handler is None:
        return CommandResult.error(f"unknown template command: {args.template_cmd}")
    try:
        return handler(lib, args)
    except (TemplateError, FileNotFoundError, OSError) as exc:
        return CommandResult.error(f"sdlc-engine template: {exc}")
