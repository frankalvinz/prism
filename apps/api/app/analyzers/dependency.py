import os
import re

from app.models.domain import ChangedFile, DependencyChange, PullRequest

DEP_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "go.mod",
    "pom.xml",
}


class DependencyAnalyzer:
    def analyze(self, pr: PullRequest) -> list[DependencyChange]:
        changes: list[DependencyChange] = []
        for file in pr.changed_files:
            base = os.path.basename(file.filename)
            if base == "package.json":
                changes.extend(self._package_json(file))
            elif base == "requirements.txt":
                changes.extend(self._requirements(file))
            elif base == "pyproject.toml":
                changes.extend(self._pyproject(file))
            elif base == "go.mod":
                changes.extend(self._go_mod(file))
            elif base == "pom.xml" or base.endswith(".csproj"):
                changes.extend(self._generic_manifest(file, ecosystem=base))
        return changes

    def _added_removed_lines(self, patch: str) -> tuple[list[str], list[str]]:
        added: list[str] = []
        removed: list[str] = []
        for line in patch.splitlines():
            if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                continue
            if line.startswith("+"):
                added.append(line[1:].strip())
            elif line.startswith("-"):
                removed.append(line[1:].strip())
        return added, removed

    def _package_json(self, file: ChangedFile) -> list[DependencyChange]:
        if not file.patch:
            return [
                DependencyChange(
                    name="(package.json)",
                    change_type="updated",
                    ecosystem="npm",
                    file=file.filename,
                )
            ]
        added, removed = self._added_removed_lines(file.patch)
        # Parse dependency name/version pairs from JSON-ish lines
        add_map = self._json_dep_lines(added)
        rem_map = self._json_dep_lines(removed)
        results: list[DependencyChange] = []
        for name, new_ver in add_map.items():
            old = rem_map.get(name)
            if old and old != new_ver:
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="updated",
                        ecosystem="npm",
                        old_version=old,
                        new_version=new_ver,
                        file=file.filename,
                    )
                )
            elif name not in rem_map:
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="added",
                        ecosystem="npm",
                        new_version=new_ver,
                        file=file.filename,
                    )
                )
        for name, old_ver in rem_map.items():
            if name not in add_map:
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="removed",
                        ecosystem="npm",
                        old_version=old_ver,
                        file=file.filename,
                    )
                )
        return results

    def _json_dep_lines(self, lines: list[str]) -> dict[str, str]:
        out: dict[str, str] = {}
        pattern = re.compile(r'"([^"]+)"\s*:\s*"([^"]+)"')
        for line in lines:
            m = pattern.search(line)
            if m:
                out[m.group(1)] = m.group(2)
        return out

    def _requirements(self, file: ChangedFile) -> list[DependencyChange]:
        if not file.patch:
            return []
        added, removed = self._added_removed_lines(file.patch)
        add_map = self._req_map(added)
        rem_map = self._req_map(removed)
        results: list[DependencyChange] = []
        for name, ver in add_map.items():
            if name in rem_map and rem_map[name] != ver:
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="updated",
                        ecosystem="pip",
                        old_version=rem_map[name],
                        new_version=ver,
                        file=file.filename,
                    )
                )
            elif name not in rem_map:
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="added",
                        ecosystem="pip",
                        new_version=ver,
                        file=file.filename,
                    )
                )
        for name, ver in rem_map.items():
            if name not in add_map:
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="removed",
                        ecosystem="pip",
                        old_version=ver,
                        file=file.filename,
                    )
                )
        return results

    def _req_map(self, lines: list[str]) -> dict[str, str | None]:
        out: dict[str, str | None] = {}
        for line in lines:
            if not line or line.startswith("#"):
                continue
            m = re.match(r"([A-Za-z0-9_.\-]+)\s*([=<>!~]+)\s*([A-Za-z0-9_.\-]+)", line)
            if m:
                out[m.group(1)] = m.group(3)
            else:
                name = re.split(r"[=<>!~\s]", line)[0]
                if name:
                    out[name] = None
        return out

    def _pyproject(self, file: ChangedFile) -> list[DependencyChange]:
        if not file.patch:
            return []
        added, removed = self._added_removed_lines(file.patch)
        # Treat quoted package lines similarly to requirements
        results: list[DependencyChange] = []
        add_pkgs = {self._strip_quote(x) for x in added if x}
        rem_pkgs = {self._strip_quote(x) for x in removed if x}
        for pkg in sorted(add_pkgs - rem_pkgs):
            if pkg.startswith("[") or "=" not in pkg and '"' not in pkg and "'" not in pkg:
                # skip section headers
                if pkg.startswith("["):
                    continue
            name = re.split(r"[>=<!\s\[]", pkg)[0].strip("\"'")
            if name and not name.startswith("#"):
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="added",
                        ecosystem="python",
                        file=file.filename,
                    )
                )
        for pkg in sorted(rem_pkgs - add_pkgs):
            name = re.split(r"[>=<!\s\[]", pkg)[0].strip("\"'")
            if name and not name.startswith("#") and not name.startswith("["):
                results.append(
                    DependencyChange(
                        name=name,
                        change_type="removed",
                        ecosystem="python",
                        file=file.filename,
                    )
                )
        return results[:50]

    @staticmethod
    def _strip_quote(value: str) -> str:
        return value.strip().strip(",").strip("\"'")

    def _go_mod(self, file: ChangedFile) -> list[DependencyChange]:
        if not file.patch:
            return []
        added, removed = self._added_removed_lines(file.patch)
        results: list[DependencyChange] = []
        for line in added:
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("module") and not line.startswith("go "):
                results.append(
                    DependencyChange(
                        name=parts[0],
                        change_type="added",
                        ecosystem="go",
                        new_version=parts[1] if len(parts) > 1 else None,
                        file=file.filename,
                    )
                )
        for line in removed:
            parts = line.split()
            if len(parts) >= 1 and not line.startswith("module") and not line.startswith("go "):
                results.append(
                    DependencyChange(
                        name=parts[0],
                        change_type="removed",
                        ecosystem="go",
                        old_version=parts[1] if len(parts) > 1 else None,
                        file=file.filename,
                    )
                )
        return results

    def _generic_manifest(self, file: ChangedFile, *, ecosystem: str) -> list[DependencyChange]:
        if not file.patch:
            return [
                DependencyChange(
                    name=f"({ecosystem})",
                    change_type="updated",
                    ecosystem=ecosystem,
                    file=file.filename,
                )
            ]
        added, removed = self._added_removed_lines(file.patch)
        if added or removed:
            return [
                DependencyChange(
                    name=f"({ecosystem})",
                    change_type="updated",
                    ecosystem=ecosystem,
                    file=file.filename,
                )
            ]
        return []
