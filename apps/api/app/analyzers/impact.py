import os
import re

from app.models.domain import DependencyEdge, PullRequest
from app.models.enums import FileRole

IMPORT_PATTERNS = [
    re.compile(r"^\s*from\s+([\w.]+)\s+import\s+", re.M),
    re.compile(r"^\s*import\s+([\w.]+)", re.M),
    re.compile(r"""(?:from|import)\s+['"]([^'"]+)['"]""", re.M),
    re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""", re.M),
]


class ImpactAnalyzer:
    """Lightweight relationship detection between changed files."""

    def analyze(self, pr: PullRequest) -> list[DependencyEdge]:
        files = [f for f in pr.changed_files if f.role in {FileRole.SOURCE, FileRole.TEST}]
        by_stem: dict[str, str] = {}
        for f in files:
            stem = os.path.splitext(os.path.basename(f.filename))[0]
            by_stem[stem.lower()] = f.filename
            # also map module-ish paths
            mod = f.filename.replace("\\", "/").rsplit(".", 1)[0].replace("/", ".")
            by_stem[mod.lower()] = f.filename

        edges: list[DependencyEdge] = []
        seen: set[tuple[str, str]] = set()

        for f in files:
            patch = f.patch or ""
            refs: set[str] = set()
            for pattern in IMPORT_PATTERNS:
                for m in pattern.finditer(patch):
                    refs.add(m.group(1))

            for ref in refs:
                target = self._resolve(ref, by_stem, f.filename)
                if not target or target == f.filename:
                    continue
                key = (f.filename, target)
                if key in seen:
                    continue
                seen.add(key)
                confidence = 0.7 if "/" in ref or "." in ref else 0.45
                edges.append(
                    DependencyEdge(
                        source=f.filename,
                        target=target,
                        relationship="imports",
                        confidence=confidence,
                    )
                )

        # Heuristic layering: routes -> services -> repositories by path naming
        path_files = {f.filename.replace("\\", "/"): f.filename for f in files}
        for path, original in path_files.items():
            lower = path.lower()
            if "route" in lower or "controller" in lower or "/api/" in lower:
                for other_path, other_orig in path_files.items():
                    if other_orig == original:
                        continue
                    if "service" in other_path.lower():
                        key = (original, other_orig)
                        if key not in seen:
                            seen.add(key)
                            edges.append(
                                DependencyEdge(
                                    source=original,
                                    target=other_orig,
                                    relationship="likely_calls",
                                    confidence=0.4,
                                )
                            )
            if "service" in lower:
                for other_path, other_orig in path_files.items():
                    if other_orig == original:
                        continue
                    if "repository" in other_path.lower() or "repo" in other_path.lower():
                        key = (original, other_orig)
                        if key not in seen:
                            seen.add(key)
                            edges.append(
                                DependencyEdge(
                                    source=original,
                                    target=other_orig,
                                    relationship="likely_calls",
                                    confidence=0.4,
                                )
                            )
        return edges[:100]

    def _resolve(self, ref: str, by_stem: dict[str, str], current: str) -> str | None:
        cleaned = ref.lstrip("./").replace("\\", "/")
        candidates = [
            cleaned.lower(),
            cleaned.split("/")[-1].lower(),
            cleaned.replace("/", ".").lower(),
            os.path.splitext(cleaned.split("/")[-1])[0].lower(),
        ]
        for c in candidates:
            if c in by_stem and by_stem[c] != current:
                return by_stem[c]
        return None
