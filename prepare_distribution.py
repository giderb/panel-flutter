"""
Prepare Panel Flutter Analysis package for distribution
Cleans up debug files, organizes documentation, creates distribution structure
"""
import os
import shutil
from pathlib import Path

def prepare_distribution():
    """Clean up repository and prepare for distribution"""

    root = Path(".")

    print("="*80)
    print("PREPARING PANEL FLUTTER ANALYSIS FOR DISTRIBUTION")
    print("="*80)

    # Files to remove (debug/test/temporary files)
    files_to_remove = [
        # Debug scripts
        "debug_damping.py",
        "debug_gui_248_bug.py",
        "debug_python_dlm.py",
        "calibrate_damping.py",

        # Test scripts (keep only essential tests in tests/)
        "test_all_fixes.py",
        "test_bdf_fixes.py",
        "test_boundary_conditions.py",
        "test_gui_isotropic_comprehensive.py",
        "test_gui_m08_fix.py",
        "run_gui_test.py",
        "run_python_flutter_M08.py",

        # Validation scripts (results already documented)
        "validate_all_fixes.py",
        "validate_flutter_speed_M08.py",
        "verify_nastran_results.py",
        "comprehensive_validation_report.py",
        "regenerate_bdf_clean.py",

        # Temporary output files
        "gui_test_output.txt",
        "isotropic_test_output.txt",
        "test_output.txt",
        "python_flutter_M08_results.txt",
        "validation_report_output.txt",

        # Duplicate/interim BDF files
        "flutter_analysis.bdf",
        "flutter_analysis_FINAL.bdf",
        "flutter_analysis_fixed.bdf",
        "flutter_analysis_VALIDATED.bdf",
        "flutter_CORRECTED.bdf",

        # Interim documentation (consolidate into docs/)
        "BUGFIX_SUMMARY.txt",
        "DISCREPANCY_RESOLUTION_SUMMARY.txt",
        "AEROSPACE_CERTIFICATION_VALIDATION_REPORT.md",
        "COMPREHENSIVE_FIX_SUMMARY.md",
        "CRITICAL_BUGFIX_REPORT.md",
        "CRITICAL_DISCREPANCY_ANALYSIS.md",
        "CRITICAL_VALIDATION_FINDINGS.md",
        "DAMPING_FIX_VALIDATION.md",
        "EXECUTIVE_SUMMARY_CRITICAL_FINDINGS.md",
        "EXECUTIVE_SUMMARY_FOR_USER.md",
        "FINAL_AEROSPACE_CERTIFICATION_REPORT.md",
        "FINAL_VALIDATION_SUMMARY.md",
        "FIX_SUMMARY_GUI_248_BUG.md",
        "LITERATURE_VALIDATION_COMPLETE.md",
        "PRE_POST_RUN_VALIDATION_CHECKLIST.md",
        "TECHNICAL_SUMMARY_AND_FIXES.md",
        "USER_ACTION_PLAN_IMMEDIATE.md",
        "VALIDATION_REPORT.md",

        # Old cleanup script
        "cleanup_for_distribution.py",
    ]

    # Directories to remove
    dirs_to_remove = [
        "test_damping_fixed",
        "test_damping_output",
        "test_output",
        "test_output_m08",
        "analysis_output/test_1_basic_al",
        "analysis_output/test_2_high_mach",
        "analysis_output/test_3_transonic",
        "analysis_output/test_4_velocity",
        "analysis_output/test_gui_workflow",
        "__pycache__",
    ]

    # Create docs directory structure
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)

    # Keep these essential docs, move to docs/
    essential_docs = {
        "README.md": ".",  # Keep in root
        "CHANGELOG.md": ".",  # Keep in root
        "USER_GUIDE.md": "docs/",
        "LICENSE": ".",  # Keep in root
        "CERTIFICATION_COMPLETE.md": "docs/CERTIFICATION.md",
    }

    print("\n[1/5] Removing debug and test files...")
    removed_count = 0
    for filename in files_to_remove:
        filepath = root / filename
        if filepath.exists():
            try:
                filepath.unlink()
                print(f"  [OK] Removed: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"  [ERR] Error removing {filename}: {e}")

    print(f"\nRemoved {removed_count} files")

    print("\n[2/5] Removing test output directories...")
    dirs_removed = 0
    for dirname in dirs_to_remove:
        dirpath = root / dirname
        if dirpath.exists():
            try:
                shutil.rmtree(dirpath)
                print(f"  [OK] Removed: {dirname}")
                dirs_removed += 1
            except Exception as e:
                print(f"  [ERR] Error removing {dirname}: {e}")

    print(f"\nRemoved {dirs_removed} directories")

    print("\n[3/5] Organizing documentation...")
    # Move/rename essential docs
    for src, dst in essential_docs.items():
        src_path = root / src
        if src_path.exists():
            if dst == ".":
                print(f"  [OK] Keeping: {src}")
            else:
                dst_path = root / dst
                try:
                    shutil.copy2(src_path, dst_path)
                    print(f"  [OK] Copied: {src} -> {dst}")
                except Exception as e:
                    print(f"  [ERR] Error copying {src}: {e}")

    print("\n[4/5] Creating distribution files...")

    # Create MANIFEST.in for package distribution
    manifest_content = """include README.md
include CHANGELOG.md
include LICENSE
include requirements.txt
include setup.py
recursive-include python_bridge *.py
recursive-include models *.py
recursive-include gui *.py
recursive-include scripts *.py
recursive-include docs *.md
recursive-include tests *.py
exclude tests/test_*
exclude *.bdf
exclude *.f06
exclude *.txt
prune .venv
prune __pycache__
prune .git
prune analysis_output
prune certification_output
"""

    with open(root / "MANIFEST.in", "w") as f:
        f.write(manifest_content)
    print("  [OK] Created: MANIFEST.in")

    # Update .gitignore for distribution
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# NASTRAN Output
*.bdf
*.f06
*.f04
*.log
*.pch
*.op2
*.op4
*.DBALL
*.MASTER
*.DBTOC

# Analysis Output
analysis_output/
certification_output/
test_output*/

# Temporary files
*.tmp
*.temp
*_temp.*
*_tmp.*

# Distribution
dist/
build/
*.egg-info/

# Documentation build
docs/_build/
docs/_static/
docs/_templates/

# OS
Thumbs.db
.DS_Store

# Local configuration
.env
.env.local
config.local.json
"""

    with open(root / ".gitignore", "w") as f:
        f.write(gitignore_content)
    print("  [OK] Updated: .gitignore")

    print("\n[5/5] Validating package structure...")

    # Check essential files exist
    essential_files = [
        "setup.py",
        "requirements.txt",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "main.py",
        "run.py",
        "run_gui.py",
    ]

    essential_dirs = [
        "python_bridge",
        "models",
        "gui",
        "tests",
        "scripts",
        "docs",
    ]

    print("\nChecking essential files:")
    all_files_present = True
    for filename in essential_files:
        filepath = root / filename
        if filepath.exists():
            print(f"  [OK] {filename}")
        else:
            print(f"  [MISSING] {filename}")
            all_files_present = False

    print("\nChecking essential directories:")
    all_dirs_present = True
    for dirname in essential_dirs:
        dirpath = root / dirname
        if dirpath.exists():
            # Count Python files
            py_files = list(dirpath.rglob("*.py"))
            print(f"  [OK] {dirname}/ ({len(py_files)} .py files)")
        else:
            print(f"  [MISSING] {dirname}/")
            all_dirs_present = False

    print("\n" + "="*80)
    if all_files_present and all_dirs_present:
        print("[SUCCESS] PACKAGE READY FOR DISTRIBUTION")
        print("\nNext steps:")
        print("  1. Review remaining files")
        print("  2. Test: python setup.py sdist bdist_wheel")
        print("  3. Test installation: pip install -e .")
        print("  4. Run tests: python -m pytest tests/")
        print("  5. Create git tag: git tag v1.0.0")
        print("  6. Push to repository: git push --tags")
    else:
        print("[WARNING] PACKAGE INCOMPLETE - missing essential files/directories")
    print("="*80)

    return all_files_present and all_dirs_present

if __name__ == "__main__":
    success = prepare_distribution()
    exit(0 if success else 1)
