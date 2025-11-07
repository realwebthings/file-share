#!/usr/bin/env python3
"""
FileShare - Secure File Sharing Server
A simple HTTP server to share files between devices on the same network.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fileshare-server",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Secure file sharing server for local networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fileshare-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    entry_points={
        "console_scripts": [
            "fileshare=auth_server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.html"],
    },
)