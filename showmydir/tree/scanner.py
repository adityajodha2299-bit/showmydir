from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from secrets import choice as secret_choice

from rich.console import Console
from rich.style import Style
from rich.text import Text

# private files
from ..config import Bytes, MetaData, Node  # noqa: TID252
from .utils import format_bytes


class BaseGenerator:
    def __init__(
        self,
        root: Path,
        ignore_list: set[str],
        depth: int | None,
        show_size: bool,
        show_size_disk: bool,
        to_file: str | None,
        highlighted_files: set[str],
    ) -> None:
        self.root: Path = root.resolve()
        self.ignore_list: set[str] = ignore_list
        self.max_depth: int | None = depth
        self.show_size: bool = show_size
        self.show_disk: bool = show_size_disk
        self._file = to_file
        self.highlighted_files = highlighted_files

        self.dir_counts: int = 0
        self.file_counts: int = 0
        self.total_size: float = 0

        self.console = (
            Console() if not self._file else Console(file=self._file_opener(Path(self._file)))
        )

        self.permission_error_files_dirs: list[str] = []

    def _file_opener(self, __file: Path, mode: str = "w"):
        self.f = open(__file, mode)  # type: ignore  # noqa: PTH123, SIM115
        return self.f

    def _file_closer(self):
        if hasattr(self.console, "file") and self.console.file:
            self.console.file.close()

    def _get_entries(self, path: Path) -> list[os.DirEntry[str]]:
        try:
            return sorted(
                [e for e in os.scandir(path) if not self._is_ignored(e.name)],
                key=lambda e: (not e.is_dir(), e.name.lower()),
            )
        except PermissionError as e:
            self.permission_error_files_dirs.append(str(e))
            return []

    def _summary_stats(self):
        _size_data = format_bytes(bytes_size=self.total_size, dim=False)
        dir_size, colour_ = _size_data.size, _size_data.colour
        self.console.print()
        self.console.print(
            f"[bold]📊 {self.file_counts} files, {self.dir_counts} folders/directories[/bold]"
        )
        self.console.print()
        text = Text("💾 Total size: ", style="bold")
        text.append(dir_size, style=colour_)
        self.console.print(text)

    def show_denied_files(self):
        if self.permission_error_files_dirs:
            self.console.print("\n[Permission Denied for these files/folders]:", style="bold red")

            # Pick one color randomly for this run
            dim_colors = ["grey50", "grey62", "grey70", "light_slate_gray", "grey35", "grey42"]
            chosen_color = secret_choice(dim_colors)
            style = Style(color=chosen_color)

            for path in self.permission_error_files_dirs:
                clear_path = Path(
                    (path.split(":", 1)[-1]).strip().removeprefix("'").removesuffix("'")
                )

                text = Text(f"  • {clear_path}", style=style)
                self.console.print(text)

    def _is_ignored(self, name: str) -> bool:
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.ignore_list)

    def _is_highlighted(self, name: str) -> bool:
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.highlighted_files)

    def _extract_metadata(self, entry: Path, stat: os.stat_result | None) -> MetaData:
        if stat is None:
            return MetaData(entry.name, None, False)

        if entry.is_dir():
            return MetaData(entry.name, stat.st_size, True)

        return MetaData(entry.name, stat.st_size, False)


class ScanEngine(BaseGenerator):
    def __init__(
        self,
        root: Path,
        ignore_list: set[str],
        depth: int | None,
        show_size: bool,
        show_size_disk: bool,
        to_file: str | None,
        highlighted_files: set[str],
    ) -> None:
        super().__init__(
            root, ignore_list, depth, show_size, show_size_disk, to_file, highlighted_files
        )

    def scan(self, path: Path, current_depth: int = 0) -> Node | None:
        if self.max_depth is not None and current_depth > self.max_depth:
            return None

        try:
            stat = path.stat()
        except (
            PermissionError,
            FileNotFoundError,
        ):  # some files change thier path while scanning
            stat = None

        _path_data = self._extract_metadata(entry=path, stat=stat)
        dir_file_name, size, is_dir = _path_data.name, _path_data.size, _path_data.is_dir
        highlighted = self._is_highlighted(path.name)

        has_unknown_size: bool = size is None
        logical_size: Bytes = size if not is_dir and size is not None else 0

        node = Node(
            name=dir_file_name,
            is_dir=is_dir,
            size=size,
            has_unknown_size=has_unknown_size,
            logical_size=logical_size,
            is_highlighted=highlighted,
        )

        if is_dir:
            if current_depth > 0:
                self.dir_counts += 1
            for entry in self._get_entries(path):
                child_node = self.scan(Path(entry.path), current_depth=current_depth + 1)
                if child_node is not None:
                    node.children.append(child_node)
                    node.logical_size += child_node.logical_size

                    if child_node.has_unknown_size:
                        node.has_unknown_size = True
        else:
            self.file_counts += 1
            self.total_size += node.size or 0

        return node
