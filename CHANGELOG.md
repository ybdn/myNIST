# Changelog

All notable changes to myNIST will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-21

### Added
- Initial release of myNIST
- 3-panel PyQt5 GUI interface
  - File panel: NIST record tree navigator
  - Data panel: Field data viewer (table format)
  - Image panel: Biometric image display
- NIST file parsing with nistitl (Idemia)
- Support for ANSI/NIST-ITL file format
- Record type support:
  - Type-1: Transaction Information
  - Type-2: User-Defined Descriptive Text
  - Type-4: High-Resolution Grayscale Fingerprint
  - Type-10: Facial & SMT Image
  - Type-13: Variable-Resolution Latent Image
  - Type-14: Variable-Resolution Fingerprint Image
  - Type-15: Variable-Resolution Palmprint Image
  - Type-17: Iris Image
- Export Signa Multiple functionality
  - Fixed rule: Delete field 2.215
  - Fixed rule: Set field 2.217 = "11707"
- File operations:
  - Open NIST files (.nist, .eft, .an2)
  - Export modified NIST files
- Image display with Pillow
- PyInstaller configuration for Ubuntu executable
- MVC architecture (Model-View-Controller)
- Comprehensive logging system
- Menu system with keyboard shortcuts
  - Ctrl+O: Open file
  - Ctrl+E: Export Signa Multiple
  - Ctrl+Q: Quit
- Status bar with operation feedback
- Build and run scripts (build.sh, run.sh)
- Unit tests with pytest
- Documentation:
  - README.md with installation guide
  - User guide (French)
  - Developer guide
  - Quick start guide
  - API documentation in docstrings

### Technical Details
- Python 3.8+ support
- Dependencies:
  - nistitl >= 0.6 (NIST parsing)
  - PyQt5 >= 5.15.0 (GUI framework)
  - Pillow >= 10.0.0 (Image processing)
  - pyinstaller >= 6.0.0 (Executable building)
- Ubuntu 20.04+ compatibility
- Fusion Qt style for modern appearance

### Known Limitations
- Read-only for most operations (except Export Signa Multiple)
- Single file processing (no batch mode)
- Type-7 and Type-8 image display not fully tested
- Export Signa Multiple rules are hardcoded
- No multi-language support (French documentation only)

### Future Improvements (Roadmap)
- [ ] Configurable export rules
- [ ] Batch file processing
- [ ] Field editing capabilities
- [ ] Image export functionality
- [ ] Search/filter in field data
- [ ] Recent files menu
- [ ] Dark theme support
- [ ] English documentation
- [ ] Cross-platform support (Windows, macOS)

## [Unreleased]

### Planned
- Configurable field modifications
- Batch export mode
- Advanced search in records
- Field validation
- Import/export of configuration

---

## Version History

- **[0.1.0]** - 2025-01-21 - Initial release

[0.1.0]: https://github.com/yourusername/mynist/releases/tag/v0.1.0
[Unreleased]: https://github.com/yourusername/mynist/compare/v0.1.0...HEAD
