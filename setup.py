"""Setup script for NIST Studio application."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mynist",
    version="0.1.0",
    author="Yoann BAUDRIN",
    description="NIST Studio - Viewer and editor for ANSI/NIST-ITL biometric files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "nistitl>=0.6",
        "PyQt5>=5.15.0",
        "Pillow>=10.0.0",
        "imagecodecs>=2024.1.1",
    ],
    entry_points={
        'console_scripts': [
            'mynist=mynist.__main__:main',
        ],
        'gui_scripts': [
            'mynist-gui=mynist.__main__:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "License :: Other/Proprietary License",
    ],
    include_package_data=True,
)
