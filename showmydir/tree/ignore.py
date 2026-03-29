from pathlib import Path

from pathspec import PathSpec

from .. import config  # noqa: TID252
from ..customExceptions import IgnoreManagerCompileNotCalledError  # noqa: TID252


class IgnoreManager:
    def __init__(self, pattens: list[str] | None = None) -> None:
        self.ignore_list = pattens or []

    def compile(self):
        self.spec = PathSpec.from_lines("gitwildmatch", self.ignore_list)

    def should_include(self, path: str) -> bool:
        if not hasattr(self, "spec"):
            raise IgnoreManagerCompileNotCalledError()
        return not self.spec.match_file(path)

    def load_gitignore_file(self, path: Path):
        path = path / ".gitignore"
        if not path.exists():
            return
        try:
            with path.open("r") as f:
                # read lines and add to list
                self.ignore_list.extend(
                    line.strip() for line in f if line.strip() and not line.strip().startswith("#")
                )
        except (PermissionError, FileNotFoundError):
            pass

    def add_pattern(self, pattern: list[str]):
        for item in pattern:
            self.ignore_list.extend(item.strip().split(","))

    def manage_pattern_list(
        self,
        no_default_ignores: bool,
        uv: bool,
        python: bool,
        node: bool,
        git: bool,
        editor: bool,
        docker: bool,
        rust: bool,
        to_file: str | None,
    ) -> list[str]:
        """
        Build the final ignore set based on user-selected options.

        Combines default ignore patterns with optional categories such as
        Python, Node.js, Git, Docker, etc. Also ensures the output file
        is excluded if specified.

        Args:
            no_default_ignores (bool): Disable default ignore patterns.
            uv (bool): Include uv-related ignores.
            python (bool): Include Python-related ignores.
            node (bool): Include Node.js-related ignores.
            git (bool): Include Git-related ignores.
            editor (bool): Include editor/OS-specific ignores.
            docker (bool): Include Docker-related ignores.
            rust (bool): Include Rust-related ignores.
            to_file (str | None): Output file name to ignore.

        Returns:
            list[str]: Final set of ignore patterns.
        """
        if not no_default_ignores:
            self.ignore_list.extend(config.DEFAULT_IGNORE_LIST)

        if uv:
            self.ignore_list.extend(config.UV_IGNORE_LIST)
        if python:
            self.ignore_list.extend(config.PYTHON_IGNORES)
        if node:
            self.ignore_list.extend(config.NODE_IGNORES)
        if git:
            self.ignore_list.extend(config.GIT_IGNORES)
        if editor:
            self.ignore_list.extend(config.EDITOR_IGNORES)
        if docker:
            self.ignore_list.extend(config.DOCKER_IGNORES)
        if rust:
            self.ignore_list.extend(config.RUST_IGNORES)

        if to_file:
            # if tree will genrate then it should also ignore that perticular file also
            # otherwise incomplete data may also show on tree
            self.ignore_list.append(Path(to_file).name)

        return self.ignore_list
