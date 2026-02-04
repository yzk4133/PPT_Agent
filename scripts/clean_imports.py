#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean sys.path.insert calls

The project now uses pyproject.toml and .vscode/settings.json to configure PYTHONPATH,
so manual path manipulation in code is no longer needed. This script removes all sys.path.insert calls.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# 设置输出编码为 UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def clean_sys_path_inserts(file_path: Path) -> Tuple[int, int]:
    """
    清理文件中的 sys.path.insert 调用

    Returns:
        (removed_count, total_lines_changed)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # 匹配 sys.path.insert 的各种模式
        patterns = [
            # 单行 sys.path.insert
            r"sys\.path\.insert\(.*?\)\n",
            # 多行 sys.path.insert（带注释）
            r"# 添加.*?到.*?路径.*?\n.*?sys\.path\.insert\(.*?\)\n",
            r"# 添加.*?目录到.*?路径.*?\n.*?sys\.path\.insert\(.*?\)\n",
        ]

        removed_count = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            removed_count += len(matches)
            content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

        # 清理多余的空行
        content = re.sub(r"\n\n\n+", "\n\n", content)

        # 如果内容有变化，写回文件
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return removed_count, 1

        return 0, 0

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, 0


def main():
    """Main function"""
    # backend directory
    backend_dir = Path(__file__).parent.parent / "backend"

    if not backend_dir.exists():
        print(f"Backend directory not found: {backend_dir}")
        return

    print("=" * 60)
    print("Cleaning sys.path.insert calls")
    print("=" * 60)
    print(f"Target directory: {backend_dir}")
    print()

    # Find all Python files (excluding archive and __pycache__)
    py_files = [
        f for f in backend_dir.rglob("*.py")
        if "archive" not in f.parts
        and "__pycache__" not in f.parts
        and ".venv" not in f.parts
    ]

    print(f"Found {len(py_files)} Python files")
    print()

    total_removed = 0
    total_files_changed = 0

    for py_file in py_files:
        removed, changed = clean_sys_path_inserts(py_file)
        if changed:
            total_removed += removed
            total_files_changed += 1
            relative_path = py_file.relative_to(backend_dir)
            print(f"[OK] {relative_path}: removed {removed} call(s)")

    print()
    print("=" * 60)
    print(f"Done! Processed {total_files_changed} files, removed {total_removed} calls")
    print("=" * 60)
    print()
    print("Note: Make sure PYTHONPATH is configured:")
    print("  1. VS Code users: Already configured in .vscode/settings.json")
    print("  2. CLI users: Set PYTHONPATH=<project_root>")
    print("  3. Or: pip install -e . (using pyproject.toml)")


if __name__ == "__main__":
    main()
