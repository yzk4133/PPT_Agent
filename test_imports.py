#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple import test"""
import sys
import os
from pathlib import Path

# Set encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add project root to path
project_root = Path(__file__).parent.resolve()
backend_root = project_root / "backend"

print(f"Project root: {project_root}")
print(f"Backend root: {backend_root}")
print(f"Backend exists: {backend_root.exists()}")
print(f"Infrastructure exists: {(backend_root / 'infrastructure').exists()}")
print()

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))

print("sys.path:")
for p in sys.path[:5]:
    print(f"  - {p}")
print()

print("Testing imports...")
print("-" * 50)

try:
    # Test infrastructure import
    from infrastructure.exceptions import BaseAPIException
    print("[OK] infrastructure.exceptions.BaseAPIException imported")
except Exception as e:
    print(f"[FAIL] Failed to import infrastructure.exceptions: {e}")

try:
    from infrastructure import get_config
    print("[OK] infrastructure.get_config imported")
except Exception as e:
    print(f"[FAIL] Failed to import infrastructure.get_config: {e}")

try:
    from domain import Task, TaskStatus
    print("[OK] domain.Task, TaskStatus imported")
except Exception as e:
    print(f"[FAIL] Failed to import domain: {e}")

try:
    from agents import master_coordinator_agent
    print("[OK] agents.master_coordinator_agent imported")
except Exception as e:
    print(f"[FAIL] Failed to import agents: {e}")

try:
    from backend import Task, get_config
    print("[OK] backend.Task, backend.get_config imported")
except Exception as e:
    print(f"[FAIL] Failed to import from backend: {e}")

print("-" * 50)
print("Done!")
