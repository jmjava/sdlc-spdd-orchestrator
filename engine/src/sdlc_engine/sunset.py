"""Close out a Work ID: collect GitHub PR, commit, and Jira state into the ledger.

``sdlc-engine sunset`` is collect-only by default. ``--apply`` stages a
``session`` record (source=sunset) in the gitignored ledger stage;
``--accept`` promotes it into the committed ledger.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any

from .context_store import ContextStore
from .issues import GhRunner, IssueSyncService, _default_gh_runner
from .links import collect_links, note_token, parse_canvas_metadata, parse_milestone_requirement
from .pointer import PointerStore
from .project import Project
from .registry import TeamRegistry

_PR_URL_RE = re.compile(r"/pull/(\d+)")
_PR_HASH_RE = re.compile(r"#(\d+)")
_PR_DIGITS_RE = re.compile(r"^\d+$")
_MAX_COMMITS = 50
_PR_JSON_FIELDS = (
    "number,title,state,url,mergedAt,headRefName,baseRefName,commits,author"
)


class SunsetError(RuntimeError):
    """Raised when sunset cannot resolve a Work ID or persist the snapshot."""


def normalize_pr_number(raw: str) -> str:
    """Accept ``123``, ``#123``, ``pr:#123``, or a ``/pull/123`` URL."""
    text = (raw or "").strip()
    if not text or text.upper() in {"TBD", "TODO", "NONE", "N/A"}:
        return ""
    m = _PR_URL_RE.search(text)
    if m:
        return m.group(1)
    if _PR_DIGITS_RE.match(text):
        return text
    m = _PR_HASH_RE.search(text)
    if m:
        return m.group(1)
    return ""


