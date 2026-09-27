import ast
import re
from typing import Any

from app.models.domain import ChangedFile, ComplexityObservation, PullRequest, RiskFinding
from app.models.enums import FindingSource, RiskCategory, Severity

try:
    from radon.complexity import cc_visit
except ImportError:  # pragma: no cover
    cc_visit = None  # type: ignore[assignment]


class ComplexityAnalyzer:
    LARGE_FUNCTION_LINES = 50
    HIGH_CC = 10

    def analyze(self, pr: PullRequest) -> tuple[list[ComplexityObservation], list[RiskFinding]]:
        observations: list[ComplexityObservation] = []
        findings: list[RiskFinding] = []

        for file in pr.changed_files:
            if file.is_binary or not file.patch:
                continue
            lang = file.language
            if lang == "Python":
                obs, file_findings = self._python(file)
            elif lang in {"JavaScript", "TypeScript"}:
                obs, file_findings = self._js_ts(file)
            else:
                obs, file_findings = self._fallback(file)
            if obs:
                observations.append(obs)
            findings.extend(file_findings)
        return observations, findings

    def _extract_added_content(self, patch: str) -> str:
        lines: list[str] = []
        for line in patch.splitlines():
            if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                continue
            if line.startswith("+"):
                lines.append(line[1:])
            elif line.startswith("-"):
                continue
            elif line.startswith("\\"):
                continue
            else:
                # context line (space-prefixed in unified diff)
                if line.startswith(" "):
                    lines.append(line[1:])
        return "\n".join(lines)

    def _python(self, file: ChangedFile) -> tuple[ComplexityObservation | None, list[RiskFinding]]:
        source = self._extract_added_content(file.patch or "")
        if not source.strip():
            return self._fallback(file)

        findings: list[RiskFinding] = []
        function_count = 0
        class_count = 0
        max_nesting = 0
        large_fns: list[str] = []
        complex_fns: list[dict[str, Any]] = []
        max_cc: int | None = None
        notes: list[str] = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            notes.append("Python AST parse failed; used diff-level fallback metrics.")
            return self._fallback(file, notes=notes)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_count += 1
                end = getattr(node, "end_lineno", None) or node.lineno
                size = end - node.lineno + 1
                if size >= self.LARGE_FUNCTION_LINES:
                    large_fns.append(f"{node.name} ({size} lines)")
                nesting = self._nesting_depth(node)
                max_nesting = max(max_nesting, nesting)
            elif isinstance(node, ast.ClassDef):
                class_count += 1

        if cc_visit is not None:
            try:
                blocks = cc_visit(source)
                for block in blocks:
                    complexity = int(block.complexity)
                    max_cc = complexity if max_cc is None else max(max_cc, complexity)
                    if complexity >= self.HIGH_CC:
                        complex_fns.append({"name": block.name, "complexity": complexity})
                        findings.append(
                            RiskFinding(
                                id=f"complexity-cc-{file.filename}-{block.name}",
                                severity=Severity.MEDIUM if complexity < 15 else Severity.HIGH,
                                category=RiskCategory.COMPLEXITY,
                                title="High cyclomatic complexity",
                                description="A function with elevated cyclomatic complexity was detected.",
                                file=file.filename,
                                evidence=f"Function {block.name} has complexity {complexity}",
                                confidence=0.8,
                                source=FindingSource.DETERMINISTIC,
                                recommendation=(
                                    "Consider splitting or simplifying this function "
                                    "to make it easier to test and review."
                                ),
                                files=[file.filename],
                            )
                        )
            except Exception:
                notes.append("radon complexity analysis failed for this file.")

        for name in large_fns:
            findings.append(
                RiskFinding(
                    id=f"complexity-large-{file.filename}-{name}",
                    severity=Severity.LOW,
                    category=RiskCategory.COMPLEXITY,
                    title="Large function",
                    description="A large function was identified in added/changed Python content.",
                    file=file.filename,
                    evidence=name,
                    confidence=0.7,
                    source=FindingSource.DETERMINISTIC,
                    recommendation="Review whether this function can be broken into smaller units.",
                    files=[file.filename],
                )
            )

        obs = ComplexityObservation(
            file=file.filename,
            language="Python",
            function_count=function_count,
            class_count=class_count,
            max_nesting_depth=max_nesting,
            max_cyclomatic_complexity=max_cc,
            large_functions=large_fns,
            complex_functions=complex_fns,
            notes=notes,
        )
        return obs, findings

    def _nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child,
                (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try),
            ):
                max_depth = max(max_depth, self._nesting_depth(child, depth + 1))
            else:
                max_depth = max(max_depth, self._nesting_depth(child, depth))
        return max_depth

    def _js_ts(self, file: ChangedFile) -> tuple[ComplexityObservation | None, list[RiskFinding]]:
        source = self._extract_added_content(file.patch or "")
        findings: list[RiskFinding] = []
        fn_patterns = [
            re.compile(r"\bfunction\s+(\w+)"),
            re.compile(r"\b(?:async\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\("),
            re.compile(r"\b(\w+)\s*\([^)]*\)\s*\{"),
        ]
        names: set[str] = set()
        for pattern in fn_patterns:
            for m in pattern.finditer(source):
                names.add(m.group(1))

        conditionals = len(re.findall(r"\b(if|else if|switch|case|for|while|\?)\b", source))
        classes = len(re.findall(r"\bclass\s+\w+", source))
        notes = [
            "JavaScript/TypeScript complexity uses lightweight pattern analysis "
            "(not a full AST parser)."
        ]
        if conditionals >= 15:
            findings.append(
                RiskFinding(
                    id=f"complexity-js-{file.filename}",
                    severity=Severity.MEDIUM,
                    category=RiskCategory.COMPLEXITY,
                    title="Dense control flow in JS/TS change",
                    description="Many conditionals/loops detected in changed JS/TS content.",
                    file=file.filename,
                    evidence=f"Approximately {conditionals} control-flow keywords in changed content",
                    confidence=0.55,
                    source=FindingSource.DETERMINISTIC,
                    recommendation="Consider simplifying nested conditionals in this change.",
                    files=[file.filename],
                )
            )

        obs = ComplexityObservation(
            file=file.filename,
            language=file.language or "JavaScript",
            function_count=len(names),
            class_count=classes,
            max_nesting_depth=0,
            max_cyclomatic_complexity=None,
            large_functions=[],
            complex_functions=[],
            notes=notes,
        )
        return obs, findings

    def _fallback(
        self, file: ChangedFile, notes: list[str] | None = None
    ) -> tuple[ComplexityObservation | None, list[RiskFinding]]:
        additions = file.additions
        note_list = list(notes or [])
        note_list.append("Unsupported or unparsable language; used line-based statistics.")
        obs = ComplexityObservation(
            file=file.filename,
            language=file.language or "Unknown",
            function_count=0,
            class_count=0,
            max_nesting_depth=0,
            notes=note_list,
        )
        findings: list[RiskFinding] = []
        if additions >= 150:
            findings.append(
                RiskFinding(
                    id=f"complexity-lines-{file.filename}",
                    severity=Severity.LOW,
                    category=RiskCategory.COMPLEXITY,
                    title="Large file-level change",
                    description="Significant additions in a single file may increase review effort.",
                    file=file.filename,
                    evidence=f"+{additions} lines",
                    confidence=0.6,
                    source=FindingSource.DETERMINISTIC,
                    recommendation="Focus review on this large file-level change.",
                    files=[file.filename],
                )
            )
        return obs, findings
