"""Framework-aware classification of changed files into FileArea."""

from __future__ import annotations

import os
import re

from app.models.enums import FileArea

_API_CONTENT = re.compile(
    r"(export\s+async\s+function\s+(GET|POST|PUT|PATCH|DELETE)\b)"
    r"|(@app\.(get|post|put|patch|delete)\b)"
    r"|(@router\.(get|post|put|patch|delete)\b)"
    r"|(router\.(get|post|put|patch|delete)\b)"
    r"|(app\.(get|post|put|patch|delete)\b)",
    re.I,
)
_UI_CONTENT = re.compile(
    r"(return\s*\(\s*<)|(<div[\s>])|(<[A-Z][A-Za-z0-9]*[\s/>])|(React\.createElement)",
    re.I,
)


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _basename(path: str) -> str:
    return os.path.basename(path)


def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def classify_file_area(filename: str, patch: str | None = None) -> FileArea:
    """Classify a file into a semantic area using path rules, then light content checks."""
    path = _norm(filename)
    lower = path.lower()
    base = _basename(lower)
    ext = _ext(lower)
    content = patch or ""

    # Tests first
    if (
        "/tests/" in f"/{lower}"
        or "/__tests__/" in f"/{lower}"
        or "/test/" in f"/{lower}"
        or re.search(r"(^|/)test_[^/]+\.py$", lower)
        or re.search(r"[^/]+_test\.py$", lower)
        or re.search(r"\.(test|spec)\.(js|jsx|ts|tsx)$", lower)
    ):
        return FileArea.TEST

    # Dependencies
    if base in {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "pipfile",
        "pipfile.lock",
        "go.mod",
        "go.sum",
        "pom.xml",
        "cargo.toml",
        "gemfile",
        "composer.json",
    } or base.endswith(".csproj"):
        return FileArea.DEPENDENCY

    # CI
    if (
        "/.github/workflows/" in f"/{lower}"
        or "gitlab-ci" in lower
        or "jenkins" in lower
        or "circleci" in lower
        or "azure-pipelines" in lower
    ):
        return FileArea.CI

    # Infra
    if (
        base in {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}
        or lower.endswith("/dockerfile")
        or "docker-compose" in base
        or "/terraform/" in f"/{lower}"
        or "/k8s/" in f"/{lower}"
        or "/helm/" in f"/{lower}"
        or "nginx" in base
    ):
        return FileArea.INFRA

    # Styles
    if ext in {".css", ".scss", ".sass", ".less"} or "/styles/" in f"/{lower}":
        return FileArea.STYLES

    # Docs
    if (
        ext in {".md", ".rst", ".adoc"}
        or lower.startswith("docs/")
        or "/docs/" in f"/{lower}"
        or base in {"readme", "readme.md", "changelog.md", "license", "license.md"}
    ):
        return FileArea.DOCS

    # Database / migrations
    if (
        "/migrations/" in f"/{lower}"
        or "/alembic/" in f"/{lower}"
        or "/prisma/migrations/" in f"/{lower}"
        or ext == ".sql"
        or "migrate" in base
    ):
        return FileArea.DATABASE

    # Config / env
    if (
        base.startswith(".env")
        or "/.env" in f"/{lower}"
        or re.search(r"\.(ya?ml|toml|ini|cfg)$", lower)
        and ("config" in lower or "settings" in lower)
        or re.search(r"\.config\.(js|ts|mjs|cjs)$", lower)
        or base.startswith("tsconfig")
        or "eslint" in base
        or "prettier" in base
        or base in {"settings.py", "settings.json", "config.py", "config.ts", "config.js"}
    ):
        return FileArea.CONFIG

    # Next.js / Nest / Express API routes
    if (
        re.search(r"(^|/)app/api/.+/route\.(ts|js|tsx|jsx)$", lower)
        or re.search(r"(^|/)pages/api/", lower)
        or re.search(r"(^|/)src/app/api/.+/route\.(ts|js)$", lower)
        or re.search(r"(^|/)routes?/", lower)
        or re.search(r"(^|/)controllers?/", lower)
        or base in {"views.py", "urls.py"}
        or re.search(r"(^|/)api/.*(router|routes|handler|controller)", lower)
    ):
        return FileArea.API

    # Auth-specific directories
    if re.search(r"(^|/)(auth|authentication|oauth|session)/", lower) or re.search(
        r"(^|/)(middleware/)?auth\.(ts|js|py)$", lower
    ):
        return FileArea.AUTH

    # Constants
    if "/constants/" in f"/{lower}" or re.search(r"(^|/)const(ants)?\.(ts|js|py)$", lower):
        return FileArea.CONSTANTS

    # Hooks / state
    if (
        "/hooks/" in f"/{lower}"
        or "/store/" in f"/{lower}"
        or "/stores/" in f"/{lower}"
        or "/context/" in f"/{lower}"
        or "/contexts/" in f"/{lower}"
        or re.search(r"(^|/)use[A-Z][A-Za-z]+\.(ts|tsx|js|jsx)$", path)
    ):
        return FileArea.HOOKS_STATE

    # Data models
    if (
        "/models/" in f"/{lower}"
        or "/schemas/" in f"/{lower}"
        or "/entities/" in f"/{lower}"
        or "/types/" in f"/{lower}"
        and ext in {".ts", ".tsx", ".py"}
        or base in {"schema.prisma", "models.py", "schema.py"}
    ):
        return FileArea.DATA_MODEL

    # Services / business logic
    if (
        "/services/" in f"/{lower}"
        or "/service/" in f"/{lower}"
        or "/repositories/" in f"/{lower}"
        or "/repository/" in f"/{lower}"
        or "/lib/" in f"/{lower}"
        and ext in {".ts", ".js", ".py"}
        and "/components/" not in f"/{lower}"
    ):
        return FileArea.SERVICE

    # UI components
    if (
        "/components/" in f"/{lower}"
        or "/component/" in f"/{lower}"
        or ext in {".vue", ".svelte"}
        or (
            ext in {".tsx", ".jsx"}
            and not re.search(r"(^|/)app/api/", lower)
            and not re.search(r"route\.(ts|js)$", lower)
        )
    ):
        return FileArea.UI

    # Content confirmation for ambiguous source files
    if _API_CONTENT.search(content):
        return FileArea.API
    if ext in {".tsx", ".jsx"} or _UI_CONTENT.search(content):
        return FileArea.UI

    if ext in {".py", ".ts", ".js", ".go", ".rs", ".java", ".rb", ".php", ".cs"}:
        return FileArea.SERVICE

    return FileArea.OTHER
