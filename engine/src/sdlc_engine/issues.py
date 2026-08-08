"""Create/update Jira or GitHub issues from requirements/milestones drafts."""

from __future__ import annotations

import base64
import difflib
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .jira_format import (
    adf_to_markdown,
    adf_to_wiki,
    build_jira_markdown,
    load_adf_document,
    load_adf_file,
    markdown_to_adf,
    markdown_to_wiki,
)
from .links import (
    _JIRA_KEY_RE,
    collect_links,
    parse_milestone_requirement,
    set_milestone_bullet,
    set_milestone_subsection,
)
from .project import Project
from .sync_local import LocalSyncService

# Optional hooks for tests (inject fake gh / HTTP).
GhRunner = Callable[[list[str], Path], subprocess.CompletedProcess]
UrlOpener = Callable[..., object]

# "123", "#123", or "owner/repo#123"
_GH_ISSUE_REF_RE = re.compile(r"^(?:(?P<repo>[\w.-]+/[\w.-]+)#)?#?(?P<num>\d+)$")


def _repo_from_remote_url(url: str) -> str:
    """owner/repo from an https or ssh GitHub remote URL ('' if not GitHub-shaped)."""
    m = re.search(r"github\.com[:/]+([\w.-]+/[\w.-]+?)(?:\.git)?/?\s*$", (url or "").strip())
    return m.group(1) if m else ""


@dataclass
class IssueDraft:
    system: str  # jira | github
    work_id: str
    title: str
    body: str
    labels: list[str]
    extra: dict


def _default_gh_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


