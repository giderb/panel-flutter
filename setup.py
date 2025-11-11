"""
Setup script for Panel Flutter Analysis Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="panel-flutter-analysis",
    version="2.1.8",
    author="Aerospace Engineering Team",
    author_email="aerospace@example.com",
    description="Certified panel flutter analysis tool for fighter aircraft - Production v2.1.8 (Validation Fixes)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourrepo/panel-flutter",
    packages=find_packages(exclude=['tests', 'tests.*', 'scripts']),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "panel-flutter=main:main",
            "panel-flutter-gui=run_gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md"],
    },
    keywords=[
        "aeroelasticity",
        "flutter",
        "aerospace",
        "structural dynamics",
        "panel flutter",
        "piston theory",
        "nastran",
        "fighter aircraft",
        "supersonic",
        "transonic"
    ],
    project_urls={
        "Documentation": "https://github.com/yourrepo/panel-flutter/blob/main/USER_GUIDE.md",
        "Source": "https://github.com/yourrepo/panel-flutter",
        "Bug Reports": "https://github.com/yourrepo/panel-flutter/issues",
    },
)
