"""Close out a Work ID: collect GitHub PR/issue, commit, and Jira state into the ledger.

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
from .placeholders import is_placeholder
from .pointer import PointerStore
from .project import Project
from .registry import TeamRegistry

_PR_URL_RE = re.compile(r"/pull/(\d+)")
_ISSUE_URL_RE = re.compile(r"/issues/(\d+)")
_PR_HASH_RE = re.compile(r"#(\d+)")
_PR_DIGITS_RE = re.compile(r"^\d+$")
_MAX_COMMITS = 50
_PR_JSON_FIELDS = (
    "number,title,state,url,mergedAt,headRefName,baseRefName,commits,author"
)
_ISSUE_JSON_FIELDS = "number,title,state,url,labels,closedAt,author"


class SunsetError(RuntimeError):
    """Raised when sunset cannot resolve a Work ID or persist the snapshot."""


def _normalize_github_number(raw: str, *, prefer: str = "either") -> str:
    """Accept ``123``, ``#123``, ``github:#123``, or a GitHub issues/pull URL.

    ``prefer`` is ``pr`` (``/pull/`` only), ``issue`` (``/issues/`` only),
    or ``either`` (either URL shape, then bare numbers).
    """
    text = (raw or "").strip()
    if is_placeholder(text):
        return ""
    if prefer in {"pr", "either"}:
        m = _PR_URL_RE.search(text)
        if m:
            return m.group(1)
    if prefer in {"issue", "either"}:
        m = _ISSUE_URL_RE.search(text)
        if m:
            return m.group(1)
    if prefer == "pr" and _ISSUE_URL_RE.search(text):
        return ""
    if prefer == "issue" and _PR_URL_RE.search(text):
        return ""
    if _PR_DIGITS_RE.match(text):
        return text
    m = _PR_HASH_RE.search(text)
    if m:
        return m.group(1)
    return ""


def normalize_pr_number(raw: str) -> str:
    """Accept ``123``, ``#123``, ``pr:#123``, or a ``/pull/123`` URL."""
    return _normalize_github_number(raw, prefer="pr")


