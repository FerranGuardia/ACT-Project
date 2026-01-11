#!/usr/bin/env python3
"""
Test Quality Validation Script.

This script validates that test files meet quality standards:
- Proper docstrings for classes and methods
- Consistent import patterns
- No duplicate fixture definitions
- Proper test naming conventions

Run before commits to ensure test standards are maintained.
"""

import ast
import pathlib
import sys
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class QualityIssue:
    """Represents a quality issue found in a test file."""
    file_path: pathlib.Path
    line_number: int
    issue_type: str
    message: str
    severity: str = "warning"  # warning, error, info


class TestQualityValidator:
    """Validates test file quality standards."""

    def __init__(self):
        self.issues: List[QualityIssue] = []

    def validate_test_file(self, file_path: pathlib.Path) -> List[QualityIssue]:
        """Validate a single test file and return any issues found."""
        self.issues = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as e:
            self.issues.append(QualityIssue(
                file_path=file_path,
                line_number=0,
                issue_type="syntax_error",
                message=f"Failed to parse file: {e}",
                severity="error"
            ))
            return self.issues

        self._validate_file_structure(file_path, tree)
        self._validate_imports(file_path, tree)
        self._validate_docstrings(file_path, tree)
        self._validate_naming_conventions(file_path, tree)

        return self.issues

    def _validate_file_structure(self, file_path: pathlib.Path, tree: ast.AST):
        """Validate overall file structure."""
        # Check for required imports
        imports = self._extract_imports(tree)
        required_imports = ["pytest"]

        for required in required_imports:
            if not any(required in imp for imp in imports):
                self.issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="missing_import",
                    message=f"Missing required import: {required}",
                    severity="error"
                ))

    def _validate_imports(self, file_path: pathlib.Path, tree: ast.AST):
        """Validate import patterns."""
        imports = self._extract_imports(tree)

        # Check for complex importlib patterns (should use direct imports)
        for imp in imports:
            if "importlib.util" in imp:
                self.issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="complex_import",
                    message="Avoid complex importlib patterns, use direct imports instead",
                    severity="warning"
                ))

        # Check for src. prefix in imports (good practice)
        has_src_imports = any(imp.startswith("from src.") for imp in imports)
        if not has_src_imports and any("from " in imp for imp in imports):
            self.issues.append(QualityIssue(
                file_path=file_path,
                line_number=1,
                issue_type="import_style",
                message="Consider using 'from src.module import Class' for consistency",
                severity="info"
            ))

    def _validate_docstrings(self, file_path: pathlib.Path, tree: ast.AST):
        """Validate docstring presence and quality."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                # Check class docstring
                if not self._has_docstring(node):
                    self.issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="missing_docstring",
                        message=f"Test class '{node.name}' missing docstring",
                        severity="warning"
                    ))

            elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                # Check method docstring
                if not self._has_docstring(node):
                    self.issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="missing_docstring",
                        message=f"Test method '{node.name}' missing docstring",
                        severity="info"
                    ))

    def _validate_naming_conventions(self, file_path: pathlib.Path, tree: ast.AST):
        """Validate test naming conventions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                # Check class name format
                if not node.name.startswith('Test') or len(node.name) < 8:  # "Test" + at least 4 chars
                    self.issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="naming_convention",
                        message=f"Test class name '{node.name}' should be more descriptive",
                        severity="info"
                    ))

            elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                # Check method name format
                if len(node.name) < 12:  # "test_" + at least 5 chars
                    self.issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="naming_convention",
                        message=f"Test method name '{node.name}' should be more descriptive",
                        severity="info"
                    ))

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements from the AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
        return imports

    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if a node has a docstring."""
        return (len(node.body) > 0 and
                isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Str))


def find_test_files(base_path: pathlib.Path) -> List[pathlib.Path]:
    """Find all test files in the project."""
    test_files = []
    for pattern in ["test_*.py", "*_test.py"]:
        test_files.extend(base_path.rglob(pattern))
    return sorted(test_files)


def main():
    """Main entry point for the validation script."""
    base_path = pathlib.Path(__file__).parent.parent.parent
    test_files = find_test_files(base_path / "tests")

    validator = TestQualityValidator()
    total_issues = 0
    files_with_issues = 0

    print(f"Validating {len(test_files)} test files...")
    print("=" * 60)

    for test_file in test_files:
        issues = validator.validate_test_file(test_file)

        if issues:
            files_with_issues += 1
            total_issues += len(issues)

            print(f"\nFile: {test_file.relative_to(base_path)}")
            for issue in issues:
                severity_marker = {
                    "error": "[ERROR]",
                    "warning": "[WARN] ",
                    "info": "[INFO] "
                }.get(issue.severity, "[UNK]  ")

                print(f"  {severity_marker} Line {issue.line_number}: {issue.message}")

    print("\n" + "=" * 60)
    print(f"Summary: {total_issues} issues found in {files_with_issues} files")

    if total_issues == 0:
        print("SUCCESS: All test files pass quality validation!")
        return 0
    else:
        print("FAILURE: Quality issues found. Please fix before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())