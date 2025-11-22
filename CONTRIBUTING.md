# Contributing to NIST Studio

Thank you for your interest in contributing to NIST Studio. This document provides guidelines for contributions.

## Development Setup

### Prerequisites

- Python 3.8+
- Git

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/ybdn/myNIST.git
cd myNIST

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-qt pytest-cov flake8 black

# Or use Make
make setup
```

### Running the Application

```bash
python -m mynist
# or
./run.sh
```

## Code Style

This project uses:
- **black** for code formatting (line length: 100)
- **flake8** for linting (max line length: 100)

Before submitting:

```bash
make format  # Auto-format code
make lint    # Check for issues
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_controllers.py -v
```

Tests are located in `tests/` and use fixtures from `tests/fixtures/`.

## Project Architecture

NIST Studio follows an MVC pattern:

```
mynist/
├── controllers/   # Business logic
├── models/        # Data model (NISTFile)
├── views/         # UI components (PyQt5)
├── utils/         # Utilities
└── resources/     # Icons and assets
```

See [docs/developer_guide.md](docs/developer_guide.md) for detailed architecture documentation.

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass: `make test`
4. Ensure code is formatted: `make format && make lint`
5. Update documentation if needed
6. Submit a pull request with a clear description

## Reporting Issues

When reporting issues, please include:
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Error messages if any

## License

By contributing, you agree that your contributions will be subject to the project's proprietary license. See [LICENSE](LICENSE) for details.

## Contact

For questions or discussions, please open an issue on GitHub.
