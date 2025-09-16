# Installation Guide

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test Installation

```bash
python test_imports.py
```

### 3. Run Application

```bash
python main.py
```

Or use the helper script:

```bash
python run.py
```

## Dependencies

### Required Python Packages

- **customtkinter**: Modern GUI framework
- **numpy**: Numerical computing
- **scipy**: Scientific computing
- **matplotlib**: Plotting and visualization
- **pandas**: Data manipulation
- **pyNastran**: NASTRAN file handling
- **pillow**: Image processing (for customtkinter)

### Optional Dependencies

- **seaborn**: Enhanced plotting styles
- **plotly**: Interactive plotting
- **tqdm**: Progress bars

## Installation Methods

### Method 1: pip install (Recommended)

```bash
pip install customtkinter>=5.2.0 numpy scipy matplotlib pandas pyNastran pillow
```

### Method 2: Using requirements.txt

```bash
pip install -r requirements.txt
```

### Method 3: Conda Environment

```bash
conda create -n panel_flutter python=3.9
conda activate panel_flutter
pip install -r requirements.txt
```

## Troubleshooting

### Common Issues

#### 1. customtkinter Not Found

```bash
pip install customtkinter --upgrade
```

#### 2. No Display Available (Linux/Server)

If running on a headless server:

```bash
# Install virtual display
sudo apt-get install xvfb

# Run with virtual display
xvfb-run -a python main.py
```

#### 3. Import Errors

Test individual imports:

```python
python -c "import customtkinter; print('customtkinter OK')"
python -c "import numpy; print('numpy OK')"
python -c "import matplotlib; print('matplotlib OK')"
```

#### 4. Matplotlib Style Warning

If you see matplotlib style warnings, install seaborn:

```bash
pip install seaborn
```

### Platform-Specific Notes

#### Windows
- Ensure you have Visual C++ redistributables installed
- Use Command Prompt or PowerShell
- Python 3.8+ recommended

#### macOS
- May need to install tkinter separately: `brew install python-tk`
- Ensure Xcode command line tools are installed

#### Linux
- Install tkinter: `sudo apt-get install python3-tk`
- For Ubuntu/Debian: `sudo apt-get install python3-tkinter`

## Verification

After installation, run the test script:

```bash
python test_imports.py
```

Expected output:
```
✓ customtkinter imported successfully
✓ ThemeManager imported successfully
✓ ProjectManager imported successfully
✓ Material models imported successfully
✓ Utils imported successfully

Import test completed.
```

## Directory Structure

Ensure your directory structure looks like this:

```
panel-flutter/
├── main.py
├── run.py
├── test_imports.py
├── requirements.txt
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── theme_manager.py
│   ├── project_manager.py
│   └── panels/
├── models/
├── utils/
├── python_bridge/
└── nastran-aeroelasticity/
```

## Development Setup

For developers who want to modify the application:

```bash
# Clone with submodules
git clone --recursive https://github.com/your-repo/panel-flutter.git

# Or clone submodules separately
git submodule update --init --recursive

# Install in development mode
pip install -e .
```

## Configuration

The application creates a `config.json` file on first run. You can customize:

- Theme preferences
- NASTRAN executable path
- Default analysis parameters
- GUI scaling

Example config.json:
```json
{
  "appearance": {
    "theme": "dark",
    "color_theme": "blue",
    "scaling": 1.0
  },
  "nastran": {
    "executable": "nastran",
    "timeout": 3600
  }
}
```