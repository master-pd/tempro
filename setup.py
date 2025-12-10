#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="tempro-bot",
    version="2.0.0",
    author="Tempro Team",
    author_email="tempro@example.com",
    description="Telegram Bot for Temporary Email Generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/master-pd/tempro",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tempro-bot=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.json", "*.md"],
    },
)