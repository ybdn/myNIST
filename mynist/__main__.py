"""Entry point for myNIST application."""

import sys
from mynist.app import MyNISTApp


def main():
    """Main entry point."""
    app = MyNISTApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
