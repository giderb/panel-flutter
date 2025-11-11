"""
Distribution Cleanup Script
Remove temporary files and prepare for distribution
"""

import os
import shutil
from pathlib import Path

# Directories to remove
REMOVE_DIRS = [
    'validation_output',
    'certification_output',
    'analysis_output',
    'test_bc_output',
    '__pycache__',
    'build',
    'dist',
    'logs',
    '.pytest_cache',
    '.venv',
    'venv'
]

# File patterns to remove
REMOVE_FILE_PATTERNS = [
    '*.log',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '*.f06',
    '*.f04',
    '*.op2',
    '*.pch',
    '*.plt',
    '*.asm',
    '*.aeso',
    '*.becho',
    '*.bat',
    '*.rcf',
    '.DS_Store',
    'Thumbs.db'
]

# Markdown files to remove (keep only essential docs)
REMOVE_MD_FILES = [
    'ADAPTIVE_FLUTTER_IMPLEMENTATION.md',
    'AEROSPACE_CERTIFICATION_SUMMARY.md',
    'BUILD_INSTRUCTIONS.md',
    'CERTIFICATION_CORRECTIONS_IMPLEMENTATION.md',
    'CODEBASE_MAP.md',
    'COMPREHENSIVE_VALIDATION_SUMMARY.md',
    'DISTRIBUTION_MANIFEST.md',
    'NASTRAN_FIX_v1.0.4_FINAL.md',
    'NASTRAN_FIX_v1.0.5_FINAL.md',
    'NASTRAN_SUBPROCESS_FIXES_FINAL.md',
    'RESULTS_PANEL_ENHANCEMENTS.md',
    'VALIDATION_EXECUTIVE_SUMMARY.md',
    'VALIDATION_REPORT.md',
    'NASTRAN_VALIDATION_REPORT.md'
]

# Test files to remove (keep only essential)
REMOVE_TEST_FILES = [
    'test_adaptive_flutter.py',
    'test_certification_corrections.py',
    'validation_tests.py'
]

def cleanup_project(root_dir: Path):
    """Clean up project for distribution"""

    print("=" * 80)
    print("PANEL FLUTTER ANALYSIS - DISTRIBUTION CLEANUP")
    print("=" * 80)
    print()

    removed_count = 0

    # Remove directories
    print("Removing temporary directories...")
    for dir_name in REMOVE_DIRS:
        dir_path = root_dir / dir_name
        if dir_path.exists():
            print(f"  Removing: {dir_name}/")
            shutil.rmtree(dir_path, ignore_errors=True)
            removed_count += 1

    # Remove markdown files
    print("\nRemoving development documentation...")
    for md_file in REMOVE_MD_FILES:
        file_path = root_dir / md_file
        if file_path.exists():
            print(f"  Removing: {md_file}")
            file_path.unlink()
            removed_count += 1

    # Remove test files
    print("\nRemoving development test files...")
    for test_file in REMOVE_TEST_FILES:
        file_path = root_dir / test_file
        if file_path.exists():
            print(f"  Removing: {test_file}")
            file_path.unlink()
            removed_count += 1

    # Remove files by pattern
    print("\nRemoving temporary files...")
    for pattern in REMOVE_FILE_PATTERNS:
        for file_path in root_dir.rglob(pattern):
            # Skip files in venv
            if '.venv' in str(file_path) or 'venv' in str(file_path):
                continue
            if file_path.exists():
                print(f"  Removing: {file_path.relative_to(root_dir)}")
                file_path.unlink()
                removed_count += 1

    # Clean __pycache__ directories recursively
    print("\nRemoving Python cache directories...")
    for pycache in root_dir.rglob('__pycache__'):
        if pycache.exists():
            print(f"  Removing: {pycache.relative_to(root_dir)}")
            shutil.rmtree(pycache, ignore_errors=True)
            removed_count += 1

    print()
    print("=" * 80)
    print(f"CLEANUP COMPLETE - {removed_count} items removed")
    print("=" * 80)
    print()
    print("Project is now ready for distribution!")
    print()
    print("Essential files retained:")
    print("  - Core code: python_bridge/, models/, gui/, utils/")
    print("  - Main scripts: main.py, run_gui.py, run.py")
    print("  - Documentation: README.md, USER_GUIDE.md")
    print("  - Configuration: requirements.txt, setup.py")
    print("  - Tests: tests/ (essential tests only)")
    print()


if __name__ == "__main__":
    root = Path(__file__).parent
    cleanup_project(root)
