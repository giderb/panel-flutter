# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for NASTRAN Panel Flutter Analysis GUI
Optimized for Windows distribution
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Collect customtkinter data files (themes, assets)
customtkinter_datas = collect_data_files('customtkinter')

# Collect all submodules to ensure nothing is missed
hidden_imports = [
    # CustomTkinter and dependencies
    'customtkinter',
    'customtkinter.windows',
    'customtkinter.windows.widgets',
    'PIL',
    'PIL._tkinter_finder',

    # Tkinter
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',

    # Matplotlib backends and dependencies
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg',
    'matplotlib.figure',
    'matplotlib.animation',

    # Scientific computing
    'numpy',
    'numpy.core',
    'numpy.core._methods',
    'numpy.lib.format',
    'scipy',
    'scipy.sparse',
    'scipy.sparse.csgraph',
    'scipy.sparse.linalg',
    'scipy.linalg',
    'scipy.integrate',
    'scipy.optimize',
    'scipy.interpolate',
    'pandas',
    'pandas.io.formats.style',

    # Plotting
    'seaborn',
    'plotly',
    'plotly.graph_objs',

    # Configuration
    'yaml',
    'json',
    'jsonschema',

    # Progress bars
    'tqdm',

    # PyNastran
    'pyNastran',
    'pyNastran.bdf',
    'pyNastran.op2',
    'pyNastran.f06',

    # Standard library that sometimes needs explicit inclusion
    'pathlib',
    'logging',
    'threading',
    'subprocess',
    'shutil',
    'tempfile',
    'collections',
    'datetime',
    'json',
    're',
]

# Add all our custom modules
custom_modules = [
    'gui',
    'gui.main_window',
    'gui.project_manager',
    'gui.theme_manager',
    'gui.report_generator',
    'gui.example_configurations',
    'gui.panels',
    'gui.panels.base_panel',
    'gui.panels.home_panel',
    'gui.panels.material_panel',
    'gui.panels.structural_panel',
    'gui.panels.aerodynamics_panel',
    'gui.panels.analysis_panel',
    'gui.panels.results_panel',
    'gui.panels.validation_panel',
    'gui.panels.geometry_panel',
    'models',
    'models.material',
    'models.structural',
    'models.aerodynamic',
    'python_bridge',
    'python_bridge.bdf_generator_sol145_fixed',
    'python_bridge.nastran_runner',
    'python_bridge.f06_parser',
    'python_bridge.integrated_analysis_executor',
    'python_bridge.flutter_analyzer',
    'python_bridge.analysis_executor',
    'python_bridge.analysis_validator',
    'python_bridge.nastran_interface',
    'python_bridge.pynastran_bdf_generator',
    'python_bridge.simple_bdf_generator',
    'python_bridge.template_bdf_generator',
    'utils',
    'utils.logger',
    'utils.config',
    'utils.nastran_detector',
]

hidden_imports.extend(custom_modules)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=customtkinter_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'IPython',
        'notebook',
        'jupyter',
        'sphinx',
        'pytest',
        'test',
        'tests',
        'unittest',
        # 'pydoc',  # CANNOT EXCLUDE - SciPy needs this!
        'doctest',
        'pywin32',  # Only include what we need via pywin32-ctypes
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PanelFlutterAnalysis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon='icon.ico' if you have an icon file
    version_file=None,
)
