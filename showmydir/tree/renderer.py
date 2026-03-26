from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.text import Text

from .scanner import ScanEngine
from .smd import node_to_dict
from .utils import choose_file_colour, format_node_size

if TYPE_CHECKING:
    from ..config import Node  # noqa: TID252


class TreeGenerator(ScanEngine):
    def __init__(
        self,
        root: Path,
        ignore_list: set[str],
        depth: int | None,
        show_size: bool,
        show_size_disk: bool,
        to_file: str | None,
        highlighted_files: set[str],
    ):
        super().__init__(
            root=root,
            ignore_list=ignore_list,
            depth=depth,
            show_size=show_size,
            show_size_disk=show_size_disk,
            to_file=to_file,
            highlighted_files=highlighted_files,
        )

        self.root_node = self.scan(self.root)

        self.console.print(f"\n{self.root}", style="cyan")
        TreeRenderer(
            show_disk=self.show_disk, show_size=self.show_size, console=self.console
        ).render(node=self.root_node)
        self.show_denied_files()
        self._summary_stats()

        self._file_closer()


class TreeRenderer:
    def __init__(
        self, show_disk: bool = True, show_size: bool = True, console: Console | None = None
    ) -> None:
        self.show_disk = show_disk
        self.show_size = show_size
        self.console = console or Console()

    def render(self, node: Node | None, prefix: str = ""):
        if node is None:
            return

        for i, child in enumerate(node.children, start=1):
            is_last: bool = i == len(node.children)
            connector = "└── " if is_last else "├── "

            name = child.name + "/" if child.is_dir else child.name
            text = Text()
            text.append(prefix)
            text.append(connector)
            text.append(name, style=choose_file_colour(child.is_dir, child.is_highlighted))

            formatted_size = format_node_size(
                node=child, show_disk=self.show_disk, show_size=self.show_size
            )
            if formatted_size.size:
                text.append(f" ({formatted_size.size})", style=formatted_size.colour)

            self.console.print(text)

            new_prefix = prefix + ("    " if is_last else "│   ")
            if child.is_dir:
                self.render(child, new_prefix)


class JsonRenderer(ScanEngine):
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
        self.root_node = self.scan(self.root)
        if self.root_node is None:
            raise typer.Exit(code=1)
        data = {
            "_format": "showmydir-v1",
            "meta": {
                "generated_by": "showmydir",
                "version": version("showmydir"),
                "root_path": str(self.root),
                "total_files": self.file_counts,
                "total_dirs": self.dir_counts,
            },
            "root": node_to_dict(self.root_node),
        }
        json.dump(data, self.console.file, indent=2, ensure_ascii=False)

        self._file_closer()


class FlatRenderer(ScanEngine):
    def render(self, node: Node | None, parent_path: Path = Path(), find_mode: bool = False):
        if node is None:
            return

        current_path = parent_path / node.name
        relative_path = current_path.relative_to(self.root)

        # avoids printing root twice
        if node.name != self.root.name or parent_path != Path():
            text = Text()
            text.append(
                str(relative_path), style=choose_file_colour(node.is_dir, node.is_highlighted)
            )
            formated_size = format_node_size(
                node, show_size=self.show_size, show_disk=self.show_disk
            )
            text.append(f" ({formated_size.size})", style=formated_size.colour)
            self.console.print(text)

        if node.is_dir and not find_mode:
            for child in node.children:
                self.render(child, current_path)

    def call_render(self, dir: Path):
        nodes = self.scan(dir)
        self.render(nodes)
