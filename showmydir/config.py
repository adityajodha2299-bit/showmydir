from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypedDict


class Mode(str, Enum):
    TREE = "tree"
    FLAT = "flat"
    JSON = "json"
    SUMMARY = "summary"


class CreateMode(str, Enum):
    ASK = "ask"
    SKIP = "skip"
    FORCE = "force"


class ViewMode(str, Enum):
    FLAT = "flat"
    JSON = "json"
    TREE = "tree"


colour = str
Bytes = int


@dataclass
class Node:
    """
    Represents a file or directory in the tree.

    Attributes:
        name: Name of the file/directory
        is_dir: True if directory, False if file
        size: Actual file size (None if unknown)
        has_unknown_size: Whether size could not be determined
        logical_size: Aggregated size (used for directories)
        is_highlighted: Whether node matches highlight patterns
        children: List of child nodes (for directories)
    """

    name: str
    is_dir: bool
    size: Bytes | None
    has_unknown_size: bool
    logical_size: Bytes
    is_highlighted: bool
    children: list[Node] = field(default_factory=list)


class NodeDict(TypedDict, total=True):
    """Dictionary representation of Node used for JSON serialization."""

    name: str
    is_dir: bool
    size: int | None
    has_unknown_size: bool
    logical_size: int
    is_highlighted: bool
    children: list[NodeDict]


@dataclass
class MetaData:
    """Stores basic metadata for a file or directory."""

    name: str
    size: Bytes | None
    is_dir: bool


@dataclass
class FormatedSize:
    """Represents a human-readable file size with display color."""

    size: str
    colour: colour


# ===============================
# Default Ignore Groups
# ===============================


# Common directories/files ignored by default
DEFAULT_IGNORE_LIST = [
    "node_modules",
    ".git",
    "__pycache__",
    "bin",
    "dist",
    "*_venv",
    ".venv",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".DS_Store",
    ".idea",
    ".vscode",
]

UV_IGNORE_LIST = [
    ".venv",
    "pyproject.toml",
    "uv.lock",
    "uv.toml",
    ".gitignore",
    "README.md",
    ".python-version",
    ".env",
    "requirements.txt",
    "poetry.lock",
]

# Python-specific
PYTHON_IGNORES = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    "pip-wheel-metadata",
    "dist",
    "build",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".coverage",
    "htmlcov",
]

# Node.js-specific
NODE_IGNORES = [
    "node_modules",
    "npm-debug.log",
    "yarn-error.log",
    "package-lock.json",
    "yarn.lock",
    ".pnpm-store",
]

# Git-specific
GIT_IGNORES = [
    ".git",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
]

# Editor / OS-specific
EDITOR_IGNORES = [
    ".DS_Store",
    "Thumbs.db",
    ".idea",
    ".vscode",
    "*.swp",
    "*.swo",
    "*~",
    ".directory",
    ".Spotlight-V100",
    ".Trashes",
]

# Docker / container related
DOCKER_IGNORES = [
    "Dockerfile",
    "docker-compose.yml",
    ".dockerignore",
    "*.tar",
    "*.tar.gz",
]

# Rust / Cargo
RUST_IGNORES = [
    "target",
    "Cargo.lock",
    "Cargo.toml",
]