def normalize_issue_number(raw: str) -> str:
    """Accept ``123``, ``#123``, ``github:#123``, or a ``/issues/123`` URL."""
    return _normalize_github_number(raw, prefer="issue")


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
class SunsetIssue:
    number: str
    title: str = ""
    state: str = ""
    url: str = ""
    labels: list[str] = field(default_factory=list)
    closed_at: str = ""
    author: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SunsetSnapshot:
    work_id: str
    jira: SunsetJira | None = None
    issues: list[SunsetIssue] = field(default_factory=list)
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
            "issues": [i.as_dict() for i in self.issues],
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
        lines.extend(["", "## GitHub issues", ""])
        if self.issues:
            for issue in self.issues:
                closed = f" closed={issue.closed_at}" if issue.closed_at else ""
                labels = f" labels={','.join(issue.labels)}" if issue.labels else ""
                lines.append(
                    f"- #{issue.number} {issue.title} [{issue.state}{closed}] "
                    f"{issue.url}{labels}".rstrip()
                )
        else:
            lines.append("(no issues discovered)")
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
            f"issues: {len(self.issues)}",
        ]
        for issue in self.issues:
            closed = f" closed={issue.closed_at}" if issue.closed_at else ""
            lines.append(
                f"  #{issue.number} {issue.title} [{issue.state}{closed}] {issue.url}".rstrip()
            )
        lines.append(f"prs: {len(self.prs)}")
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
            "registry_github": links.registry_github or (note_token(row.note, "github") if row else ""),
            "registry_jira": links.registry_jira or "",
            "canvas_related_pr": "",
            "canvas_source_issue": "",
            "canvas_source_url": "",
            "canvas_source_system": "",
        }
        if links.canvas:
            meta = parse_canvas_metadata(links.canvas)
            snap.links["canvas_related_pr"] = meta.get("related_pr") or ""
            snap.links["canvas_source_issue"] = meta.get("source_issue") or ""
            snap.links["canvas_source_url"] = meta.get("source_url") or ""
            snap.links["canvas_source_system"] = meta.get("source_system") or ""

        snap.jira = self._collect_jira(wid, links.jira_key, snap.warnings)
        snap.prs = self._collect_prs(wid, snap, snap.warnings)
        snap.issues = self._collect_issues(wid, snap, snap.warnings)
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
            keywords=["sunset", "jira", "github", "issue", "pr", "commit"],
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

    def _collect_issues(
        self, work_id: str, snap: SunsetSnapshot, warnings: list[str]
    ) -> list[SunsetIssue]:
        pr_nums = {p.number for p in snap.prs}
        numbers: list[str] = []
        for raw in (
            snap.links.get("github_number") or "",
            snap.links.get("github_url") or "",
            snap.links.get("registry_github") or "",
            snap.links.get("canvas_source_issue") or "",
            snap.links.get("canvas_source_url") or "",
        ):
            num = normalize_issue_number(raw)
            if num and num not in numbers and num not in pr_nums:
                numbers.append(num)

        if self._gh_available():
            for num in self._search_issue_numbers(
                work_id, snap.jira.key if snap.jira else "", warnings
            ):
                if num not in numbers and num not in pr_nums:
                    numbers.append(num)
        else:
            warnings.append("GitHub issue fetch skipped: gh CLI not found")

        issues: list[SunsetIssue] = []
        for num in numbers:
            issue = self._view_issue(num, warnings)
            if issue:
                issues.append(issue)
            elif not self._gh_available():
                issues.append(SunsetIssue(number=num, title="(local ref only)"))
        return issues

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
            if len(cmd) >= 3 and cmd[1] in {"pr", "issue"}:
                cmd[3:3] = ["--repo", repo]
            else:
                cmd.extend(["--repo", repo])
        return self._gh_runner(cmd, self.project.root)

    def _search_gh_numbers(
        self, kind: str, work_id: str, jira_key: str, warnings: list[str]
    ) -> list[str]:
        queries = [work_id]
        if jira_key:
            queries.append(jira_key)
        found: list[str] = []
        for q in queries:
            proc = self._gh(
                kind,
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
                    f"gh {kind} list --search {q!r} failed: "
                    f"{(proc.stderr or proc.stdout or '').strip() or 'exit ' + str(proc.returncode)}"
                )
                continue
            try:
                rows = json.loads(proc.stdout or "[]")
            except json.JSONDecodeError as exc:
                warnings.append(f"gh {kind} list returned invalid JSON: {exc}")
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

    def _search_pr_numbers(self, work_id: str, jira_key: str, warnings: list[str]) -> list[str]:
        return self._search_gh_numbers("pr", work_id, jira_key, warnings)

    def _search_issue_numbers(self, work_id: str, jira_key: str, warnings: list[str]) -> list[str]:
        return self._search_gh_numbers("issue", work_id, jira_key, warnings)

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

    def _view_issue(self, number: str, warnings: list[str]) -> SunsetIssue | None:
        if not self._gh_available():
            return None
        proc = self._gh("issue", "view", number, "--json", _ISSUE_JSON_FIELDS)
        if proc.returncode != 0:
            warnings.append(
                f"gh issue view {number} failed: "
                f"{(proc.stderr or proc.stdout or '').strip() or 'exit ' + str(proc.returncode)}"
            )
            return SunsetIssue(number=number, title="(unresolved)")
        try:
            data = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            warnings.append(f"gh issue view {number} returned invalid JSON: {exc}")
            return SunsetIssue(number=number, title="(unresolved)")
        if not isinstance(data, dict):
            return SunsetIssue(number=number, title="(unresolved)")
        author = ""
        raw_author = data.get("author")
        if isinstance(raw_author, dict):
            author = str(raw_author.get("login") or raw_author.get("name") or "")
        elif isinstance(raw_author, str):
            author = raw_author
        labels: list[str] = []
        for lab in data.get("labels") or []:
            if isinstance(lab, dict) and lab.get("name"):
                labels.append(str(lab["name"]))
            elif isinstance(lab, str):
                labels.append(lab)
        return SunsetIssue(
            number=str(data.get("number") or number),
            title=str(data.get("title") or ""),
            state=str(data.get("state") or ""),
            url=str(data.get("url") or ""),
            labels=labels,
            closed_at=str(data.get("closedAt") or ""),
            author=author,
        )
