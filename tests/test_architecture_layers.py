import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

REMOVED_WRAPPER_PATHS = [
    REPO_ROOT / "receipt_schema.py",
    REPO_ROOT / "parsing" / "receipt_schema.py",
    REPO_ROOT / "parsing" / "receipt_parse_result.py",
    REPO_ROOT / "diagnostics" / "__init__.py",
    REPO_ROOT / "diagnostics" / "lidl_diagnostics.py",
    REPO_ROOT / "diagnostics" / "rewe_diagnostics.py",
    REPO_ROOT / "workflows" / "receipt_sync.py",
    REPO_ROOT / "storage" / "receipt_repository.py",
    REPO_ROOT / "storage" / "file_manager.py",
    REPO_ROOT / "storage" / "receipt_store.py",
]

FORBIDDEN_IMPORT_MODULES = {
    "receipt_schema",
    "parsing.receipt_schema",
    "parsing.receipt_parse_result",
    "diagnostics",
    "diagnostics.lidl_diagnostics",
    "diagnostics.rewe_diagnostics",
    "diagnostics.rewe_api_reporting",
    "diagnostics.rewe_workflow_reporting",
    "storage.receipt_repository",
    "storage.file_manager",
    "storage.receipt_store",
}

PACKAGE_RULES = {
    "shared": {"api", "auth", "parsing", "storage", "reporting", "workflows", "diagnostics", "cli", "config"},
    "api": {"auth", "parsing", "storage", "reporting", "workflows", "diagnostics", "cli"},
    "auth": {"api", "parsing", "storage", "reporting", "workflows", "diagnostics", "cli"},
    "parsing": {"api", "auth", "storage", "reporting", "workflows", "diagnostics", "cli"},
    "storage": {"api", "auth", "parsing", "reporting", "workflows", "diagnostics", "cli"},
    "reporting": {"api", "auth", "parsing", "storage", "workflows", "diagnostics", "cli"},
}

WORKFLOW_PUBLIC_MODULES = [
    REPO_ROOT / "workflows" / "lidl_workflow.py",
    REPO_ROOT / "workflows" / "rewe_workflow.py",
]


def _absolute_import_roots(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.split(".", 1)[0])
    return imports


def _absolute_import_modules(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module)
    return imports


def _module_all_exports(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "__all__":
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            break
        exports: list[str] = []
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                exports.append(element.value)
        return exports
    return []


class ArchitectureLayerTests(unittest.TestCase):
    def test_removed_wrapper_modules_do_not_exist_anymore(self):
        missing_candidates = [path for path in REMOVED_WRAPPER_PATHS if path.exists()]
        self.assertEqual(missing_candidates, [])

    def test_adapter_packages_do_not_import_forbidden_layers(self):
        for package_name, banned_roots in PACKAGE_RULES.items():
            package_dir = REPO_ROOT / package_name
            for file_path in package_dir.glob("*.py"):
                imported_roots = _absolute_import_roots(file_path)
                forbidden = imported_roots & banned_roots
                self.assertEqual(
                    forbidden,
                    set(),
                    msg=f"{file_path.relative_to(REPO_ROOT)} importiert verbotene Schichten: {sorted(forbidden)}",
                )

    def test_python_files_do_not_import_removed_wrapper_or_legacy_diagnostics_modules(self):
        for file_path in REPO_ROOT.rglob("*.py"):
            if "__pycache__" in file_path.parts:
                continue
            imported_modules = _absolute_import_modules(file_path)
            forbidden = imported_modules & FORBIDDEN_IMPORT_MODULES
            self.assertEqual(
                forbidden,
                set(),
                msg=(
                    f"{file_path.relative_to(REPO_ROOT)} importiert Legacy-Pfade: "
                    f"{sorted(forbidden)}"
                ),
            )

    def test_pipeline_runner_no_longer_imports_concrete_parsing_or_storage_adapters(self):
        pipeline_runner_path = REPO_ROOT / "workflows" / "pipeline_runner.py"
        imported_roots = _absolute_import_roots(pipeline_runner_path)
        self.assertNotIn("parsing", imported_roots)
        self.assertNotIn("storage", imported_roots)

    def test_workflow_public_apis_export_only_non_private_symbols(self):
        for file_path in WORKFLOW_PUBLIC_MODULES:
            exports = _module_all_exports(file_path)
            self.assertNotEqual(
                exports,
                [],
                msg=f"{file_path.relative_to(REPO_ROOT)} definiert kein __all__",
            )
            self.assertEqual(
                [name for name in exports if name.startswith("_")],
                [],
                msg=(
                    f"{file_path.relative_to(REPO_ROOT)} exportiert private Workflow-Helfer: "
                    f"{exports}"
                ),
            )


if __name__ == "__main__":
    unittest.main()

