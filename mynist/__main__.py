"""Entry point for NIST Studio application."""

import sys
from mynist.app import NISTStudioApp


def main():
    """Main entry point."""
    app = NISTStudioApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
