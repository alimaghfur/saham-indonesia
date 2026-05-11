"""Pytest configuration and shared fixtures.

This conftest ensures the stubs directory is on sys.path so tests can run
without real pandas/numpy/yfinance installed.
"""
import sys
from pathlib import Path

# Add stubs first so they take precedence during testing
stubs_dir = str(Path(__file__).parent.parent / "stubs")
src_dir = str(Path(__file__).parent.parent / "src")

if stubs_dir not in sys.path:
    sys.path.insert(0, stubs_dir)
if src_dir not in sys.path:
    sys.path.insert(1, src_dir)
