import os
import re
from datetime import datetime
from typing import Any

from app.analyzers.file_area import classify_file_area
from app.core.config import Settings
from app.models.domain import ChangedFile, PullRequest, PullRequestCommit
from app.models.enums import FileRole, FileStatus

LANGUAGE_BY_EXT: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C",
    ".swift": "Swift",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".sql": "SQL",
    ".sh": "Shell",
    ".css": "CSS",
    ".scss": "SCSS",
    ".html": "HTML",
}

TEST_PATTERNS = [
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)__tests__/"),
    re.compile(r"(^|/)test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r".*\.(test|spec)\.(js|jsx|ts|tsx)$"),
]

GENERATED_PATTERNS = [
    re.compile(r"(^|/)dist/"),
    re.compile(r"(^|/)build/"),
    re.compile(r"(^|/)vendor/"),
    re.compile(r"package-lock\.json$"),
    re.compile(r"yarn\.lock$"),
    re.compile(r"pnpm-lock\.yaml$"),
    re.compile(r".*\.min\.(js|css)$"),
    re.compile(r".*\.generated\."),
]

DEPENDENCY_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "go.mod",
    "go.sum",
    "pom.xml",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
}

MIGRATION_PATTERNS = [
    re.compile(r"(^|/)migrations?/"),
    re.compile(r".*migrate.*", re.I),
    re.compile(r".*\.sql$"),
]

CONFIG_PATTERNS = [
    re.compile(r"(^|/)\.github/"),
    re.compile(r"(^|/)Dockerfile"),
    re.compile(r"(^|/)docker-compose"),
    re.compile(r".*\.config\.(js|ts|mjs|cjs)$"),
    re.compile(r"(^|/)\.env"),
    re.compile(r"(^|/)tsconfig"),
    re.compile(r"(^|/)eslint"),
    re.compile(r"(^|/)prettier"),
]

DOC_EXTS = {".md", ".rst", ".txt", ".adoc"}


def detect_language(filename: str) -> str | None:
    _, ext = os.path.splitext(filename)
    return LANGUAGE_BY_EXT.get(ext.lower())


def is_test_file(filename: str) -> bool:
    return any(p.search(filename.replace("\\", "/")) for p in TEST_PATTERNS)


def is_generated_file(filename: str) -> bool:
    path = filename.replace("\\", "/")
    return any(p.search(path) for p in GENERATED_PATTERNS)


def classify_role(filename: str) -> FileRole:
    path = filename.replace("\\", "/")
    base = os.path.basename(path)

    if is_test_file(path):
        return FileRole.TEST
    if is_generated_file(path):
        return FileRole.GENERATED
    if base in DEPENDENCY_FILES or base.endswith(".csproj"):
        return FileRole.DEPENDENCY
    if any(p.search(path) for p in MIGRATION_PATTERNS):
        return FileRole.MIGRATION
    if any(p.search(path) for p in CONFIG_PATTERNS):
        return FileRole.CONFIG
    _, ext = os.path.splitext(path)
    if ext.lower() in DOC_EXTS or path.lower().startswith("docs/"):
        return FileRole.DOCUMENTATION
    if detect_language(path) in {
        "Python",
        "JavaScript",
        "TypeScript",
        "Go",
        "Rust",
        "Java",
        "C#",
        "Ruby",
        "PHP",
        "C",
        "C++",
        "Swift",
        "Kotlin",
    }:
        return FileRole.SOURCE
    return FileRole.OTHER


