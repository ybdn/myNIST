# myNIST Developer Guide

## Architecture Overview

myNIST follows the **Model-View-Controller (MVC)** architecture pattern for clean separation of concerns.

### Components

#### Models ([mynist/models/](../mynist/models/))

**NISTFile** ([nist_file.py](../mynist/models/nist_file.py))
- Core model representing a parsed NIST file
- Uses nistitl library for parsing ANSI/NIST-ITL files
- Provides methods for:
  - Parsing NIST files
  - Extracting records by type
  - Modifying and deleting fields
  - Exporting modified files

#### Views ([mynist/views/](../mynist/views/))

**MainWindow** ([main_window.py](../mynist/views/main_window.py))
- Main application window
- Manages 3-panel layout using QSplitter
- Handles menu actions and file dialogs

**FilePanel** ([file_panel.py](../mynist/views/file_panel.py))
- Left panel displaying record tree structure
- Uses QTreeWidget to show NIST records
- Emits signals when records are selected

**DataPanel** ([data_panel.py](../mynist/views/data_panel.py))
- Middle panel showing field data
- Uses QTableWidget for field display
- Shows all non-empty fields for selected record

**ImagePanel** ([image_panel.py](../mynist/views/image_panel.py))
- Right panel for biometric images
- Uses QLabel with QPixmap for image display
- Supports multiple image formats via Pillow

#### Controllers ([mynist/controllers/](../mynist/controllers/))

**FileController** ([file_controller.py](../mynist/controllers/file_controller.py))
- Manages file operations
- Opens and closes NIST files
- Maintains current file state

**ExportController** ([export_controller.py](../mynist/controllers/export_controller.py))
- Handles export operations
- Implements "Export Signa Multiple" logic
- Applies fixed rules to Type-2 fields

## Development Setup

### 1. Clone and Setup

```bash
cd myNIST
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Development Mode

```bash
# Run directly
python -m mynist

# Or use the run script
./run.sh
```

### 3. Running Tests

```bash
# Install test dependencies
pip install pytest pytest-qt

# Run all tests
pytest

# Run specific test file
pytest tests/test_nist_file.py

# Run with coverage
pip install pytest-cov
pytest --cov=mynist tests/
```

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints where appropriate
- Document all public methods with docstrings
- Keep functions focused and small

### Example:

```python
def parse(self, filepath: Optional[str] = None) -> bool:
    """
    Parse NIST file.

    Args:
        filepath: Path to NIST file (uses self.filepath if not provided)

    Returns:
        True if parsing succeeded, False otherwise
    """
    # Implementation
```

### Import Organization

```python
# Standard library
import sys
from pathlib import Path

# Third-party
from PyQt5.QtWidgets import QWidget
import nistitl

# Local
from mynist.models.nist_file import NISTFile
from mynist.utils.logger import get_logger
```

## Adding New Features

### Adding a New Field Transformation

1. Update constants in [mynist/utils/constants.py](../mynist/utils/constants.py):

```python
SIGNA_MULTIPLE_RULES = {
    'delete_fields': [215, 216],  # Add new field
    'replace_fields': {
        217: "11707",
        218: "new_value"  # Add new replacement
    }
}
```

2. The ExportController will automatically apply new rules

### Adding a New Panel

1. Create new panel in [mynist/views/](../mynist/views/):

```python
from PyQt5.QtWidgets import QWidget

class NewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
```

2. Add to MainWindow in [main_window.py](../mynist/views/main_window.py):

```python
self.new_panel = NewPanel(self)
splitter.addWidget(self.new_panel)
```

### Adding a New Record Type

1. Update RECORD_TYPE_NAMES in [constants.py](../mynist/utils/constants.py)
2. If it's an image type, add to IMAGE_TYPES list
3. ImagePanel will automatically handle it

## Building and Distribution

### Building Executable

```bash
# Use build script
./build.sh

# Or manually
pyinstaller mynist.spec
```

### Customizing Build

Edit [mynist.spec](../mynist.spec):

- Add hidden imports
- Include additional data files
- Exclude unnecessary modules

```python
hiddenimports=[
    'nistitl',
    'new_module',  # Add here
],
excludes=[
    'matplotlib',  # Add modules to exclude
],
```

## Debugging

### Enable Debug Logging

In [mynist/utils/logger.py](../mynist/utils/logger.py):

```python
logger = setup_logger(APP_NAME, level=logging.DEBUG)
```

### PyQt5 Debugging

Run with PyQt5 debug mode:

```bash
export QT_DEBUG_PLUGINS=1
python -m mynist
```

### nistitl Debugging

Check parsed NIST structure:

```python
import nistitl
msg = nistitl.Message()
msg.parse(open('file.nist', 'rb').read())

# Inspect message
print(msg.records)
print(dir(msg))
```

## Common Development Tasks

### Adding a Menu Action

In [main_window.py](../mynist/views/main_window.py):

```python
def create_menus(self):
    menubar = self.menuBar()
    file_menu = menubar.addMenu('&File')

    new_action = QAction('&New Action', self)
    new_action.setShortcut('Ctrl+N')
    new_action.triggered.connect(self.on_new_action)
    file_menu.addAction(new_action)

def on_new_action(self):
    # Implementation
    pass
```

### Connecting Signals

```python
# In panel
from PyQt5.QtCore import pyqtSignal

class MyPanel(QWidget):
    data_changed = pyqtSignal(str)  # Define signal

    def some_method(self):
        self.data_changed.emit("data")  # Emit signal

# In main window
self.my_panel.data_changed.connect(self.on_data_changed)

def on_data_changed(self, data):
    # Handle signal
    pass
```

## Testing Guidelines

### Unit Tests

Test individual components in isolation:

```python
def test_nist_file_creation():
    nist_file = NISTFile()
    assert nist_file is not None
```

### Integration Tests

Test with actual NIST files (place in `tests/fixtures/`):

```python
def test_parse_real_nist():
    nist_file = NISTFile('tests/fixtures/sample.nist')
    assert nist_file.parse() is True
```

### GUI Tests (pytest-qt)

```python
def test_main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "myNIST - NIST File Viewer"
```

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `pytest`
4. Update documentation
5. Submit pull request

## Resources

- **nistitl documentation**: https://nistitl.readthedocs.io/
- **PyQt5 documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **ANSI/NIST-ITL standard**: https://www.nist.gov/itl/iad/image-group/ansinist-itl-standard-references
- **PyInstaller manual**: https://pyinstaller.org/en/stable/

## Troubleshooting

### Import Errors

Check PYTHONPATH includes project root:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### PyQt5 Not Found in Virtual Environment

```bash
pip install --force-reinstall PyQt5
```

### nistitl Parse Errors

Verify NIST file format:

```bash
file your_file.nist
hexdump -C your_file.nist | head
```

## Contact

For questions or issues, refer to the project README or create an issue in the repository.
