#!/usr/bin/env python3
"""
Build script for NASTRAN Panel Flutter Analysis executable.

This script automates the process of compiling the Python application
into a standalone Windows executable using PyInstaller.

Usage:
    python build_executable.py [options]

Options:
    --clean         Clean build directories before building (default)
    --no-clean      Skip cleaning build directories
    --skip-tests    Skip post-build tests
    --package       Create distribution ZIP after building
    --verbose       Show detailed build output
"""

import sys
import os
import subprocess
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import time


class ExecutableBuilder:
    """Handles the executable build process."""

    def __init__(self, verbose=False):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.spec_file = self.project_root / "panel_flutter.spec"
        self.exe_name = "PanelFlutterAnalysis.exe"
        self.verbose = verbose
        self.venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        self.venv_pyinstaller = self.project_root / ".venv" / "Scripts" / "pyinstaller.exe"

    def print_header(self, text):
        """Print formatted header."""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)

    def print_step(self, step_num, text):
        """Print formatted step."""
        print(f"\n[Step {step_num}] {text}")
        print("-" * 70)

    def check_requirements(self):
        """Check if all requirements are met."""
        self.print_step(1, "Checking Requirements")

        # Check if virtual environment exists
        if not self.venv_python.exists():
            print("❌ Virtual environment not found!")
            print(f"   Expected: {self.venv_python}")
            print("\n   Please create virtual environment:")
            print("   python -m venv .venv")
            return False

        print(f"✅ Virtual environment found: {self.venv_python}")

        # Check if PyInstaller is installed
        if not self.venv_pyinstaller.exists():
            print("❌ PyInstaller not found in virtual environment!")
            print("\n   Installing PyInstaller...")
            try:
                subprocess.run(
                    [str(self.venv_python), "-m", "pip", "install", "pyinstaller"],
                    check=True,
                    capture_output=not self.verbose
                )
                print("✅ PyInstaller installed successfully")
            except subprocess.CalledProcessError:
                print("❌ Failed to install PyInstaller")
                return False
        else:
            print(f"✅ PyInstaller found: {self.venv_pyinstaller}")

        # Check if spec file exists
        if not self.spec_file.exists():
            print(f"❌ Spec file not found: {self.spec_file}")
            return False

        print(f"✅ Spec file found: {self.spec_file}")

        # Check if main.py exists
        main_py = self.project_root / "main.py"
        if not main_py.exists():
            print(f"❌ main.py not found: {main_py}")
            return False

        print(f"✅ main.py found: {main_py}")

        return True

    def clean_build_directories(self):
        """Clean previous build artifacts."""
        self.print_step(2, "Cleaning Build Directories")

        dirs_to_clean = [self.build_dir, self.dist_dir]

        for dir_path in dirs_to_clean:
            if dir_path.exists():
                print(f"🧹 Removing: {dir_path}")
                try:
                    shutil.rmtree(dir_path)
                    print(f"   ✅ Removed successfully")
                except Exception as e:
                    print(f"   ⚠️  Warning: Could not remove completely: {e}")
            else:
                print(f"   ℹ️  Not found (skipping): {dir_path}")

        # Clean PyInstaller cache
        cache_dir = Path.home() / "AppData" / "Local" / "pyinstaller"
        if cache_dir.exists():
            print(f"🧹 Cleaning PyInstaller cache: {cache_dir}")
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✅ Cache cleaned")
            except Exception as e:
                print(f"   ⚠️  Warning: {e}")

        print("\n✅ Cleanup complete")

    def build_executable(self):
        """Build the executable using PyInstaller."""
        self.print_step(3, "Building Executable")

        print("🔨 Running PyInstaller...")
        print(f"   Spec file: {self.spec_file}")
        print(f"   Output directory: {self.dist_dir}")

        start_time = time.time()

        # Build command
        cmd = [
            str(self.venv_pyinstaller),
            "--clean",
            "--noconfirm",
            str(self.spec_file)
        ]

        print(f"\n   Command: {' '.join(cmd)}")
        print("\n   Building... (this may take 2-3 minutes)")
        print("   " + "─" * 66)

        try:
            if self.verbose:
                # Show full output
                result = subprocess.run(cmd, check=True, cwd=self.project_root)
            else:
                # Show minimal output
                result = subprocess.run(
                    cmd,
                    check=True,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )

                # Show last few lines of output
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    print("\n   Last 10 lines of build output:")
                    for line in lines[-10:]:
                        print(f"   {line}")

            build_time = time.time() - start_time

            print("\n✅ Build completed successfully!")
            print(f"   Build time: {build_time:.1f} seconds")

            return True

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Build failed!")
            print(f"   Error code: {e.returncode}")
            if not self.verbose and e.stderr:
                print(f"\n   Error output:")
                print(e.stderr)
            return False

    def verify_executable(self):
        """Verify the built executable."""
        self.print_step(4, "Verifying Executable")

        exe_path = self.dist_dir / self.exe_name

        if not exe_path.exists():
            print(f"❌ Executable not found: {exe_path}")
            return False

        print(f"✅ Executable found: {exe_path}")

        # Get file size
        size_bytes = exe_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        print(f"   Size: {size_mb:.1f} MB ({size_bytes:,} bytes)")

        # Get build timestamp
        timestamp = datetime.fromtimestamp(exe_path.stat().st_mtime)
        print(f"   Built: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        # Check for documentation files
        docs = [
            "README_EXECUTABLE.md",
            "QUICK_START.txt",
            "BUILD_INFO.txt"
        ]

        print(f"\n   Documentation files:")
        for doc in docs:
            doc_path = self.dist_dir / doc
            if doc_path.exists():
                print(f"   ✅ {doc}")
            else:
                print(f"   ⚠️  {doc} (missing)")

        return True

    def run_post_build_tests(self):
        """Run basic tests on the built executable."""
        self.print_step(5, "Running Post-Build Tests")

        exe_path = self.dist_dir / self.exe_name

        print("ℹ️  Note: Full GUI testing requires manual verification")
        print("   The executable should be tested by:")
        print("   1. Double-clicking PanelFlutterAnalysis.exe")
        print("   2. Creating a test project")
        print("   3. Running a sample analysis")

        # Check build warnings
        warn_file = self.build_dir / "panel_flutter" / "warn-panel_flutter.txt"
        if warn_file.exists():
            print(f"\n   Checking build warnings...")
            with open(warn_file, 'r', encoding='utf-8', errors='ignore') as f:
                warnings = f.read()

            # Count critical warnings
            critical_keywords = ['error', 'failed', 'critical']
            critical_count = sum(
                1 for line in warnings.lower().split('\n')
                if any(kw in line for kw in critical_keywords)
            )

            if critical_count > 0:
                print(f"   ⚠️  {critical_count} potential issues found in build warnings")
                print(f"   Review: {warn_file}")
            else:
                print(f"   ✅ No critical warnings found")

        return True

    def create_distribution_package(self):
        """Create distribution ZIP package."""
        self.print_step(6, "Creating Distribution Package")

        import zipfile

        # Create ZIP filename with version and date
        version = "1.0.2"
        date_str = datetime.now().strftime("%Y%m%d")
        zip_name = f"PanelFlutterAnalysis_v{version}_{date_str}_Win64.zip"
        zip_path = self.project_root / zip_name

        print(f"📦 Creating: {zip_name}")

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add executable
                exe_path = self.dist_dir / self.exe_name
                zipf.write(exe_path, self.exe_name)
                print(f"   ✅ Added: {self.exe_name}")

                # Add documentation
                docs = ["README_EXECUTABLE.md", "QUICK_START.txt", "BUILD_INFO.txt"]
                for doc in docs:
                    doc_path = self.dist_dir / doc
                    if doc_path.exists():
                        zipf.write(doc_path, doc)
                        print(f"   ✅ Added: {doc}")

            zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ Distribution package created!")
            print(f"   File: {zip_path}")
            print(f"   Size: {zip_size_mb:.1f} MB")

            return True

        except Exception as e:
            print(f"❌ Failed to create distribution package: {e}")
            return False

    def print_summary(self, success):
        """Print build summary."""
        self.print_header("Build Summary")

        if success:
            print("\n✅ BUILD SUCCESSFUL!\n")
            print(f"Executable location: {self.dist_dir / self.exe_name}")
            print(f"Distribution folder: {self.dist_dir}")
            print("\nNext steps:")
            print("  1. Test the executable:")
            print(f"     cd {self.dist_dir}")
            print(f"     .\\{self.exe_name}")
            print("  2. Create test project and run analysis")
            print("  3. Verify NASTRAN execution works")
            print("  4. If all tests pass, distribute the files in dist/")
        else:
            print("\n❌ BUILD FAILED!\n")
            print("Please review the error messages above.")
            print("Common issues:")
            print("  - Missing dependencies: pip install -r requirements.txt")
            print("  - PyInstaller not installed: pip install pyinstaller")
            print("  - Check build warnings in build/panel_flutter/warn-*.txt")

        print("\n" + "=" * 70 + "\n")

    def build(self, clean=True, skip_tests=False, create_package=False):
        """Execute the complete build process."""
        self.print_header("NASTRAN Panel Flutter Analysis - Executable Builder")
        print(f"Build started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Step 1: Check requirements
        if not self.check_requirements():
            self.print_summary(False)
            return False

        # Step 2: Clean (if requested)
        if clean:
            self.clean_build_directories()
        else:
            print("\n[Step 2] Cleaning skipped (--no-clean)")

        # Step 3: Build executable
        if not self.build_executable():
            self.print_summary(False)
            return False

        # Step 4: Verify executable
        if not self.verify_executable():
            self.print_summary(False)
            return False

        # Step 5: Run tests (if requested)
        if not skip_tests:
            self.run_post_build_tests()
        else:
            print("\n[Step 5] Tests skipped (--skip-tests)")

        # Step 6: Create package (if requested)
        if create_package:
            self.create_distribution_package()
        else:
            print("\n[Step 6] Package creation skipped (use --package to enable)")

        self.print_summary(True)
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build NASTRAN Panel Flutter Analysis executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_executable.py                    # Standard build
  python build_executable.py --verbose          # Show detailed output
  python build_executable.py --package          # Build and create ZIP
  python build_executable.py --no-clean         # Skip cleaning build dirs
        """
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        default=True,
        help='Clean build directories before building (default)'
    )
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Skip cleaning build directories'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip post-build tests'
    )
    parser.add_argument(
        '--package',
        action='store_true',
        help='Create distribution ZIP after building'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed build output'
    )

    args = parser.parse_args()

    # Handle --no-clean
    clean = not args.no_clean

    # Create builder
    builder = ExecutableBuilder(verbose=args.verbose)

    # Run build
    try:
        success = builder.build(
            clean=clean,
            skip_tests=args.skip_tests,
            create_package=args.package
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
