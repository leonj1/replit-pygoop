"""
Setup script for PyGoop.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pygoop",
    version="0.1.0",
    author="PyGoop Team",
    author_email="info@pygoop.example.com",
    description="A Python web crawler and scraping library inspired by the Golang 'goop' project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pygoop/pygoop",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.3",
        "click>=8.0.0",
        "validators>=0.18.0",
    ],
    entry_points={
        "console_scripts": [
            "pygoop=pygoop.cli:cli",
        ],
    },
)