class IssueSyncService:
    def __init__(
        self,
        project: Project | None = None,
        *,
        gh_runner: GhRunner | None = None,
        urlopen: UrlOpener | None = None,
    ) -> None:
        self.project = project or Project.resolve()
        self.local = LocalSyncService(self.project)
        self._gh_runner = gh_runner or _default_gh_runner
        self._urlopen = urlopen or urllib.request.urlopen

    def _github_repo(self) -> str:
        return (
            os.environ.get("SDLC_GITHUB_REPO")
            or os.environ.get("GH_REPO")
            or ""
        ).strip()

    def _gh_cmd(self, *parts: str) -> list[str]:
        cmd = ["gh", *parts]
        repo = self._github_repo()
        if repo:
            # Insert --repo after the gh subcommand group (issue create/view/close).
            # gh accepts: gh issue create --repo OWNER/NAME ...
            if len(cmd) >= 3 and cmd[1] == "issue":
                cmd[3:3] = ["--repo", repo]
            else:
                cmd.extend(["--repo", repo])
        return cmd

    def draft(self, work_id: str, system: str = "both") -> list[IssueDraft]:
        req = self.project.milestone_path(work_id)
        if not req.is_file():
            raise FileNotFoundError(f"missing requirements/milestones/{work_id}.md")
        parsed = parse_milestone_requirement(req)
        summary = parsed.get("jira_summary") or parsed.get("summary") or work_id
        summary = " ".join(summary.split())
        drafts: list[IssueDraft] = []
        systems = ["jira", "github"] if system == "both" else [system]
        if "jira" in systems:
            req_rel = f"requirements/milestones/{work_id}.md"
            body_md = build_jira_markdown(
                work_id=work_id,
                summary=summary,
                description=parsed.get("jira_description") or parsed.get("summary") or "",
                acceptance=parsed.get("jira_acceptance") or "",
                business_value=parsed.get("jira_business_value") or "",
                scope_in=parsed.get("jira_scope_in") or "",
                scope_out=parsed.get("jira_scope_out") or "",
                requirement_rel=req_rel,
            )
            labels = [x.strip() for x in (parsed.get("jira_labels") or "").split(",") if x.strip()]
            base = self._jira_base_url()
            fmt = self._jira_description_format(base)
            adf = markdown_to_adf(body_md)
            # Always precompute wiki via ADF→wiki shim for draft --format wiki.
            wiki = adf_to_wiki(adf)
            extra = {
                "issuetype": parsed.get("jira_type") or "Story",
                "key": parsed.get("jira_key") or "",
                "project": os.environ.get("JIRA_PROJECT", ""),
                "components": parsed.get("jira_components") or "",
                "description_format": fmt,
                "description_wiki": wiki,
                "description_adf": adf,
            }
            drafts.append(
                IssueDraft(
                    system="jira",
                    work_id=work_id,
                    title=summary[:255] or work_id,
                    body=body_md,
                    labels=labels,
                    extra=extra,
                )
            )
        if "github" in systems:
            title = parsed.get("github_title") or summary or work_id
            body = parsed.get("github_body") or parsed.get("summary") or ""
            body = (
                body.strip()
                + f"\n\n---\nWork ID: `{work_id}`\nRequirement: `requirements/milestones/{work_id}.md`\n"
            )
            labels = [x.strip() for x in (parsed.get("github_labels") or "").split(",") if x.strip()]
            drafts.append(
                IssueDraft(
                    system="github",
                    work_id=work_id,
                    title=title[:256],
                    body=body.strip(),
                    labels=labels,
                    extra={"number": parsed.get("github_number") or ""},
                )
            )
        return drafts

    def push(
        self,
        work_id: str,
        system: str,
        *,
        apply: bool = False,
        description_format: str | None = None,
    ) -> str:
        if system not in {"jira", "github"}:
            raise ValueError("system must be jira or github")
        drafts = self.draft(work_id, system=system)
        draft = drafts[0]
        if system == "jira" and description_format:
            fmt = description_format.strip().lower()
            if fmt not in {"adf", "wiki", "plain"}:
                raise ValueError("description_format must be adf|wiki|plain")
            draft.extra["description_format"] = fmt
            if fmt == "wiki":
                adf = draft.extra.get("description_adf") or markdown_to_adf(draft.body)
                draft.extra["description_wiki"] = adf_to_wiki(adf)
        if system == "github" and draft.extra.get("number"):
            msg = (
                f"GitHub issue already linked as #{draft.extra['number']}; skip create."
            )
            return f"[dry-run] {msg}" if not apply else msg
        if not apply:
            return self._format_dry_run(draft)
        if system == "github":
            return self._push_github(draft)
        return self._push_jira(draft)

    def _format_dry_run(self, draft: IssueDraft) -> str:
        key = draft.extra.get("key") or ""
        updating = bool(draft.system == "jira" and key and _JIRA_KEY_RE.match(str(key)))
        action = "update" if updating else "create"
        lines = [
            f"[dry-run] would {action} {draft.system} issue for {draft.work_id}",
            f"title: {draft.title}",
            f"labels: {', '.join(draft.labels) or '-'}",
        ]
        if draft.system == "jira":
            fmt = draft.extra.get("description_format") or "adf"
            lines.append(
                f"description_format: {fmt} "
                "(adf = raw ADF JSON; wiki = optional ADF→wiki shim)"
            )
            if updating:
                lines.append(f"existing_key: {key}")
            lines.append("body (markdown source):")
            lines.append(draft.body)
            if fmt == "adf":
                lines.append("body (ADF JSON — sent as-is, no wiki conversion):")
                lines.append(json.dumps(draft.extra.get("description_adf"), indent=2))
            else:
                lines.append("body (wiki markup via ADF→wiki shim):")
                lines.append(str(draft.extra.get("description_wiki") or ""))
        else:
            lines.append(
                f"extra: {json.dumps({k: v for k, v in draft.extra.items() if k != 'description_adf'})}"
            )
            lines.append("body:")
            lines.append(draft.body)
        lines.extend(
            [
                "",
                "Re-run with --apply to execute (explicit CLI only; no automatic sync).",
            ]
        )
        return "\n".join(lines)

    def _jira_base_url(self) -> str:
        return (
            os.environ.get("JIRA_BASE_URL")
            or os.environ.get("JIRA_URL")
            or ""
        ).rstrip("/")

    def _jira_api_version(self, base: str) -> str:
        explicit = os.environ.get("JIRA_API_VERSION", "").strip()
        if explicit in {"2", "3"}:
            return explicit
        # Cloud hosts need v3 + ADF; Server/DC often still on v2 wiki.
        if "atlassian.net" in base.lower():
            return "3"
        return os.environ.get("JIRA_API_VERSION_DEFAULT", "3")

    def _jira_description_format(self, base: str) -> str:
        """Return adf|wiki|plain.

        Default is **raw ADF** for API v3 (Cloud). Wiki is opt-in via
        ``JIRA_DESCRIPTION_FORMAT=wiki`` (runs the ADF→wiki shim). There is no
        automatic ADF→wiki conversion unless that format is chosen or
        ``JIRA_DESCRIPTION_FALLBACK=1`` is set.
        """
        explicit = os.environ.get("JIRA_DESCRIPTION_FORMAT", "").strip().lower()
        if explicit in {"adf", "wiki", "plain"}:
            return explicit
        return "adf" if self._jira_api_version(base) == "3" else "wiki"

    def _jira_description_fallback_enabled(self) -> bool:
        # Default off: raw ADF must not silently become wiki on Cloud.
        return os.environ.get("JIRA_DESCRIPTION_FALLBACK", "0").strip() not in {
            "",
            "0",
            "false",
            "no",
            "off",
        }

    def _jira_description_payload(self, draft: IssueDraft, fmt: str):
        if fmt == "adf":
            return draft.extra.get("description_adf") or markdown_to_adf(draft.body)
        if fmt == "wiki":
            # Prefer ADF→wiki shim when ADF is available.
            adf = draft.extra.get("description_adf")
            if isinstance(adf, dict):
                return adf_to_wiki(adf)
            if draft.extra.get("description_wiki"):
                return draft.extra["description_wiki"]
            return markdown_to_wiki(draft.body)
        return draft.body

    def _jira_auth_mode(self) -> str:
        """basic (Cloud email+token) or bearer (Server/DC PAT)."""
        mode = os.environ.get("JIRA_AUTH_MODE", "").strip().lower()
        if mode in {"basic", "bearer"}:
            return mode
        # Heuristic: Cloud → basic; otherwise bearer PAT is common on Server/DC.
        base = self._jira_base_url().lower()
        if "atlassian.net" in base:
            return "basic"
        return os.environ.get("JIRA_AUTH_MODE_DEFAULT", "basic").strip().lower() or "basic"

    def _jira_request_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check",
        }
        token = os.environ.get("JIRA_API_TOKEN", "")
        email = os.environ.get("JIRA_EMAIL", "")
        mode = self._jira_auth_mode()
        if mode == "bearer":
            if not token:
                raise RuntimeError("Jira bearer auth requires JIRA_API_TOKEN")
            headers["Authorization"] = f"Bearer {token}"
            return headers
        if not (email and token):
            raise RuntimeError("Jira basic auth requires JIRA_EMAIL and JIRA_API_TOKEN")
        headers["Authorization"] = "Basic " + base64.b64encode(
            f"{email}:{token}".encode()
        ).decode()
        return headers

    def _push_github(self, draft: IssueDraft) -> str:
        if draft.extra.get("number"):
            return f"GitHub issue already linked as #{draft.extra['number']}; skip create."
        if self._gh_runner is _default_gh_runner and not shutil.which("gh"):
            raise RuntimeError("gh CLI not found; install GitHub CLI or use --dry-run")
        cmd = self._gh_cmd("issue", "create", "--title", draft.title, "--body", draft.body)
        for label in draft.labels:
            cmd.extend(["--label", label])
        proc = self._gh_runner(cmd, self.project.root)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gh issue create failed")
        url = proc.stdout.strip().splitlines()[-1].strip()
        num = ""
        if "/issues/" in url:
            num = url.rstrip("/").split("/issues/")[-1]
        req = self.project.milestone_path(draft.work_id)
        if num:
            set_milestone_bullet(req, "GitHub", "Number", num)
            set_milestone_bullet(req, "GitHub", "URL", url)
            set_milestone_bullet(req, "GitHub", "Title", draft.title)
        self.local.repair_links(draft.work_id)
        return f"Created GitHub issue {url}"

    def _jira_http(
        self,
        method: str,
        url: str,
        *,
        payload: dict | None = None,
    ) -> tuple[int, dict | str]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers=self._jira_request_headers(),
        )
        try:
            with self._urlopen(req, timeout=30) as resp:
                raw = resp.read()
                status = getattr(resp, "status", None)
                if status is None and hasattr(resp, "getcode"):
                    status = resp.getcode()
                if status is None:
                    status = 200
                if not raw:
                    return int(status), {}
                return int(status), json.loads(raw.decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"Jira {method} {url} failed ({exc.code}): {detail}") from exc

    def _push_jira(self, draft: IssueDraft) -> str:
        base = self._jira_base_url()
        project = draft.extra.get("project") or os.environ.get("JIRA_PROJECT", "")
        token = os.environ.get("JIRA_API_TOKEN", "")
        mode = self._jira_auth_mode()
        if not base or not token:
            raise RuntimeError(
                "Jira push requires JIRA_BASE_URL (or JIRA_URL) and JIRA_API_TOKEN"
            )
        if mode == "basic" and not os.environ.get("JIRA_EMAIL"):
            raise RuntimeError("Jira basic auth requires JIRA_EMAIL")
        existing = draft.extra.get("key") or ""
        updating = bool(existing and _JIRA_KEY_RE.match(existing))
        if not updating and not project:
            raise RuntimeError("Jira create requires JIRA_PROJECT")

        api_ver = self._jira_api_version(base)
        fmt = (draft.extra.get("description_format") or self._jira_description_format(base)).lower()
        description = self._jira_description_payload(draft, fmt)

        def _send(version: str, desc, *, update: bool) -> tuple[str, int]:
            if update:
                url = f"{base}/rest/api/{version}/issue/{existing}"
                payload = {"fields": {"summary": draft.title, "description": desc}}
                status, body = self._jira_http("PUT", url, payload=payload)
                # 204 No Content is success for many Server/DC installs.
                return existing, status
            url = f"{base}/rest/api/{version}/issue"
            fields: dict = {
                "project": {"key": project},
                "summary": draft.title,
                "description": desc,
                "issuetype": {"name": draft.extra.get("issuetype") or "Story"},
            }
            if draft.labels:
                fields["labels"] = draft.labels
            comps = draft.extra.get("components") or ""
            comp_names = [c.strip() for c in comps.split(",") if c.strip()]
            if comp_names:
                fields["components"] = [{"name": c} for c in comp_names]
            status, body = self._jira_http("POST", url, payload={"fields": fields})
            key = (body or {}).get("key", "") if isinstance(body, dict) else ""
            return str(key), status

        try:
            key, status = _send(api_ver, description, update=updating)
        except RuntimeError as exc:
            # Optional fallback only when explicitly enabled — never the default for ADF.
            msg = str(exc)
            can_fallback = (
                self._jira_description_fallback_enabled()
                and ("failed (400)" in msg or "failed (415)" in msg)
            )
            if not can_fallback:
                raise
            alt_fmt = "wiki" if fmt == "adf" else "adf"
            alt_ver = "2" if alt_fmt == "wiki" else "3"
            key, status = _send(
                alt_ver,
                self._jira_description_payload(draft, alt_fmt),
                update=updating,
            )
            fmt, api_ver = alt_fmt, alt_ver

        if key and not updating:
            set_milestone_bullet(self.project.milestone_path(draft.work_id), "Jira", "Key", key)
            set_milestone_bullet(
                self.project.milestone_path(draft.work_id), "Jira", "Summary", draft.title
            )
            self.local.repair_links(draft.work_id)
        elif updating:
            set_milestone_bullet(
                self.project.milestone_path(draft.work_id), "Jira", "Summary", draft.title
            )
            self.local.repair_links(draft.work_id)

        action = "Updated" if updating else "Created"
        return (
            f"{action} Jira issue {key} ({base}/browse/{key}) "
            f"[api=v{api_ver} description={fmt} auth={mode} http={status}]"
        )

    def upload_adf(
        self,
        issue_key: str,
        adf_path: Path,
        *,
        apply: bool = False,
        description_format: str | None = None,
    ) -> str:
        """Upload a raw ADF JSON file to an existing issue (explicit CLI only).

        Default description format is **raw ADF**. Pass ``description_format='wiki'``
        (or env ``JIRA_DESCRIPTION_FORMAT=wiki``) to run the ADF→wiki shim for
        Server/DC API v2.
        """
        if not _JIRA_KEY_RE.match(issue_key):
            raise ValueError(f"invalid Jira issue key: {issue_key}")
        adf = load_adf_file(Path(adf_path))
        base = self._jira_base_url()
        if not base or not os.environ.get("JIRA_API_TOKEN"):
            raise RuntimeError(
                "upload-adf requires JIRA_BASE_URL (or JIRA_URL) and JIRA_API_TOKEN"
            )
        fmt = (description_format or self._jira_description_format(base)).strip().lower()
        if fmt not in {"adf", "wiki"}:
            raise ValueError("upload-adf description_format must be adf|wiki")
        api_ver = "3" if fmt == "adf" else "2"
        # Allow override when operator knows their Server accepts ADF on v3.
        explicit_ver = os.environ.get("JIRA_API_VERSION", "").strip()
        if explicit_ver in {"2", "3"}:
            api_ver = explicit_ver
        description: dict | str = adf if fmt == "adf" else adf_to_wiki(adf)
        url = f"{base}/rest/api/{api_ver}/issue/{issue_key}"
        if not apply:
            preview = (
                json.dumps(description, indent=2)[:500]
                if isinstance(description, dict)
                else str(description)[:500]
            )
            return (
                f"[dry-run] would PUT {url}\n"
                f"description_format: {fmt} (raw ADF unless format=wiki)\n"
                f"auth_mode: {self._jira_auth_mode()}\n"
                f"preview:\n{preview}\n"
                "Re-run with --apply to update (explicit; no automatic sync)."
            )
        status, _body = self._jira_http(
            "PUT",
            url,
            payload={"fields": {"description": description}},
        )
        return (
            f"Updated Jira issue {issue_key} description "
            f"[api=v{api_ver} description={fmt} auth={self._jira_auth_mode()} http={status}]"
        )

    def _default_adf_path(self, issue_key: str) -> Path:
        return self.project.root / "adf" / f"{issue_key}.adf.json"

    def _resolve_adf_path(self, issue_key: str, adf_path: Path | None) -> Path:
        if adf_path is None:
            return self._default_adf_path(issue_key)
        path = Path(adf_path)
        if not path.is_absolute():
            path = self.project.root / path
        return path

    @staticmethod
    def _adf_pretty(doc: dict, *, sort_keys: bool = False) -> str:
        return json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=sort_keys) + "\n"

    def _adf_diff_report(self, local: dict | None, remote: dict) -> str:
        remote_pretty = self._adf_pretty(remote, sort_keys=True)
        if local is None:
            return (
                "local: (missing)\n"
                "remote vs local: remote-only (no local file)\n"
                "--- markdown preview (remote) ---\n"
                + adf_to_markdown(remote).rstrip()
                + "\n"
            )
        local_pretty = self._adf_pretty(local, sort_keys=True)
        equal = json.loads(local_pretty) == json.loads(remote_pretty)
        if equal:
            return "local: present\nremote vs local: identical (normalized JSON)\n"
        local_md = adf_to_markdown(local).splitlines(keepends=True)
        remote_md = adf_to_markdown(remote).splitlines(keepends=True)
        md_diff = "".join(
            difflib.unified_diff(
                local_md,
                remote_md,
                fromfile="local.md",
                tofile="remote.md",
                n=3,
            )
        )
        json_diff = "".join(
            difflib.unified_diff(
                local_pretty.splitlines(keepends=True),
                remote_pretty.splitlines(keepends=True),
                fromfile="local.adf.json",
                tofile="remote.adf.json",
                n=2,
            )
        )
        # Prefer a short markdown diff; fall back to JSON if markdown is identical.
        body = md_diff if md_diff.strip() else json_diff
        if len(body) > 4000:
            body = body[:4000] + "\n… (diff truncated)\n"
        return (
            "local: present\n"
            "remote vs local: differ\n"
            "--- diff ---\n"
            + body
        )

    def fetch_issue_adf(self, issue_key: str) -> dict:
        """GET issue description ADF from Jira Cloud (API v3 by default)."""
        if not _JIRA_KEY_RE.match(issue_key):
            raise ValueError(f"invalid Jira issue key: {issue_key}")
        base = self._jira_base_url()
        token = os.environ.get("JIRA_API_TOKEN", "")
        if not base or not token:
            raise RuntimeError(
                "download-adf requires JIRA_BASE_URL (or JIRA_URL) and JIRA_API_TOKEN"
            )
        if self._jira_auth_mode() == "basic" and not os.environ.get("JIRA_EMAIL"):
            raise RuntimeError("Jira basic auth requires JIRA_EMAIL")
        api_ver = self._jira_api_version(base)
        _status, data = self._jira_http(
            "GET",
            f"{base}/rest/api/{api_ver}/issue/{issue_key}?fields=summary,description",
        )
        if not isinstance(data, dict):
            raise RuntimeError("Jira download-adf returned unexpected payload")
        fields = data.get("fields") or {}
        desc = fields.get("description")
        if not isinstance(desc, dict):
            raise RuntimeError(
                f"Jira {issue_key} description is not ADF JSON "
                f"(got {type(desc).__name__}). Use Cloud REST API v3 "
                "(JIRA_API_VERSION=3); wiki/string descriptions cannot be "
                "written to adf/<KEY>.adf.json."
            )
        return load_adf_document(desc)

    def download_adf(
        self,
        issue_key: str,
        *,
        adf_path: Path | None = None,
        apply: bool = False,
    ) -> str:
        """Pull remote Jira description ADF into a local adf/<KEY>.adf.json file.

        Dry-run by default (diff only). Pass ``apply=True`` to overwrite the
        local file. Explicit CLI only — never automatic.
        """
        if not _JIRA_KEY_RE.match(issue_key):
            raise ValueError(f"invalid Jira issue key: {issue_key}")
        path = self._resolve_adf_path(issue_key, adf_path)
        remote = self.fetch_issue_adf(issue_key)
        local: dict | None = None
        if path.is_file():
            local = load_adf_file(path)
        diff = self._adf_diff_report(local, remote)
        base = self._jira_base_url()
        if not apply:
            return (
                f"[dry-run] would write {path}\n"
                f"issue: {issue_key}\n"
                f"url: {base}/browse/{issue_key}\n"
                f"{diff}"
                "Re-run with --apply to overwrite the local ADF file "
                "(explicit; no automatic sync). Use git to roll back."
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._adf_pretty(remote), encoding="utf-8")
        return (
            f"Wrote {path} from Jira {issue_key} "
            f"({base}/browse/{issue_key})\n"
            f"{diff}"
        )

    def pull(self, work_id: str, system: str, *, apply: bool = False) -> str:
        links = collect_links(self.project, work_id)
        if system == "github":
            num = links.github_number
            if not num:
                raise ValueError("no GitHub Number on milestone requirement")
            if self._gh_runner is _default_gh_runner and not shutil.which("gh"):
                raise RuntimeError("gh CLI not found")
            proc = self._gh_runner(
                self._gh_cmd(
                    "issue",
                    "view",
                    num,
                    "--json",
                    "title,state,url,labels,body",
                ),
                self.project.root,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "gh issue view failed")
            data = json.loads(proc.stdout)
            report = (
                f"GitHub #{num}: {data.get('title')} [{data.get('state')}]\n"
                f"URL: {data.get('url')}\n"
            )
            if apply:
                req = self.project.milestone_path(work_id)
                set_milestone_bullet(req, "GitHub", "Title", data.get("title") or "")
                set_milestone_bullet(req, "GitHub", "URL", data.get("url") or "")
                set_milestone_bullet(req, "GitHub", "Number", str(num))
                labels = data.get("labels") or []
                if isinstance(labels, list) and labels:
                    names = []
                    for lab in labels:
                        if isinstance(lab, dict) and lab.get("name"):
                            names.append(str(lab["name"]))
                        elif isinstance(lab, str):
                            names.append(lab)
                    if names:
                        set_milestone_bullet(req, "GitHub", "Labels", ", ".join(names))
                self.local.repair_links(work_id)
                report += "Applied into requirements/milestones + local links.\n"
            else:
                report += "Dry-run only; pass --apply to write milestone fields.\n"
            return report
        if system == "jira":
            key = links.jira_key
            if not key:
                raise ValueError("no Jira Key on milestone requirement")
            base = self._jira_base_url()
            token = os.environ.get("JIRA_API_TOKEN", "")
            if not base or not token:
                raise RuntimeError(
                    "Jira pull requires JIRA_BASE_URL (or JIRA_URL) and JIRA_API_TOKEN"
                )
            if self._jira_auth_mode() == "basic" and not os.environ.get("JIRA_EMAIL"):
                raise RuntimeError("Jira basic auth requires JIRA_EMAIL")
            api_ver = self._jira_api_version(base)
            _status, data = self._jira_http(
                "GET",
                f"{base}/rest/api/{api_ver}/issue/{key}?fields=summary,status,labels,description",
            )
            if not isinstance(data, dict):
                raise RuntimeError("Jira pull returned unexpected payload")
            fields = data.get("fields", {})
            summary = fields.get("summary", "")
            status = (fields.get("status") or {}).get("name", "")
            desc_raw = fields.get("description")
            desc_md = adf_to_markdown(desc_raw) if isinstance(desc_raw, dict) else (desc_raw or "")
            report = (
                f"Jira {key}: {summary} [{status}]\n"
                f"URL: {base}/browse/{key}\n"
                f"description_format: {'adf' if isinstance(desc_raw, dict) else 'text'}\n"
            )
            if desc_md:
                report += "description (markdown):\n" + desc_md.rstrip() + "\n"
            if apply:
                path = self.project.milestone_path(work_id)
                set_milestone_bullet(path, "Jira", "Summary", summary)
                set_milestone_bullet(path, "Jira", "Key", key)
                if desc_md.strip():
                    set_milestone_subsection(path, "Jira", "Description", desc_md.strip())
                self.local.repair_links(work_id)
                report += "Applied into requirements/milestones + local links.\n"
            else:
                report += "Dry-run only; pass --apply to write milestone fields.\n"
            return report
        raise ValueError("system must be jira or github")

    @staticmethod
    def parse_github_issue_ref(ref: str) -> tuple[str, str]:
        """Split '123', '#123', or 'owner/repo#123' into ('owner/repo' or '', number)."""
        m = _GH_ISSUE_REF_RE.match((ref or "").strip())
        if not m:
            raise ValueError(
                f"invalid GitHub issue reference: {ref!r} "
                "(use 123, #123, or owner/repo#123)"
            )
        return m.group("repo") or "", m.group("num")

    def resolve_github_repo(self, explicit: str | None = None) -> str:
        """owner/repo: explicit arg → SDLC_GITHUB_REPO/GH_REPO env → git remote origin.

        Returns '' when nothing resolves; gh then falls back to the cwd remote.
        """
        if explicit and explicit.strip():
            return explicit.strip()
        env = self._github_repo()
        if env:
            return env
        proc = self._gh_runner(["git", "remote", "get-url", "origin"], self.project.root)
        if proc.returncode == 0:
            return _repo_from_remote_url(proc.stdout or "")
        return ""

    def _require_gh(self) -> None:
        if self._gh_runner is _default_gh_runner and not shutil.which("gh"):
            raise RuntimeError("gh CLI not found; install GitHub CLI and run `gh auth login`")

    def fetch_github_issue(self, issue_ref: str, *, repo: str | None = None) -> dict:
        """GET number/title/state/url/body for a GitHub issue via the gh CLI."""
        ref_repo, num = self.parse_github_issue_ref(issue_ref)
        resolved = self.resolve_github_repo(ref_repo or repo)
        self._require_gh()
        cmd = ["gh", "issue", "view", num, "--json", "number,title,state,url,body"]
        if resolved:
            cmd.extend(["--repo", resolved])
        proc = self._gh_runner(cmd, self.project.root)
        if proc.returncode != 0:
            raise RuntimeError(
                proc.stderr.strip() or proc.stdout.strip() or "gh issue view failed"
            )
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"gh issue view returned invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("gh issue view returned unexpected payload")
        data.setdefault("number", int(num))
        data["repo"] = resolved
        return data

    def update_github_issue_body(
        self, issue_ref: str, body_md: str, *, repo: str | None = None
    ) -> str:
        """PUT (via `gh issue edit --body`) markdown into an existing issue body."""
        ref_repo, num = self.parse_github_issue_ref(issue_ref)
        resolved = self.resolve_github_repo(ref_repo or repo)
        self._require_gh()
        cmd = ["gh", "issue", "edit", num, "--body", body_md]
        if resolved:
            cmd.extend(["--repo", resolved])
        proc = self._gh_runner(cmd, self.project.root)
        if proc.returncode != 0:
            raise RuntimeError(
                proc.stderr.strip() or proc.stdout.strip() or "gh issue edit failed"
            )
        label = f"{resolved}#{num}" if resolved else f"#{num}"
        url = proc.stdout.strip().splitlines()[-1].strip() if proc.stdout.strip() else ""
        return f"Updated GitHub issue {label} body" + (f" ({url})" if url else "")

    def close_github(self, number: str) -> str:
        """Best-effort close for integration-test cleanup."""
        proc = self._gh_runner(
            self._gh_cmd("issue", "close", str(number)),
            self.project.root,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gh issue close failed")
        return f"Closed GitHub issue #{number}"
