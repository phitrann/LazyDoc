from __future__ import annotations

import asyncio
import re
from collections import Counter, defaultdict
from pathlib import PurePosixPath

from app.services.github_client import GitHubClient


class CodeHealthAnalyzer:
    SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".rb", ".php", ".cs"}
    EXCLUDED_PATH_PARTS = {"node_modules", "dist", "build", "coverage", ".next", ".venv", "venv", "__pycache__", "vendor"}
    MAX_FILES = 12
    MAX_BYTES = 240_000

    SECRET_PATTERNS = (
        (
            "hardcoded-secret",
            re.compile(r"(gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})"),
            "High",
            "High",
            "Rotate the exposed secret and move it to an environment variable or secret store.",
        ),
        (
            "suspicious-credential-literal",
            re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
            "Medium",
            "Medium",
            "Replace the literal credential with a runtime secret reference.",
        ),
    )

    EXEC_PATTERNS = (
        (
            "dynamic-execution",
            re.compile(r"\b(eval|exec)\s*\(|new\s+Function\s*\("),
            "High",
            "Medium",
            "Avoid dynamic execution unless the input is fully trusted and validated.",
        ),
        (
            "shell-execution",
            re.compile(r"\b(subprocess\.(?:run|call|Popen)|os\.system|child_process\.exec)\s*\("),
            "High",
            "Medium",
            "Use a safer API or parameterized command execution.",
        ),
    )

    DEBUG_PATTERNS = (
        ("console-log", re.compile(r"\bconsole\.log\s*\("), "Low", "High", "Remove debugging logs before shipping."),
        ("debugger-statement", re.compile(r"\bdebugger\b"), "Low", "High", "Remove debugger statements before releasing."),
        ("python-breakpoint", re.compile(r"\b(pdb\.set_trace|breakpoint)\s*\("), "Low", "High", "Remove interactive breakpoints from production code."),
    )

    TODO_PATTERNS = (re.compile(r"\b(TODO|FIXME|XXX)\b"),)

    def __init__(self, client: GitHubClient) -> None:
        self._client = client

    async def analyze(
        self,
        owner: str,
        repo: str,
        tree: list[dict],
        github_token: str | None = None,
    ) -> dict | None:
        candidates = self._select_files(tree)
        if not candidates:
            return None

        warnings: list[str] = []
        contents = await self._load_contents(owner, repo, candidates, github_token=github_token, warnings=warnings)
        if not contents:
            return None

        findings: list[dict] = []
        import_graph: dict[str, set[str]] = defaultdict(set)
        incoming_edges: Counter[str] = Counter()
        scanned_paths = {item["path"] for item in contents}
        python_module_map = self._build_python_module_map(scanned_paths)

        for item in contents:
            path = item["path"]
            content = item["content"]
            findings.extend(self._scan_file(path, content))
            imports = self._extract_internal_imports(path, content, scanned_paths, python_module_map)
            import_graph[path].update(imports)
            for target in imports:
                incoming_edges[target] += 1

        internal_edges = sum(len(targets) for targets in import_graph.values())
        coupling_index = round(internal_edges / max(len(contents), 1), 2)
        circular_dependencies = self._count_cycles(import_graph)
        orphan_files = [path for path in scanned_paths if incoming_edges[path] == 0]
        orphan_file_percent = round((len(orphan_files) / max(len(scanned_paths), 1)) * 100, 1)

        findings.extend(self._architecture_findings(circular_dependencies, coupling_index, orphan_file_percent))
        score, breakdown = self._score_and_breakdown(findings, circular_dependencies, coupling_index, orphan_file_percent)
        grade = self._grade(score)

        return {
            "grade": grade,
            "score": score,
            "summary": self._summary(grade, score, findings, circular_dependencies),
            "metrics": {
                "scanned_files": len(contents),
                "source_files_detected": len(candidates),
                "security_findings": sum(1 for finding in findings if finding["category"] == "security"),
                "architecture_findings": sum(1 for finding in findings if finding["category"] == "architecture"),
                "maintenance_findings": sum(1 for finding in findings if finding["category"] == "maintenance"),
                "critical_findings": sum(1 for finding in findings if finding["severity"] == "Critical"),
                "high_findings": sum(1 for finding in findings if finding["severity"] == "High"),
                "medium_findings": sum(1 for finding in findings if finding["severity"] == "Medium"),
                "low_findings": sum(1 for finding in findings if finding["severity"] == "Low"),
                "circular_dependencies": circular_dependencies,
                "coupling_index": coupling_index,
                "orphan_file_percent": orphan_file_percent,
            },
            "breakdown": breakdown,
            "findings": findings[:8],
            "warnings": warnings,
        }

    async def _load_contents(
        self,
        owner: str,
        repo: str,
        candidates: list[dict],
        github_token: str | None,
        warnings: list[str],
    ) -> list[dict]:
        semaphore = asyncio.Semaphore(4)

        async def fetch(candidate: dict) -> dict | None:
            async with semaphore:
                try:
                    content = await self._client.get_file_contents(owner, repo, candidate["path"], github_token=github_token)
                except Exception as exc:  # noqa: BLE001 - convert upstream issues into warnings.
                    warnings.append(str(exc))
                    return None
                if not content.strip():
                    return None
                return {"path": candidate["path"], "content": content}

        results = await asyncio.gather(*(fetch(candidate) for candidate in candidates))
        return [result for result in results if result is not None]

    def _select_files(self, tree: list[dict]) -> list[dict]:
        candidates: list[dict] = []
        for entry in tree:
            if entry.get("type") != "blob":
                continue
            path = str(entry.get("path") or "")
            if not path or any(part in self.EXCLUDED_PATH_PARTS for part in PurePosixPath(path).parts):
                continue
            suffix = PurePosixPath(path).suffix.lower()
            if suffix not in self.SOURCE_EXTENSIONS:
                continue
            size = entry.get("size")
            if isinstance(size, int) and size > 120_000:
                continue
            candidates.append(entry)
        candidates.sort(key=lambda item: (str(item.get("path") or "").count("/"), str(item.get("path") or "")))
        return candidates[: self.MAX_FILES]

    def _scan_file(self, path: str, content: str) -> list[dict]:
        findings: list[dict] = []
        lines = content.splitlines()
        for line_number, line in enumerate(lines, start=1):
            for rule_name, pattern, severity, confidence, suggestion in self.SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        self._finding(
                            "security",
                            rule_name,
                            severity,
                            confidence,
                            path,
                            line_number,
                            "Potential secret or API key detected.",
                            suggestion,
                            "Security",
                            line.strip(),
                            "Exposed secrets can leak credentials and should be moved to environment variables or secret storage.",
                        )
                    )
            for rule_name, pattern, severity, confidence, suggestion in self.EXEC_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        self._finding(
                            "security",
                            rule_name,
                            severity,
                            confidence,
                            path,
                            line_number,
                            "Potential dynamic or shell execution detected.",
                            suggestion,
                            "Security",
                            line.strip(),
                            "Dynamic execution can run attacker-controlled input or unsafe shell commands.",
                        )
                    )
            for rule_name, pattern, severity, confidence, suggestion in self.DEBUG_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        self._finding(
                            "maintenance",
                            rule_name,
                            severity,
                            confidence,
                            path,
                            line_number,
                            "Debug code should be removed from production paths.",
                            suggestion,
                            "Maintenance",
                            line.strip(),
                            "Debug statements make production code harder to maintain and can leak implementation details.",
                        )
                    )
            if self.TODO_PATTERNS[0].search(line):
                findings.append(
                    self._finding(
                        "maintenance",
                        "todo-marker",
                        "Low",
                        "High",
                        path,
                        line_number,
                        "TODO/FIXME marker detected.",
                        "Track or resolve the note so it does not linger in production code.",
                        "Maintenance",
                        line.strip(),
                        "Outstanding TODO markers often mean unfinished work or missing cleanup in shipped code.",
                    )
                )
        return findings

    def _extract_internal_imports(
        self,
        path: str,
        content: str,
        scanned_paths: set[str],
        python_module_map: dict[str, str],
    ) -> set[str]:
        imports: set[str] = set()
        suffix = PurePosixPath(path).suffix.lower()
        if suffix == ".py":
            imports.update(self._extract_python_imports(path, content, scanned_paths, python_module_map))
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            imports.update(self._extract_js_imports(path, content, scanned_paths))
        return imports

    def _extract_python_imports(
        self,
        path: str,
        content: str,
        scanned_paths: set[str],
        python_module_map: dict[str, str],
    ) -> set[str]:
        imports: set[str] = set()
        current_dir = PurePosixPath(path).parent
        for line in content.splitlines():
            line = line.strip()
            from_match = re.match(r"from\s+([.\w]+)\s+import\s+(.+)", line)
            if from_match:
                module_name = from_match.group(1)
                imported_names = self._parse_python_import_targets(from_match.group(2))
                target = self._resolve_python_target(current_dir, module_name, scanned_paths, python_module_map)
                if target:
                    imports.add(target)
                for imported_name in imported_names:
                    nested_module_name = self._join_python_module_name(module_name, imported_name)
                    nested_target = self._resolve_python_target(
                        current_dir,
                        nested_module_name,
                        scanned_paths,
                        python_module_map,
                    )
                    if nested_target:
                        imports.add(nested_target)
            import_match = re.match(r"import\s+([.\w, ]+)", line)
            if import_match:
                for target_name in import_match.group(1).split(","):
                    normalized_target = target_name.strip().split(" as ", 1)[0].strip()
                    target = self._resolve_python_target(current_dir, normalized_target, scanned_paths, python_module_map)
                    if target:
                        imports.add(target)
        return imports

    def _build_python_module_map(self, scanned_paths: set[str]) -> dict[str, str]:
        module_map: dict[str, str] = {}
        for path in sorted(scanned_paths):
            path_obj = PurePosixPath(path)
            if path_obj.suffix.lower() != ".py":
                continue
            parts = list(path_obj.with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            if not parts:
                continue
            for index in range(len(parts)):
                alias = ".".join(parts[index:])
                module_map.setdefault(alias, path)
        return module_map

    def _parse_python_import_targets(self, raw_targets: str) -> list[str]:
        targets: list[str] = []
        for target in raw_targets.split(","):
            normalized = target.strip().split(" as ", 1)[0].strip()
            if normalized and normalized != "*":
                targets.append(normalized)
        return targets

    def _join_python_module_name(self, module_name: str, imported_name: str) -> str:
        if module_name.endswith("."):
            return f"{module_name}{imported_name}"
        return f"{module_name}.{imported_name}"

    def _resolve_python_target(
        self,
        current_dir: PurePosixPath,
        module_name: str,
        scanned_paths: set[str],
        python_module_map: dict[str, str],
    ) -> str | None:
        if not module_name:
            return None

        if module_name.startswith("."):
            level = len(module_name) - len(module_name.lstrip("."))
            normalized = module_name.lstrip(".")
            candidate_dir = current_dir
            for _ in range(max(level - 1, 0)):
                candidate_dir = candidate_dir.parent
            candidate_stem = candidate_dir if not normalized else candidate_dir.joinpath(*normalized.split("."))
            return self._find_python_path(candidate_stem.as_posix(), scanned_paths)

        return python_module_map.get(module_name)

    def _find_python_path(self, candidate_stem: str, scanned_paths: set[str]) -> str | None:
        for suffix in (".py", "/__init__.py"):
            candidate = f"{candidate_stem}{suffix}"
            if candidate in scanned_paths:
                return candidate
        return None

    def _extract_js_imports(self, path: str, content: str, scanned_paths: set[str]) -> set[str]:
        imports: set[str] = set()
        current_dir = PurePosixPath(path).parent
        for line in content.splitlines():
            for pattern in (
                re.compile(r"import\s+.*?\s+from\s+['\"](.+?)['\"]"),
                re.compile(r"require\s*\(\s*['\"](.+?)['\"]\s*\)"),
            ):
                match = pattern.search(line)
                if not match:
                    continue
                target = self._resolve_js_target(current_dir, match.group(1), scanned_paths)
                if target:
                    imports.add(target)
        return imports

    def _resolve_js_target(self, current_dir: PurePosixPath, import_path: str, scanned_paths: set[str]) -> str | None:
        if not import_path.startswith("."):
            return None
        base = current_dir.joinpath(import_path).as_posix()
        suffixes = ["", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", "/index.ts", "/index.tsx", "/index.js", "/index.jsx"]
        for suffix in suffixes:
            candidate = f"{base}{suffix}"
            if candidate in scanned_paths:
                return candidate
        return None

    def _count_cycles(self, import_graph: dict[str, set[str]]) -> int:
        visited: set[str] = set()
        active: set[str] = set()
        cycles = 0

        def visit(node: str) -> None:
            nonlocal cycles
            if node in active:
                cycles += 1
                return
            if node in visited:
                return
            visited.add(node)
            active.add(node)
            for target in import_graph.get(node, set()):
                visit(target)
            active.remove(node)

        for node in import_graph:
            visit(node)
        return cycles

    def _score_and_breakdown(
        self,
        findings: list[dict],
        circular_dependencies: int,
        coupling_index: float,
        orphan_file_percent: float,
    ) -> tuple[int, list[dict]]:
        security_penalty, security_drivers = self._finding_penalty(
            [finding for finding in findings if finding["category"] == "security"],
            "security",
        )
        architecture_penalty, architecture_drivers = self._architecture_penalty(circular_dependencies, coupling_index)
        maintenance_penalty, maintenance_drivers = self._maintenance_penalty(
            [finding for finding in findings if finding["category"] == "maintenance"],
            orphan_file_percent,
        )
        total_penalty = security_penalty + architecture_penalty + maintenance_penalty
        score = max(min(100 - total_penalty, 100), 0)
        breakdown = [
            {"name": "Security", "score": max(100 - security_penalty, 0), "impact": -security_penalty, "drivers": security_drivers},
            {
                "name": "Architecture",
                "score": max(100 - architecture_penalty, 0),
                "impact": -architecture_penalty,
                "drivers": architecture_drivers,
            },
            {
                "name": "Maintenance",
                "score": max(100 - maintenance_penalty, 0),
                "impact": -maintenance_penalty,
                "drivers": maintenance_drivers,
            },
            {"name": "Overall", "score": score, "impact": -total_penalty, "drivers": self._overall_drivers(findings, circular_dependencies, coupling_index, orphan_file_percent)},
        ]
        return score, breakdown

    def _grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def _finding_penalty(self, findings: list[dict], category_label: str) -> tuple[int, list[str]]:
        severity_penalties = {"Critical": 25, "High": 10, "Medium": 5, "Low": 2}
        counts = Counter(finding["severity"] for finding in findings)
        penalty = sum(counts[severity] * severity_penalties.get(severity, 1) for severity in counts)
        drivers = [
            f"{counts[severity]} {severity} {category_label} finding{'' if counts[severity] == 1 else 's'} (-{counts[severity] * severity_penalties.get(severity, 1)})"
            for severity in ("Critical", "High", "Medium", "Low")
            if counts[severity] > 0
        ]
        return penalty, drivers

    def _architecture_penalty(self, circular_dependencies: int, coupling_index: float) -> tuple[int, list[str]]:
        drivers: list[str] = []
        penalty = 0
        if circular_dependencies > 0:
            cycle_penalty = min(circular_dependencies * 8, 24)
            penalty += cycle_penalty
            drivers.append(f"{circular_dependencies} circular dependency signal(s) (-{cycle_penalty})")
        if coupling_index > 3:
            coupling_penalty = min(int((coupling_index - 3) * 2), 15)
            penalty += coupling_penalty
            drivers.append(f"Coupling index {coupling_index} above target (-{coupling_penalty})")
        if not drivers:
            drivers.append("No architecture penalties detected.")
        return penalty, drivers

    def _maintenance_penalty(self, findings: list[dict], orphan_file_percent: float) -> tuple[int, list[str]]:
        finding_penalty, finding_drivers = self._finding_penalty(findings, "maintenance")
        orphan_penalty = min(int(max(orphan_file_percent - 70, 0) * 0.3), 10)
        drivers = list(finding_drivers)
        if orphan_penalty > 0:
            drivers.append(f"Orphan file density {orphan_file_percent}% (-{orphan_penalty})")
        if not drivers:
            drivers.append("No maintenance penalties detected.")
        return finding_penalty + orphan_penalty, drivers

    def _overall_drivers(self, findings: list[dict], circular_dependencies: int, coupling_index: float, orphan_file_percent: float) -> list[str]:
        drivers = []
        if findings:
            drivers.append(f"{len(findings)} total finding(s)")
        if circular_dependencies > 0:
            drivers.append(f"{circular_dependencies} cycle signal(s)")
        if coupling_index > 3:
            drivers.append(f"Coupling index {coupling_index}")
        if orphan_file_percent > 70:
            drivers.append(f"Orphan file density {orphan_file_percent}%")
        return drivers or ["No overall penalties detected."]

    def _summary(self, grade: str, score: int, findings: list[dict], circular_dependencies: int) -> str:
        finding_count = len(findings)
        if finding_count == 0:
            return f"Code health looks solid overall. The repository scored {score}/100 ({grade}) with no high-risk findings detected."
        cycle_text = "No circular dependencies detected" if circular_dependencies == 0 else f"{circular_dependencies} circular dependency signal(s) detected"
        return f"Code health scored {score}/100 ({grade}) with {finding_count} finding(s). {cycle_text}."

    def _finding(
        self,
        category: str,
        rule_name: str,
        severity: str,
        confidence: str,
        file_path: str,
        line: int,
        message: str,
        suggestion: str,
        impact_area: str,
        evidence: str,
        why_it_matters: str,
    ) -> dict:
        return {
            "id": f"{rule_name}:{file_path}:{line}",
            "category": category,
            "rule_name": rule_name,
            "severity": severity,
            "confidence": confidence,
            "file_path": file_path,
            "line": line,
            "message": message,
            "suggestion": suggestion,
            "impact_area": impact_area,
            "evidence": evidence,
            "why_it_matters": why_it_matters,
        }

    def _architecture_findings(self, circular_dependencies: int, coupling_index: float, orphan_file_percent: float) -> list[dict]:
        findings: list[dict] = []
        if circular_dependencies > 0:
            findings.append(
                self._finding(
                    "architecture",
                    "circular-dependency",
                    "Medium" if circular_dependencies > 1 else "Low",
                    "High",
                    "(repository graph)",
                    0,
                    f"{circular_dependencies} circular dependency signal(s) detected.",
                    "Break the cycle by extracting shared code into a lower-level module.",
                    "Architecture",
                    f"Detected {circular_dependencies} cycle(s) in the import graph.",
                    "Circular imports make refactors and testing harder.",
                )
            )
        if coupling_index > 3:
            findings.append(
                self._finding(
                    "architecture",
                    "high-coupling",
                    "Medium" if coupling_index > 5 else "Low",
                    "Medium",
                    "(repository graph)",
                    0,
                    f"Coupling index is {coupling_index}, above the preferred range.",
                    "Reduce direct dependencies between modules and split responsibilities.",
                    "Architecture",
                    f"Import edges per scanned file: {coupling_index}.",
                    "High coupling makes modules harder to reuse and isolate.",
                )
            )
        if orphan_file_percent > 70:
            findings.append(
                self._finding(
                    "maintenance",
                    "orphan-file-density",
                    "Low",
                    "Medium",
                    "(repository graph)",
                    0,
                    f"{orphan_file_percent}% of scanned files have no incoming internal references.",
                    "Review dead or isolated modules and prune or document them.",
                    "Maintenance",
                    f"Orphan file share: {orphan_file_percent}%.",
                    "Highly isolated files are often stale or difficult to navigate.",
                )
            )
        return findings
