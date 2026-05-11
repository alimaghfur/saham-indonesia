"""Custom test runner that doesn't require pytest installation.

Runs all test files, discovers test classes and functions, reports results.
"""
from __future__ import annotations

import importlib
import inspect
import sys
import traceback
from pathlib import Path

# Ensure stubs and src are on path
stubs_dir = str(Path(__file__).parent / "stubs")
src_dir = str(Path(__file__).parent / "src")
sys.path.insert(0, stubs_dir)
sys.path.insert(1, src_dir)
sys.path.insert(2, str(Path(__file__).parent / "tests"))


def discover_tests(test_dir: Path):
    """Find all test_*.py files and return module names."""
    tests = []
    for f in sorted(test_dir.glob("test_*.py")):
        module_name = f.stem
        tests.append(module_name)
    return tests


def run_test_func(func):
    """Run a single test function, return (passed, error_msg)."""
    try:
        func()
        return True, ""
    except AssertionError as e:
        return False, f"AssertionError: {e}"
    except Exception as e:
        tb = traceback.format_exc()
        return False, f"{type(e).__name__}: {e}\n{tb}"


def run_tests():
    test_dir = Path(__file__).parent / "tests"
    modules = discover_tests(test_dir)

    total = 0
    passed = 0
    failed = 0
    errors = []

    for mod_name in modules:
        try:
            # Import conftest first to set up paths
            spec = importlib.util.spec_from_file_location(
                mod_name, test_dir / f"{mod_name}.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"  ERROR importing {mod_name}: {e}")
            errors.append((f"{mod_name}.<import>", f"{type(e).__name__}: {e}\n{tb}"))
            continue

        # Find test classes and functions
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and name.startswith("Test"):
                # Test class
                for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if method_name.startswith("test_"):
                        total += 1
                        test_id = f"{mod_name}::{name}::{method_name}"
                        try:
                            instance = obj()
                            ok, msg = run_test_func(lambda: method(instance))
                        except Exception as e:
                            ok, msg = False, f"Setup error: {e}"
                        if ok:
                            passed += 1
                            print(f"  PASS: {test_id}")
                        else:
                            failed += 1
                            errors.append((test_id, msg))
                            print(f"  FAIL: {test_id}")
            elif inspect.isfunction(obj) and name.startswith("test_"):
                total += 1
                test_id = f"{mod_name}::{name}"
                ok, msg = run_test_func(obj)
                if ok:
                    passed += 1
                    print(f"  PASS: {test_id}")
                else:
                    failed += 1
                    errors.append((test_id, msg))
                    print(f"  FAIL: {test_id}")

    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed, {total} total")
    print("=" * 70)

    if errors:
        print("\nFAILURES:")
        for test_id, msg in errors:
            print(f"\n--- {test_id} ---")
            print(msg[:500])  # Truncate long tracebacks

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