@dataclass
class SunsetPr:
    number: str
    title: str = ""
    state: str = ""
    url: str = ""
    merged_at: str = ""
    head_ref: str = ""
    base_ref: str = ""
    author: str = ""
    commits: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SunsetCommit:
    sha: str
    subject: str
    author: str = ""
    date: str = ""
    source: str = "git"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class SunsetJira:
    key: str = ""
    summary: str = ""
    status: str = ""
    url: str = ""
    description: str = ""
    source: str = "local"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class SunsetSnapshot:
    work_id: str
    jira: SunsetJira | None = None
    github_issue: dict[str, str] | None = None
    prs: list[SunsetPr] = field(default_factory=list)
    commits: list[SunsetCommit] = field(default_factory=list)
    links: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    ledger_id: str = ""
    staged: bool = False
    accepted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "work_id": self.work_id,
            "jira": self.jira.as_dict() if self.jira else None,
            "github_issue": self.github_issue,
            "prs": [p.as_dict() for p in self.prs],
            "commits": [c.as_dict() for c in self.commits],
            "links": dict(self.links),
            "warnings": list(self.warnings),
            "ledger_id": self.ledger_id,
            "staged": self.staged,
            "accepted": self.accepted,
        }

    def ledger_title(self) -> str:
        return f"Sunset snapshot for {self.work_id}"

    def ledger_body(self) -> str:
        lines = [
            f"# Sunset: {self.work_id}",
            "",
            "## Jira",
            "",
        ]
        if self.jira and (self.jira.key or self.jira.summary):
            lines.extend(
                [
                    f"- Key: {self.jira.key or '(none)'}",
                    f"- Summary: {self.jira.summary or '(none)'}",
                    f"- Status: {self.jira.status or '(unknown)'}",
                    f"- URL: {self.jira.url or '(none)'}",
                    f"- Source: {self.jira.source}",
                ]
            )
            if self.jira.description:
                lines.extend(["", self.jira.description.strip(), ""])
        else:
            lines.append("(no Jira key on milestone / not pulled)")
        lines.extend(["", "## GitHub PRs", ""])
        if self.prs:
            for pr in self.prs:
                merged = f" merged={pr.merged_at}" if pr.merged_at else ""
                lines.append(
                    f"- #{pr.number} {pr.title} [{pr.state}{merged}] {pr.url}".rstrip()
                )
                if pr.head_ref or pr.base_ref:
                    lines.append(f"  {pr.head_ref or '?'} -> {pr.base_ref or '?'}")
        else:
            lines.append("(no PRs discovered)")
        if self.github_issue:
            lines.extend(
                [
                    "",
                    "## GitHub issue",
                    "",
                    f"- #{self.github_issue.get('number', '')} "
                    f"{self.github_issue.get('title', '')} "
                    f"[{self.github_issue.get('state', '')}] "
                    f"{self.github_issue.get('url', '')}".rstrip(),
                ]
            )
        lines.extend(["", "## Commits", ""])
        if self.commits:
            for c in self.commits:
                extra = f" ({c.author}, {c.date})" if c.author or c.date else ""
                lines.append(f"- {c.sha} {c.subject}{extra}")
        else:
            lines.append("(no commits matching Work ID / Jira key / PR)")
        if self.warnings:
            lines.extend(["", "## Warnings", ""])
            for w in self.warnings:
                lines.append(f"- {w}")
        return "\n".join(lines).rstrip() + "\n"

    def as_text(self) -> str:
        lines = [
            f"sunset: {self.work_id}",
            f"jira: {self._jira_line()}",
            f"github_issue: {self._issue_line()}",
            f"prs: {len(self.prs)}",
        ]
        for pr in self.prs:
            merged = f" merged={pr.merged_at}" if pr.merged_at else ""
            lines.append(f"  #{pr.number} {pr.title} [{pr.state}{merged}] {pr.url}".rstrip())
        lines.append(f"commits: {len(self.commits)}")
        for c in self.commits[:20]:
            lines.append(f"  {c.sha} {c.subject}")
        if len(self.commits) > 20:
            lines.append(f"  … {len(self.commits) - 20} more")
        if self.ledger_id:
            state = "accepted" if self.accepted else "staged"
            lines.append(f"ledger: {self.ledger_id} ({state})")
        else:
            lines.append("ledger: (dry-run; pass --apply to stage a session record)")
        if self.warnings:
            lines.append("warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines) + "\n"

    def _jira_line(self) -> str:
        if not self.jira or not (self.jira.key or self.jira.summary):
            return "(none)"
        status = f" [{self.jira.status}]" if self.jira.status else ""
        return f"{self.jira.key or '(no key)'} {self.jira.summary}{status}".strip()

    def _issue_line(self) -> str:
        if not self.github_issue:
            return "(none)"
        return (
            f"#{self.github_issue.get('number', '')} "
            f"{self.github_issue.get('title', '')} "
            f"[{self.github_issue.get('state', '')}]"
        ).strip()


class SunsetService:
    def __init__(
        self,
        project: Project | None = None,
        *,
        gh_runner: GhRunner | None = None,
        issues: IssueSyncService | None = None,
        store: ContextStore | None = None,
    ) -> None:
        self.project = project or Project.resolve()
        self._gh_runner = gh_runner or _default_gh_runner
        self.issues = issues or IssueSyncService(self.project, gh_runner=self._gh_runner)
        self.store = store or ContextStore(self.project)
        self.registry = TeamRegistry(self.project)

    def resolve_work_id(self, work_id: str | None = None) -> str:
        wid = (work_id or "").strip()
        if wid:
            return wid
        pointer = PointerStore(self.project).get()
        if pointer:
            return pointer
        raise SunsetError("no Work ID (pass --work-id or set the pointer via claim/resume)")

    def collect(self, work_id: str | None = None) -> SunsetSnapshot:
        wid = self.resolve_work_id(work_id)
        snap = SunsetSnapshot(work_id=wid)
        row = next((r for r in self.registry.rows() if r.work_id == wid), None)
        links = collect_links(self.project, wid, row)
        snap.links = {
            "jira_key": links.jira_key or "",
            "github_number": links.github_number or "",
            "github_url": links.github_url or "",
            "registry_pr": note_token(row.note, "pr") if row else "",
            "registry_jira": links.registry_jira or "",
            "canvas_related_pr": "",
        }
        if links.canvas:
            meta = parse_canvas_metadata(links.canvas)
            snap.links["canvas_related_pr"] = meta.get("related_pr") or ""

        snap.jira = self._collect_jira(wid, links.jira_key, snap.warnings)
        snap.github_issue = self._collect_github_issue(wid, links.github_number, snap.warnings)
        snap.prs = self._collect_prs(wid, snap, snap.warnings)
        snap.commits = self._collect_commits(wid, snap)
        return snap

    def run(
        self,
        work_id: str | None = None,
        *,
        apply: bool = False,
        accept: bool = False,
    ) -> SunsetSnapshot:
        snap = self.collect(work_id)
        if accept:
            apply = True
        if not apply:
            return snap
        result = self.store.persist_lesson(
            kind="session",
            work_id=snap.work_id,
            body=snap.ledger_body(),
            title=snap.ledger_title(),
            area="closeout",
            source="sunset",
            phase="sync",
            keywords=["sunset", "jira", "github", "pr", "commit"],
            accept=accept,
            project_guide=False,
        )
        if not result.ok:
            err = "; ".join(result.errors) or "ledger persist failed"
            raise SunsetError(err)
        snap.ledger_id = str(result.git.get("id") or "")
        snap.staged = not accept
        snap.accepted = accept
        return snap

    def report_text(
        self,
        work_id: str | None = None,
        *,
        apply: bool = False,
        accept: bool = False,
    ) -> str:
        return self.run(work_id, apply=apply, accept=accept).as_text()

    def report_json(
        self,
        work_id: str | None = None,
        *,
        apply: bool = False,
        accept: bool = False,
    ) -> str:
        return json.dumps(self.run(work_id, apply=apply, accept=accept).as_dict(), indent=2) + "\n"

    # --- collectors ---

    def _collect_jira(self, work_id: str, key: str, warnings: list[str]) -> SunsetJira | None:
        local = SunsetJira(key=key, source="local")
        req = self.project.milestone_path(work_id)
        if req.is_file():
            parsed = parse_milestone_requirement(req)
            local.summary = parsed.get("jira_summary") or ""
            local.key = local.key or parsed.get("jira_key") or ""
        if not local.key:
            warnings.append("Jira: no key on milestone requirement")
            return local if local.summary else None
        try:
            report = self.issues.pull(work_id, "jira", apply=False)
        except Exception as exc:  # noqa: BLE001 - remote is best-effort
            warnings.append(f"Jira pull skipped: {exc}")
            return local
        remote = SunsetJira(key=local.key, source="jira-pull")
        for line in report.splitlines():
            if line.startswith(f"Jira {local.key}:"):
                rest = line.split(":", 1)[1].strip()
                if rest.endswith("]") and "[" in rest:
                    remote.summary = rest[: rest.rfind("[")].strip()
                    remote.status = rest[rest.rfind("[") + 1 : -1]
                else:
                    remote.summary = rest
            elif line.startswith("URL:"):
                remote.url = line.split(":", 1)[1].strip()
        if not remote.summary:
            remote.summary = local.summary
        return remote

    def _collect_github_issue(
        self, work_id: str, number: str, warnings: list[str]
    ) -> dict[str, str] | None:
        if not number:
            return None
        try:
            report = self.issues.pull(work_id, "github", apply=False)
        except Exception as exc:  # noqa: BLE001 - remote is best-effort
            warnings.append(f"GitHub issue pull skipped: {exc}")
            return {"number": number, "title": "", "state": "", "url": ""}
        data = {"number": number, "title": "", "state": "", "url": ""}
        for line in report.splitlines():
            if line.startswith(f"GitHub #{number}:"):
                rest = line.split(":", 1)[1].strip()
                if rest.endswith("]") and "[" in rest:
                    data["title"] = rest[: rest.rfind("[")].strip()
                    data["state"] = rest[rest.rfind("[") + 1 : -1]
                else:
                    data["title"] = rest
            elif line.startswith("URL:"):
                data["url"] = line.split(":", 1)[1].strip()
        return data

    def _collect_prs(
        self, work_id: str, snap: SunsetSnapshot, warnings: list[str]
    ) -> list[SunsetPr]:
        numbers: list[str] = []
        for raw in (
            snap.links.get("registry_pr") or "",
            snap.links.get("canvas_related_pr") or "",
        ):
            num = normalize_pr_number(raw)
            if num and num not in numbers:
                numbers.append(num)

        if self._gh_available():
            for num in self._search_pr_numbers(work_id, snap.jira.key if snap.jira else "", warnings):
                if num not in numbers:
                    numbers.append(num)
            current = self._current_branch_pr(warnings)
            if current and current not in numbers:
                numbers.append(current)
        else:
            warnings.append("GitHub PR fetch skipped: gh CLI not found")

        prs: list[SunsetPr] = []
        for num in numbers:
            pr = self._view_pr(num, warnings)
            if pr:
                prs.append(pr)
            elif not self._gh_available():
                prs.append(SunsetPr(number=num, title="(local ref only)"))
        return prs

    def _collect_commits(self, work_id: str, snap: SunsetSnapshot) -> list[SunsetCommit]:
        seen: dict[str, SunsetCommit] = {}
        greps = [work_id]
        if snap.jira and snap.jira.key:
            greps.append(snap.jira.key)
        for needle in greps:
            for commit in self._git_log_grep(needle):
                seen.setdefault(commit.sha, commit)
        for pr in snap.prs:
            for raw in pr.commits:
                sha = (raw.get("sha") or "")[:12]
                if not sha:
                    continue
                seen.setdefault(
                    sha,
                    SunsetCommit(
                        sha=sha,
                        subject=raw.get("subject") or "",
                        author=raw.get("author") or "",
                        date=raw.get("date") or "",
                        source=f"pr:{pr.number}",
                    ),
                )
        out = list(seen.values())
        out.sort(key=lambda c: (c.date, c.sha), reverse=True)
        return out[:_MAX_COMMITS]

    def _git_log_grep(self, needle: str) -> list[SunsetCommit]:
        if not needle:
            return []
        try:
            proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.project.root),
                    "log",
                    "--all",
                    "--grep",
                    needle,
                    "--format=%h\t%s\t%an\t%ad",
                    "--date=short",
                    f"-n{_MAX_COMMITS}",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return []
        if proc.returncode != 0:
            return []
        out: list[SunsetCommit] = []
        for line in proc.stdout.splitlines():
            parts = line.split("\t", 3)
            if len(parts) < 2:
                continue
            sha, subject = parts[0], parts[1]
            author = parts[2] if len(parts) > 2 else ""
            date = parts[3] if len(parts) > 3 else ""
            out.append(SunsetCommit(sha=sha, subject=subject, author=author, date=date, source="git"))
        return out

    def _gh_available(self) -> bool:
        if self._gh_runner is not _default_gh_runner:
            return True
        return shutil.which("gh") is not None

    def _gh(self, *parts: str) -> subprocess.CompletedProcess:
        cmd = ["gh", *parts]
        repo = (os.environ.get("SDLC_GITHUB_REPO") or os.environ.get("GH_REPO") or "").strip()
        if repo:
            if len(cmd) >= 3 and cmd[1] == "pr":
                cmd[3:3] = ["--repo", repo]
            else:
                cmd.extend(["--repo", repo])
        return self._gh_runner(cmd, self.project.root)

    def _search_pr_numbers(self, work_id: str, jira_key: str, warnings: list[str]) -> list[str]:
        queries = [work_id]
        if jira_key:
            queries.append(jira_key)
        found: list[str] = []
        for q in queries:
            proc = self._gh(
                "pr",
                "list",
                "--search",
                q,
                "--state",
                "all",
                "--limit",
                "20",
                "--json",
                "number,title,url,state",
            )
            if proc.returncode != 0:
                warnings.append(
                    f"gh pr list --search {q!r} failed: "
                    f"{(proc.stderr or proc.stdout or '').strip() or 'exit ' + str(proc.returncode)}"
                )
                continue
            try:
                rows = json.loads(proc.stdout or "[]")
            except json.JSONDecodeError as exc:
                warnings.append(f"gh pr list returned invalid JSON: {exc}")
                continue
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                num = str(row.get("number") or "")
                if num and num not in found:
                    found.append(num)
        return found

    def _current_branch_pr(self, warnings: list[str]) -> str:
        proc = self._gh("pr", "view", "--json", "number")
        if proc.returncode != 0:
            return ""
        try:
            data = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            return ""
        if isinstance(data, dict) and data.get("number"):
            return str(data["number"])
        return ""

    def _view_pr(self, number: str, warnings: list[str]) -> SunsetPr | None:
        if not self._gh_available():
            return None
        proc = self._gh("pr", "view", number, "--json", _PR_JSON_FIELDS)
        if proc.returncode != 0:
            warnings.append(
                f"gh pr view {number} failed: "
                f"{(proc.stderr or proc.stdout or '').strip() or 'exit ' + str(proc.returncode)}"
            )
            return SunsetPr(number=number, title="(unresolved)")
        try:
            data = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            warnings.append(f"gh pr view {number} returned invalid JSON: {exc}")
            return SunsetPr(number=number, title="(unresolved)")
        if not isinstance(data, dict):
            return SunsetPr(number=number, title="(unresolved)")
        author = ""
        raw_author = data.get("author")
        if isinstance(raw_author, dict):
            author = str(raw_author.get("login") or raw_author.get("name") or "")
        elif isinstance(raw_author, str):
            author = raw_author
        commits: list[dict[str, str]] = []
        for raw in data.get("commits") or []:
            if not isinstance(raw, dict):
                continue
            sha = str(raw.get("oid") or raw.get("sha") or "")[:12]
            subject = str(raw.get("messageHeadline") or raw.get("message") or "")
            c_author = ""
            authors = raw.get("authors") or []
            if isinstance(authors, list) and authors and isinstance(authors[0], dict):
                c_author = str(authors[0].get("name") or authors[0].get("login") or "")
            commits.append(
                {
                    "sha": sha,
                    "subject": subject,
                    "author": c_author,
                    "date": str(raw.get("committedDate") or raw.get("date") or "")[:10],
                }
            )
        return SunsetPr(
            number=str(data.get("number") or number),
            title=str(data.get("title") or ""),
            state=str(data.get("state") or ""),
            url=str(data.get("url") or ""),
            merged_at=str(data.get("mergedAt") or ""),
            head_ref=str(data.get("headRefName") or ""),
            base_ref=str(data.get("baseRefName") or ""),
            author=author,
            commits=commits,
        )