def _parse_status(raw: str) -> FileStatus:
    mapping = {
        "added": FileStatus.ADDED,
        "modified": FileStatus.MODIFIED,
        "removed": FileStatus.REMOVED,
        "renamed": FileStatus.RENAMED,
        "copied": FileStatus.COPIED,
        "changed": FileStatus.CHANGED,
        "unchanged": FileStatus.UNCHANGED,
    }
    return mapping.get(raw.lower(), FileStatus.MODIFIED)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_changed_file(raw: dict[str, Any], *, max_patch_size: int) -> ChangedFile:
    filename = raw.get("filename") or ""
    patch = raw.get("patch")
    binary_ext = filename.endswith(
        (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".woff", ".woff2")
    )
    # GitHub omits patch for binary or too-large files
    is_binary = bool(raw.get("is_binary")) or binary_ext
    if patch is None and (raw.get("additions") or raw.get("deletions")):
        # text file without patch (truncated) — not necessarily binary
        is_binary = bool(raw.get("is_binary")) or binary_ext
    if isinstance(patch, str) and len(patch) > max_patch_size:
        patch = patch[:max_patch_size] + "\n... [patch truncated by PRISM]"

    return ChangedFile(
        filename=filename,
        status=_parse_status(str(raw.get("status", "modified"))),
        additions=int(raw.get("additions") or 0),
        deletions=int(raw.get("deletions") or 0),
        changes=int(raw.get("changes") or 0),
        patch=patch if isinstance(patch, str) else None,
        previous_filename=raw.get("previous_filename"),
        language=detect_language(filename),
        is_test_file=is_test_file(filename),
        is_generated_file=is_generated_file(filename),
        is_binary=is_binary,
        role=classify_role(filename),
        area=classify_file_area(filename, patch if isinstance(patch, str) else None),
    )


def normalize_commits(raw_commits: list[dict[str, Any]]) -> list[PullRequestCommit]:
    commits: list[PullRequestCommit] = []
    for item in raw_commits:
        commit = item.get("commit") or {}
        author = (commit.get("author") or {}).get("name") or (item.get("author") or {}).get("login")
        commits.append(
            PullRequestCommit(
                sha=str(item.get("sha") or ""),
                message=str(commit.get("message") or ""),
                author=author,
                committed_at=_parse_dt((commit.get("author") or {}).get("date")),
            )
        )
    return commits


def normalize_pull_request(
    raw_pr: dict[str, Any],
    raw_files: list[dict[str, Any]],
    raw_commits: list[dict[str, Any]],
    settings: Settings,
) -> tuple[PullRequest, bool, str | None]:
    """Return normalized PR, partial flag, and partial message."""
    base = raw_pr.get("base") or {}
    head = raw_pr.get("head") or {}
    repo_obj = base.get("repo") or {}
    full_name = repo_obj.get("full_name") or f"{base.get('label', 'unknown')}"
    if "/" in full_name:
        owner, repo_name = full_name.split("/", 1)
    else:
        owner = str((raw_pr.get("user") or {}).get("login") or "unknown")
        repo_name = full_name

    total_files = len(raw_files)
    limited_files = raw_files[: settings.max_files]
    partial = total_files > settings.max_files
    partial_message = None

    total_diff = 0
    changed: list[ChangedFile] = []
    for raw in limited_files:
        patch = raw.get("patch") or ""
        total_diff += len(patch) if isinstance(patch, str) else 0
        if total_diff > settings.max_total_diff_size and changed:
            partial = True
            break
        changed.append(normalize_changed_file(raw, max_patch_size=settings.max_patch_size))

    if partial:
        partial_message = (
            f"Analysis completed for {len(changed)} of {total_files} changed files "
            f"(PR exceeds current analysis limits)."
        )

    user = raw_pr.get("user") or {}
    pr = PullRequest(
        id=int(raw_pr.get("id") or 0),
        number=int(raw_pr.get("number") or 0),
        title=str(raw_pr.get("title") or ""),
        description=raw_pr.get("body"),
        author=str(user.get("login") or "unknown"),
        repository=repo_name,
        owner=owner,
        base_branch=str(base.get("ref") or ""),
        head_branch=str(head.get("ref") or ""),
        head_sha=str(head.get("sha") or ""),
        created_at=_parse_dt(raw_pr.get("created_at")),
        updated_at=_parse_dt(raw_pr.get("updated_at")),
        state=str(raw_pr.get("state") or "open"),
        additions=int(raw_pr.get("additions") or 0),
        deletions=int(raw_pr.get("deletions") or 0),
        changed_files_count=int(raw_pr.get("changed_files") or total_files),
        commits=normalize_commits(raw_commits),
        changed_files=changed,
        html_url=str(raw_pr.get("html_url") or ""),
        is_private=bool(repo_obj.get("private")),
    )
    return pr, partial, partial_message
