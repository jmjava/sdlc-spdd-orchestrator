"""Flask application factory for the ADF WYSIWYG viewer."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

from sdlc_engine.jira_format import adf_to_markdown, markdown_to_adf

from .adf_html import adf_to_html
from .html_adf import html_to_adf
from .pages import EDIT_TEMPLATE, INDEX_TEMPLATE
from .store import AdfStore, AdfStoreError


def create_app(
    root: Path | str,
    *,
    upload_adf: Callable[..., str] | None = None,
    download_adf: Callable[..., str] | None = None,
    gh_runner: Callable[..., Any] | None = None,
) -> Any:
    """Create the Flask app.

    ``root`` is the default browse start (usually cwd). Paths may be absolute
    anywhere on the local filesystem — this tool is intended for local use only.
    ``gh_runner`` is the injectable gh CLI transport (see ``sdlc_engine.issues``)
    used by the GitHub Issue pull/push endpoints; tests pass a fake.
    """
    try:
        from flask import Flask, jsonify, redirect, render_template_string, request
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Flask is required for the ADF viewer. Install with: pip install -e '.[viewer]'"
        ) from exc

    root_path = Path(root).expanduser().resolve()
    store = AdfStore(root_path)
    store.ensure_dir()

    app = Flask(__name__)
    app.config["ADF_ROOT"] = str(root_path)

    def _issue_service():
        from sdlc_engine.issues import IssueSyncService
        from sdlc_engine.project import Project

        return IssueSyncService(Project.resolve(root_path), gh_runner=gh_runner)

    def _uploader() -> Callable[..., str]:
        if upload_adf is not None:
            return upload_adf

        svc = _issue_service()

        def _call(
            issue_key: str,
            adf_path: Path,
            *,
            apply: bool = False,
            description_format: str | None = None,
        ) -> str:
            return svc.upload_adf(
                issue_key,
                adf_path,
                apply=apply,
                description_format=description_format,
            )

        return _call

    def _downloader() -> Callable[..., str]:
        if download_adf is not None:
            return download_adf

        svc = _issue_service()

        def _call(
            issue_key: str,
            adf_path: Path,
            *,
            apply: bool = False,
        ) -> str:
            return svc.download_adf(
                issue_key,
                adf_path=adf_path,
                apply=apply,
            )

        return _call

    def _edit_href(abs_path: str) -> str:
        return "/edit?path=" + quote(abs_path, safe="")

    def _path_arg() -> str:
        """Path from query ``path=`` or JSON body."""
        if request.method in {"POST", "PUT", "PATCH"}:
            body = request.get_json(silent=True) or {}
            if isinstance(body, dict) and body.get("path"):
                return str(body["path"]).strip()
        return (request.args.get("path") or "").strip()

    @app.get("/")
    def index():
        files = store.list_files()
        return render_template_string(
            INDEX_TEMPLATE,
            files=files,
            start_path=str(store.adf_dir),
            root_label=str(root_path),
        )

    @app.get("/edit")
    def edit_query():
        path = _path_arg()
        if not path:
            return redirect("/")
        try:
            abs_path = store.display_path(path)
            doc = store.load_path(abs_path)
        except AdfStoreError as exc:
            return str(exc), 404
        html = adf_to_html(doc)
        issue_key = store.issue_key_from_name(abs_path)
        return render_template_string(
            EDIT_TEMPLATE,
            filename=abs_path,
            files=store.list_files(),
            preview_html=html,
            adf_json=json.dumps(doc, indent=2, ensure_ascii=False),
            issue_key=issue_key,
            jira_base=os.environ.get("JIRA_BASE_URL")
            or os.environ.get("JIRA_URL")
            or "",
            start_path=str(Path(abs_path).parent),
            root_label=str(root_path),
        )

    @app.get("/edit/<path:relpath>")
    def edit_legacy(relpath: str):
        """Compatibility: /edit/ORCH-1.adf.json → adf/ file under start root."""
        return redirect(_edit_href(store.display_path(relpath)))

    @app.get("/api/browse")
    def api_browse():
        path = request.args.get("path") or str(store.adf_dir)
        try:
            listing = store.browse(path)
            return jsonify({"ok": True, **listing})
        except AdfStoreError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/create")
    def api_create():
        body = request.get_json(silent=True) or {}
        path = (body.get("path") or "").strip()
        title = body.get("title")
        if not path:
            return jsonify({"ok": False, "error": "path required"}), 400
        try:
            created = store.create_path(path, title=title if isinstance(title, str) else None)
            abs_s = str(created.resolve())
            return jsonify(
                {
                    "ok": True,
                    "path": abs_s,
                    "edit_url": _edit_href(abs_s),
                }
            )
        except AdfStoreError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/adf")
    def api_get_adf():
        path = _path_arg()
        if not path:
            return jsonify({"ok": False, "error": "path required"}), 400
        try:
            return jsonify(store.load_path(path))
        except AdfStoreError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/adf/<path:relpath>")
    def api_get_adf_legacy(relpath: str):
        try:
            return jsonify(store.load_path(relpath))
        except AdfStoreError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/render")
    def api_render():
        try:
            body = request.get_json(force=True, silent=False)
            if not isinstance(body, dict):
                return jsonify({"ok": False, "error": "JSON object required"}), 400
            warnings: list[str] = []
            html = adf_to_html(body, collect_warnings=warnings)
            return jsonify({"ok": True, "html": html, "warnings": warnings})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/html-to-adf")
    def api_html_to_adf():
        try:
            body = request.get_json(force=True, silent=False) or {}
            html = body.get("html") if isinstance(body, dict) else None
            if html is None and isinstance(body, dict) and "content" not in body:
                html = request.get_data(as_text=True)
            if not isinstance(html, str):
                return jsonify({"ok": False, "error": "expected {html: string}"}), 400
            doc = html_to_adf(html)
            return jsonify({"ok": True, "adf": doc})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/save")
    def api_save():
        try:
            body = request.get_json(force=True, silent=True)
            if body is None:
                body = json.loads(request.get_data(as_text=True))
            if not isinstance(body, dict):
                return jsonify({"ok": False, "error": "JSON object required"}), 400
            path = (body.get("path") or "").strip()
            if not path:
                return jsonify({"ok": False, "error": "path required"}), 400
            if "html" in body and "type" not in body:
                doc = html_to_adf(str(body["html"]))
            else:
                doc = {k: v for k, v in body.items() if k != "path"}
                if "type" not in doc:
                    return jsonify({"ok": False, "error": "ADF doc or html required"}), 400
            saved = store.save_path(path, doc)
            return jsonify({"ok": True, "path": str(saved.resolve()), "adf": doc})
        except (AdfStoreError, json.JSONDecodeError, ValueError, TypeError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/save/<path:relpath>")
    def api_save_legacy(relpath: str):
        """Compatibility wrapper for older clients."""
        try:
            body = request.get_json(force=True, silent=True)
            if body is None:
                body = json.loads(request.get_data(as_text=True))
            if isinstance(body, dict) and "html" in body and "type" not in body:
                doc = html_to_adf(str(body["html"]))
            else:
                doc = body
            saved = store.save_path(relpath, doc)
            return jsonify({"ok": True, "path": str(saved.resolve()), "adf": doc})
        except (AdfStoreError, json.JSONDecodeError, ValueError, TypeError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    def _sync_response(body: dict[str, Any]):
        path = (body.get("path") or "").strip()
        if not path:
            return jsonify({"ok": False, "error": "path required"}), 400
        try:
            abs_path = store.display_path(path)
            store.load_path(abs_path)
            adf_path = store.resolve_path(abs_path)
        except AdfStoreError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        apply = bool(body.get("apply"))
        fmt = (body.get("description_format") or body.get("format") or "adf").strip().lower()
        if fmt not in {"adf", "wiki"}:
            return jsonify({"ok": False, "error": "description_format must be adf|wiki"}), 400
        issue_key = (body.get("issue_key") or store.issue_key_from_name(abs_path)).strip()
        cmd = (
            f"./scripts/sdlc.sh issues upload-adf --file {abs_path} "
            f"--issue-key {issue_key} --description-format {fmt}"
            + (" --apply" if apply else "")
        )
        if not apply:
            message = (
                f"[prepare] file={abs_path} issue={issue_key} format={fmt}\n"
                "No network write. Re-run with {\"apply\": true} or add --apply on the CLI.\n"
                f"Suggested:\n{cmd}"
            )
            try:
                message = _uploader()(
                    issue_key, adf_path, apply=False, description_format=fmt
                )
            except Exception as exc:  # noqa: BLE001
                message = f"{message}\n\n(engine dry-run skipped: {exc})"
            return jsonify(
                {
                    "ok": True,
                    "apply": False,
                    "issue_key": issue_key,
                    "description_format": fmt,
                    "message": message,
                    "cli": cmd,
                }
            )
        try:
            message = _uploader()(
                issue_key, adf_path, apply=True, description_format=fmt
            )
            return jsonify(
                {
                    "ok": True,
                    "apply": True,
                    "issue_key": issue_key,
                    "description_format": fmt,
                    "message": message,
                    "cli": cmd,
                }
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify(
                {
                    "ok": False,
                    "apply": True,
                    "issue_key": issue_key,
                    "description_format": fmt,
                    "error": str(exc),
                    "cli": cmd,
                }
            ), 400

    @app.post("/api/sync")
    def api_sync():
        return _sync_response(request.get_json(silent=True) or {})

    @app.post("/api/sync/<path:relpath>")
    def api_sync_legacy(relpath: str):
        body = dict(request.get_json(silent=True) or {})
        body["path"] = store.display_path(relpath)
        return _sync_response(body)

    def _download_response(body: dict[str, Any]):
        path = (body.get("path") or "").strip()
        apply = bool(body.get("apply"))
        issue_key = (body.get("issue_key") or "").strip()
        if path:
            try:
                abs_path = store.display_path(path)
                adf_path = store.resolve_path(abs_path)
                if not issue_key:
                    issue_key = store.issue_key_from_name(abs_path)
            except AdfStoreError as exc:
                return jsonify({"ok": False, "error": str(exc)}), 400
        else:
            if not issue_key:
                return jsonify(
                    {"ok": False, "error": "issue_key or path required"}
                ), 400
            abs_path = str((root_path / "adf" / f"{issue_key}.adf.json").resolve())
            adf_path = Path(abs_path)
        if not issue_key:
            return jsonify({"ok": False, "error": "issue_key required"}), 400
        cmd = (
            f"./scripts/sdlc.sh issues download-adf {issue_key} --file {abs_path}"
            + (" --apply" if apply else "")
        )
        if not apply:
            message = (
                f"[prepare] file={abs_path} issue={issue_key}\n"
                "No local write. Re-run with {\"apply\": true} or add --apply on the CLI.\n"
                f"Suggested:\n{cmd}"
            )
            try:
                message = _downloader()(issue_key, adf_path, apply=False)
            except Exception as exc:  # noqa: BLE001
                message = f"{message}\n\n(engine dry-run skipped: {exc})"
            return jsonify(
                {
                    "ok": True,
                    "apply": False,
                    "direction": "jira-to-local",
                    "issue_key": issue_key,
                    "path": abs_path,
                    "message": message,
                    "cli": cmd,
                }
            )
        try:
            message = _downloader()(issue_key, adf_path, apply=True)
            adf_doc = None
            try:
                adf_doc = store.load_path(abs_path)
            except AdfStoreError:
                pass
            return jsonify(
                {
                    "ok": True,
                    "apply": True,
                    "direction": "jira-to-local",
                    "issue_key": issue_key,
                    "path": abs_path,
                    "message": message,
                    "cli": cmd,
                    "adf": adf_doc,
                    "html": adf_to_html(adf_doc) if adf_doc else None,
                }
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify(
                {
                    "ok": False,
                    "apply": True,
                    "direction": "jira-to-local",
                    "issue_key": issue_key,
                    "path": abs_path,
                    "error": str(exc),
                    "cli": cmd,
                }
            ), 400

    @app.post("/api/download")
    def api_download():
        return _download_response(request.get_json(silent=True) or {})

    _GITHUB_NOTE = "GitHub stores markdown; complex ADF formatting may flatten."

    @app.post("/api/github/pull")
    def api_github_pull():
        """Fetch a GitHub issue body (markdown → ADF) into the editor.

        Dry-run previews only; ``apply`` also writes the ADF to ``path``.
        """
        body = request.get_json(silent=True) or {}
        issue = str(body.get("issue") or "").strip()
        if not issue:
            return jsonify(
                {"ok": False, "error": "issue required (123, #123, or owner/repo#123)"}
            ), 400
        repo = str(body.get("repo") or "").strip() or None
        path = str(body.get("path") or "").strip()
        apply = bool(body.get("apply"))
        if apply and not path:
            return jsonify({"ok": False, "error": "path required to apply pull"}), 400
        try:
            data = _issue_service().fetch_github_issue(issue, repo=repo)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:  # noqa: BLE001 — gh/transport errors are 4xx, not 500
            return jsonify({"ok": False, "error": str(exc)}), 400
        markdown = str(data.get("body") or "")
        adf = markdown_to_adf(markdown)
        number = data.get("number")
        message = (
            f"GitHub #{number}: {data.get('title')} [{data.get('state')}]\n"
            f"URL: {data.get('url')}\n"
        )
        saved: str | None = None
        if apply:
            try:
                saved = str(store.save_path(path, adf).resolve())
                message += f"Wrote {saved} from issue body (markdown → ADF).\n"
            except AdfStoreError as exc:
                return jsonify({"ok": False, "error": str(exc)}), 400
        else:
            message += "Dry-run only; pass {\"apply\": true} to overwrite the local file.\n"
        return jsonify(
            {
                "ok": True,
                "apply": apply,
                "direction": "github-to-local",
                "issue": issue,
                "number": number,
                "repo": data.get("repo") or "",
                "url": data.get("url") or "",
                "title": data.get("title") or "",
                "state": data.get("state") or "",
                "markdown": markdown,
                "adf": adf,
                "html": adf_to_html(adf),
                "path": saved,
                "note": _GITHUB_NOTE,
                "message": message,
            }
        )

    @app.post("/api/github/push")
    def api_github_push():
        """Push editor content (ADF → markdown) back to a GitHub issue body.

        Dry-run returns the markdown preview; ``apply`` runs ``gh issue edit``.
        """
        body = request.get_json(silent=True) or {}
        issue = str(body.get("issue") or "").strip()
        if not issue:
            return jsonify(
                {"ok": False, "error": "issue required (123, #123, or owner/repo#123)"}
            ), 400
        repo = str(body.get("repo") or "").strip() or None
        path = str(body.get("path") or "").strip()
        apply = bool(body.get("apply"))
        adf_doc = body.get("adf")
        svc = _issue_service()
        try:
            svc.parse_github_issue_ref(issue)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        try:
            if isinstance(adf_doc, dict):
                from sdlc_engine.jira_format import load_adf_document

                doc = load_adf_document(adf_doc)
            elif path:
                doc = store.load_path(path)
            else:
                return jsonify({"ok": False, "error": "path or adf required"}), 400
        except (AdfStoreError, ValueError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        markdown = adf_to_markdown(doc)
        if not apply:
            return jsonify(
                {
                    "ok": True,
                    "apply": False,
                    "direction": "local-to-github",
                    "issue": issue,
                    "markdown": markdown,
                    "note": _GITHUB_NOTE,
                    "message": (
                        f"[dry-run] would update GitHub issue {issue} body "
                        f"(ADF → markdown, {len(markdown)} chars).\n"
                        f"{_GITHUB_NOTE}\n"
                        "Re-run with {\"apply\": true} to push.\n\n"
                        "--- markdown preview ---\n" + markdown
                    ),
                }
            )
        try:
            message = svc.update_github_issue_body(issue, markdown, repo=repo)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:  # noqa: BLE001 — gh/transport errors are 4xx, not 500
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify(
            {
                "ok": True,
                "apply": True,
                "direction": "local-to-github",
                "issue": issue,
                "markdown": markdown,
                "note": _GITHUB_NOTE,
                "message": message,
            }
        )

    return app


def run_viewer(
    root: Path | str,
    *,
    host: str = "127.0.0.1",
    port: int = 5050,
    debug: bool = False,
) -> None:
    app = create_app(root)
    root_p = Path(root).expanduser().resolve()
    print(f"Start directory: {root_p}")
    print(f"Default ADF folder: {root_p / 'adf'}")
    print(f"Browse: any local path (local-only tool)")
    print(f"Open: http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)
