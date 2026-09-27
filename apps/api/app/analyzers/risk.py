"""Area-aware, word-boundary risk rules with grouped findings."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.domain import PullRequest, RiskFinding
from app.models.enums import FileArea, FindingSource, RiskCategory, Severity

_CAMEL_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_PATH_SPLIT = re.compile(r"[/\\._\-]+")
_IMPORT_LINE = re.compile(r"^\s*(import\b|from\b)")
_REEXPORT_LINE = re.compile(
    r"^\s*export\s+(\*|\{|type\b|type\s+\{|[\w*]+\s*,|[\w*]+\s+from\b)",
    re.I,
)
_COMMENT = re.compile(r"^\s*(#|//|/\*|\*|<!--)")


def _is_ignored_added_line(body: str) -> bool:
    """Skip imports, re-exports, and comments — keep export function/const handlers."""
    if _COMMENT.match(body):
        return True
    if _IMPORT_LINE.match(body):
        return True
    if _REEXPORT_LINE.match(body):
        return True
    return False


def added_lines(patch: str | None) -> list[str]:
    if not patch:
        return []
    lines: list[str] = []
    for line in patch.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        if _is_ignored_added_line(body):
            continue
        lines.append(body)
    return lines

_SEV_RANK = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


@dataclass(frozen=True)
class RiskRule:
    category: RiskCategory
    severity: Severity
    path_tokens: frozenset[str]
    content_patterns: tuple[re.Pattern[str], ...]
    allowed_areas: frozenset[FileArea] | None
    excluded_areas: frozenset[FileArea]
    title: str
    explanation: str
    recommendation: str


_UI_SOFT = frozenset(
    {FileArea.UI, FileArea.DOCS, FileArea.STYLES, FileArea.TEST, FileArea.CONSTANTS, FileArea.HOOKS_STATE}
)

RISK_RULES: tuple[RiskRule, ...] = (
    RiskRule(
        category=RiskCategory.AUTHENTICATION,
        severity=Severity.HIGH,
        path_tokens=frozenset(
            {"auth", "authentication", "login", "oauth", "jwt", "passwd", "password", "signin", "signout"}
        ),
        content_patterns=(
            re.compile(r"\bjwt\.(sign|verify|decode)\b", re.I),
            re.compile(r"\bbcrypt\b", re.I),
            re.compile(r"\bgetServerSession\b"),
            re.compile(r"\bnext-auth\b", re.I),
            re.compile(r"\bpassport\.", re.I),
            re.compile(r"\bsession\.(create|destroy|regenerate)\b", re.I),
        ),
        allowed_areas=frozenset({FileArea.AUTH, FileArea.API, FileArea.SERVICE}),
        excluded_areas=_UI_SOFT,
        title="Authentication-related code was modified",
        explanation=(
            "Login, session, or credential handling changed. Mistakes here can lock users out "
            "or weaken access control."
        ),
        recommendation=(
            "Review auth flows end-to-end, confirm tokens/cookies are scoped correctly, and "
            "cover login/logout and session expiry with tests."
        ),
    ),
    RiskRule(
        category=RiskCategory.AUTHORIZATION,
        severity=Severity.HIGH,
        path_tokens=frozenset({"authorization", "permission", "rbac", "acl", "authorize"}),
        content_patterns=(
            re.compile(r"\bhasPermission\b"),
            re.compile(r"\bcheckAccess\b"),
            re.compile(r"\brequireRole\b"),
            re.compile(r"\bauthorize\(", re.I),
        ),
        allowed_areas=frozenset({FileArea.AUTH, FileArea.API, FileArea.SERVICE}),
        excluded_areas=_UI_SOFT,
        title="Authorization-related code was modified",
        explanation=(
            "Permission or access-control logic changed. Incorrect checks can expose private data "
            "or block legitimate users."
        ),
        recommendation=(
            "Verify role and permission checks on every new or changed endpoint, including "
            "negative cases (unauthorized users)."
        ),
    ),
    RiskRule(
        category=RiskCategory.DATABASE,
        severity=Severity.HIGH,
        path_tokens=frozenset({"migration", "migrations", "alembic", "prisma"}),
        content_patterns=(
            re.compile(r"\bCREATE\s+TABLE\b", re.I),
            re.compile(r"\bALTER\s+TABLE\b", re.I),
            re.compile(r"\bDROP\s+TABLE\b", re.I),
            re.compile(r"\bADD\s+COLUMN\b", re.I),
            re.compile(r"\bFOREIGN\s+KEY\b", re.I),
        ),
        allowed_areas=frozenset({FileArea.DATABASE, FileArea.DATA_MODEL, FileArea.SERVICE}),
        excluded_areas=frozenset({FileArea.UI, FileArea.DOCS, FileArea.STYLES, FileArea.TEST}),
        title="Database-related code was modified",
        explanation=(
            "Schema or migration changes can break existing data or deployments if they are not "
            "backward compatible."
        ),
        recommendation=(
            "Confirm migrations are reversible or safely expandable, and run them against a "
            "staging copy of production-like data."
        ),
    ),
    RiskRule(
        category=RiskCategory.API,
        severity=Severity.MEDIUM,
        path_tokens=frozenset({"route", "routes", "controllers", "endpoints", "router"}),
        content_patterns=(
            re.compile(r"export\s+async\s+function\s+(GET|POST|PUT|PATCH|DELETE)\b"),
            re.compile(r"@app\.(get|post|put|patch|delete)\b", re.I),
            re.compile(r"@router\.(get|post|put|patch|delete)\b", re.I),
            re.compile(r"\brouter\.(get|post|put|patch|delete)\b", re.I),
            re.compile(r"\bapp\.(get|post|put|patch|delete)\b", re.I),
        ),
        allowed_areas=frozenset({FileArea.API, FileArea.SERVICE}),
        excluded_areas=_UI_SOFT,
        title="API-related code was modified",
        explanation=(
            "HTTP routes or request handlers changed. Breaking response shapes or auth on these "
            "paths can break clients."
        ),
        recommendation=(
            "Check request validation, auth on each method, status codes, and whether existing "
            "consumers still accept the response contract."
        ),
    ),
    RiskRule(
        category=RiskCategory.DEPENDENCIES,
        severity=Severity.MEDIUM,
        path_tokens=frozenset(
            {
                "package.json",
                "requirements.txt",
                "pyproject.toml",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                "go.mod",
                "pom.xml",
            }
        ),
        content_patterns=(),
        allowed_areas=frozenset({FileArea.DEPENDENCY}),
        excluded_areas=frozenset(),
        title="Dependency manifests were modified",
        explanation=(
            "Third-party packages changed. New versions can introduce breaking APIs or security fixes."
        ),
        recommendation=(
            "Review changelogs for major bumps, run the test suite, and confirm lockfiles are "
            "committed consistently."
        ),
    ),
    RiskRule(
        category=RiskCategory.CONFIGURATION,
        severity=Severity.MEDIUM,
        path_tokens=frozenset({"tsconfig", "eslint", "prettier", "webpack", "vite.config"}),
        content_patterns=(),
        allowed_areas=frozenset({FileArea.CONFIG}),
        excluded_areas=frozenset({FileArea.UI, FileArea.DOCS, FileArea.STYLES, FileArea.TEST}),
        title="Configuration files were modified",
        explanation="Build, lint, or runtime configuration changed and can alter how the app ships.",
        recommendation="Confirm CI still passes and that config changes match the intended environments.",
    ),
    RiskRule(
        category=RiskCategory.INFRASTRUCTURE,
        severity=Severity.MEDIUM,
        path_tokens=frozenset(
            {"dockerfile", "docker-compose", "terraform", "k8s", "helm", "nginx"}
        ),
        content_patterns=(),
        allowed_areas=frozenset({FileArea.INFRA}),
        excluded_areas=frozenset({FileArea.UI, FileArea.DOCS, FileArea.STYLES, FileArea.TEST}),
        title="Infrastructure-related files were modified",
        explanation="Deploy or runtime infrastructure changed, which can affect availability and security.",
        recommendation="Validate against staging and review networking, secrets, and resource limits.",
    ),
    RiskRule(
        category=RiskCategory.SECURITY,
        severity=Severity.HIGH,
        path_tokens=frozenset({"security", "crypto", "encrypt", "decrypt", "vault", "cors", "csp"}),
        content_patterns=(
            re.compile(r"\bcrypto\.(createHash|createHmac|randomBytes)\b"),
            re.compile(r"\bencrypt(ion)?\b", re.I),
            re.compile(r"\bsecret[_-]?key\b", re.I),
            re.compile(r"\bAccess-Control-Allow-Origin\b"),
        ),
        allowed_areas=None,
        excluded_areas=frozenset(
            {FileArea.DOCS, FileArea.STYLES, FileArea.TEST, FileArea.CONSTANTS, FileArea.UI}
        ),
        title="Security-sensitive paths were modified",
        explanation="Crypto, secrets, or security headers changed. Mistakes here can expose data.",
        recommendation=(
            "Double-check secret handling (never log secrets), TLS/CORS settings, and crypto usage."
        ),
    ),
    RiskRule(
        category=RiskCategory.PAYMENTS,
        severity=Severity.HIGH,
        path_tokens=frozenset({"payment", "stripe", "billing", "checkout", "invoice"}),
        content_patterns=(
            re.compile(r"\bstripe\.", re.I),
            re.compile(r"\bbilling\b", re.I),
        ),
        allowed_areas=None,
        excluded_areas=frozenset({FileArea.DOCS, FileArea.STYLES, FileArea.TEST}),
        title="Payment-related code was modified",
        explanation="Money-handling logic changed. Bugs can cause incorrect charges or refunds.",
        recommendation=(
            "Exercise payment flows in a sandbox, verify webhooks, and confirm amounts and currency."
        ),
    ),
    RiskRule(
        category=RiskCategory.DATA_HANDLING,
        severity=Severity.MEDIUM,
        path_tokens=frozenset({"pii", "gdpr", "serializer", "serializers"}),
        content_patterns=(
            re.compile(r"\bPII\b"),
            re.compile(r"\bGDPR\b", re.I),
            re.compile(r"\bpersonal[_-]?data\b", re.I),
            re.compile(r"\bmultipart/form-data\b", re.I),
        ),
        allowed_areas=frozenset(
            {FileArea.API, FileArea.SERVICE, FileArea.DATA_MODEL, FileArea.DATABASE}
        ),
        excluded_areas=_UI_SOFT,
        title="Data-handling code was modified",
        explanation="How user or sensitive data is stored, exported, or uploaded may have changed.",
        recommendation=(
            "Confirm retention, access controls, and that uploads/exports are validated and sanitized."
        ),
    ),
    RiskRule(
        category=RiskCategory.CI_CD,
        severity=Severity.MEDIUM,
        path_tokens=frozenset({"workflows", "gitlab-ci", "jenkins", "circleci", "azure-pipelines"}),
        content_patterns=(),
        allowed_areas=frozenset({FileArea.CI}),
        excluded_areas=frozenset(),
        title="CI/CD configuration was modified",
        explanation="Pipeline changes can silently weaken required checks or deployments.",
        recommendation="Confirm required status checks and deployment gates still enforce safety.",
    ),
    RiskRule(
        category=RiskCategory.ENVIRONMENT,
        severity=Severity.HIGH,
        path_tokens=frozenset({".env", "dotenv"}),
        content_patterns=(
            re.compile(r"\bprocess\.env\.[A-Z0-9_]+\b"),
            re.compile(r"\bos\.environ\b"),
        ),
        allowed_areas=frozenset({FileArea.CONFIG, FileArea.API, FileArea.SERVICE, FileArea.INFRA}),
        excluded_areas=frozenset({FileArea.DOCS, FileArea.STYLES, FileArea.TEST, FileArea.UI}),
        title="Environment configuration was modified",
        explanation="Environment variables or secrets wiring changed.",
        recommendation=(
            "Ensure secrets are not committed, defaults are safe, and each environment has the "
            "required keys documented."
        ),
    ),
)


def tokenize_path(filename: str) -> set[str]:
    """Split a path into lowercase tokens using separators and camelCase."""
    path = filename.replace("\\", "/")
    parts = _PATH_SPLIT.split(path)
    tokens: set[str] = set()
    for part in parts:
        if not part:
            continue
        for piece in _CAMEL_SPLIT.split(part):
            cleaned = re.sub(r"[^a-z0-9]+", "", piece.lower())
            if cleaned and len(cleaned) > 1:
                tokens.add(cleaned)
        lower = part.lower()
        if lower:
            tokens.add(lower)
    return tokens


def _downgrade(severity: Severity) -> Severity:
    order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
    idx = order.index(severity) if severity in order else 2
    return order[min(idx + 1, len(order) - 1)]


class RiskAnalyzer:
    def analyze(self, pr: PullRequest) -> list[RiskFinding]:
        buckets: dict[RiskCategory, dict] = {}

        for file in pr.changed_files:
            path_tokens = tokenize_path(file.filename)
            path_lower = file.filename.replace("\\", "/").lower()
            content_blob = "\n".join(added_lines(file.patch))

            for rule in RISK_RULES:
                if file.area in rule.excluded_areas:
                    continue
                if rule.allowed_areas is not None and file.area not in rule.allowed_areas:
                    continue

                matched_path = [
                    tok
                    for tok in rule.path_tokens
                    if tok in path_tokens
                    or (
                        (any(c in tok for c in "./-_") or tok.startswith("."))
                        and tok in path_lower
                    )
                ]
                matched_content: list[str] = []
                for pattern in rule.content_patterns:
                    m = pattern.search(content_blob)
                    if m:
                        matched_content.append(m.group(0)[:48])

                if not matched_path and not matched_content:
                    continue

                confidence = 0.0
                if matched_path:
                    confidence += 0.5
                if matched_content:
                    confidence += 0.35
                if rule.allowed_areas is not None and file.area in rule.allowed_areas:
                    confidence += 0.15
                elif matched_path:
                    confidence += 0.05

                confidence = min(confidence, 1.0)
                if confidence < 0.5:
                    continue

                severity = rule.severity if confidence >= 0.7 else _downgrade(rule.severity)

                bucket = buckets.get(rule.category)
                if bucket is None:
                    bucket = {
                        "rule": rule,
                        "severity": severity,
                        "confidence": confidence,
                        "files": [],
                        "signals": [],
                    }
                    buckets[rule.category] = bucket
                else:
                    if _SEV_RANK[severity] < _SEV_RANK[bucket["severity"]]:
                        bucket["severity"] = severity
                    bucket["confidence"] = max(bucket["confidence"], confidence)

                if file.filename not in bucket["files"]:
                    bucket["files"].append(file.filename)
                for signal in matched_path[:3] + matched_content[:3]:
                    if signal not in bucket["signals"]:
                        bucket["signals"].append(signal)

        findings: list[RiskFinding] = []
        for category, bucket in buckets.items():
            rule: RiskRule = bucket["rule"]
            files: list[str] = bucket["files"]
            if not files:
                continue
            findings.append(
                RiskFinding(
                    id=f"risk-{category.value}",
                    severity=bucket["severity"],
                    category=category,
                    title=rule.title,
                    description=rule.explanation,
                    file=files[0],
                    evidence=(
                        f"Matched in {len(files)} file(s): " + ", ".join(bucket["signals"][:6])
                    ),
                    confidence=bucket["confidence"],
                    source=FindingSource.DETERMINISTIC,
                    recommendation=rule.recommendation,
                    files=files,
                )
            )

        findings.sort(key=lambda f: (_SEV_RANK.get(f.severity, 9), f.category.value))
        return findings
