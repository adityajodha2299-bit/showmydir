import re
from pathlib import Path

from rich.console import Console

from . import config
from .config import CreateMode, Node
from .customExceptions import (
    CreateModeNotUpdatedError,
    GitIgnoreFileNotFoundError,
    InvalidNodeNameError,
)

# The string must start and end with one or more alphanumeric characters, underscores, hyphens, or periods.  # noqa: E501
SAFE_NAME_PATTERN = re.compile(r"^(?!.*\.{2})[\w\-.]+$")


def sanitize_name(name: str) -> str:
    """
    Sanitize a node name to prevent path traversal or unsafe characters.

    Only allows: a-z, A-Z, 0-9, _, -, .
    Rejects names containing slashes or '..'.
    """
    if not SAFE_NAME_PATTERN.match(name) or not name.strip():
        raise InvalidNodeNameError(name)
    return name


def handle_file(
    safe_name: str,
    parent: Path,
    mode: CreateMode,
    dry_run: bool,
    console: Console,
    indent: str,
):
    """
    Handle creation or overwrite behavior for a single file node.

    Depending on the selected mode (ASK, SKIP, FORCE), this function
    decides whether to create, skip, or overwrite a file. It also
    supports dry-run mode where no actual changes are made.

    Args:
        node (Node): File node containing metadata.
        parent (Path): Parent directory path where file will be created.
        mode (CreateMode): File handling strategy (ASK, SKIP, FORCE).
        dry_run (bool): If True, simulate actions without creating files.
        console (Console): Rich console instance for output.
        indent (str): Indentation used for structured printing.

    Raises:
        CreateModeNotUpdatedError: If an unknown mode is provided.
    """

    if mode == CreateMode.ASK:
        message = "[PROMPT]"
    elif mode == CreateMode.SKIP:
        message = "[SKIP]"
    elif mode == CreateMode.FORCE:
        message = "[FORCED]"

    current_path = parent / safe_name

    if current_path.exists():
        if dry_run:
            console.print(
                f"{indent}[red]{message}[/red] [green]{safe_name}[/green] "
                + ("(would ask)" if mode == CreateMode.ASK else "")
            )
        else:
            if mode == CreateMode.ASK:
                while True:
                    choice = (
                        console.input(
                            "[red]⚠️[/red] Conflicting file found, want to overwrite? [y/n]: "
                        )
                        .strip()
                        .lower()
                    )
                    if choice == "y":
                        current_path.write_text("")
                        break
                    if choice == "n":
                        break
                    console.print("Invalid choice...")
            elif mode == CreateMode.FORCE:
                current_path.touch()
            elif mode == CreateMode.SKIP:
                console.print(f"Successfully Skipped file: {safe_name}")
            else:
                raise CreateModeNotUpdatedError()
    else:
        if dry_run:
            console.print(f"{indent}[green]{safe_name}[/green]")
        else:
            current_path.touch()


def handle_dir(
    safe_name: str,
    parent: Path,
    mode: CreateMode,
    dry_run: bool,
    console: Console,
    indent: str = "   ",
):
    """
    Handle creation or overwrite behavior for a directory node.

    Creates directories or simulates creation based on the selected
    mode and dry-run setting. Unlike files, directories typically do
    not require overwrite confirmation.

    Args:
        node (Node): Directory node.
        parent (Path): Parent directory path.
        mode (CreateMode): Directory handling strategy.
        dry_run (bool): If True, simulate actions without creating directories.
        console (Console): Rich console instance for output.
        indent (str): Indentation used for structured printing.

    Raises:
        CreateModeNotUpdatedError: If an unknown mode is provided.
    """

    if mode == CreateMode.ASK:
        message = "[PROMPT]"
    elif mode == CreateMode.SKIP:
        message = "[SKIP]"
    elif mode == CreateMode.FORCE:
        message = "[OVERWRITE]"

    current_path = parent / safe_name

    if current_path.exists():
        if dry_run:
            console.print(
                f"{indent}[red]{message}[/red] [cyan]{safe_name}[/cyan] "
                + ("(would ask)" if mode == CreateMode.ASK else "")
            )
        else:
            if mode == CreateMode.ASK:
                # In both cases (overwrites or not) directory will always show no effect
                # dir no matter what/how, it will got created
                pass  # directories don't need overwrite confirmation
            elif mode == CreateMode.FORCE:
                current_path.mkdir(parents=True, exist_ok=True)
            elif mode == CreateMode.SKIP:
                console.print(f"Successfully Skipped directory: {safe_name}")
            else:
                raise CreateModeNotUpdatedError()
    else:
        if dry_run:
            console.print(f"{indent}[cyan]{safe_name}[/cyan]")
        else:
            current_path.mkdir(parents=True, exist_ok=True)


def create_dir(
    root_node: Node,
    parent: Path,
    dry_run: bool,
    mode: CreateMode,
    console: Console,
    final_ignore: set[str],
    level: int = 0,
    safe_dir_name: str | None = None,
):
    """
    Recursively create directory and file structure from a Node tree.

    Traverses the given Node structure and creates directories and files
    based on the selected mode. Supports dry-run to preview changes
    without modifying the filesystem.

    Args:
        root_node (Node): Root node of the directory structure.
        parent (Path): Base path where structure will be created.
        dry_run (bool): If True, simulate actions without creating files.
        mode (CreateMode): File/directory handling strategy.
        console (Console): Rich console instance for output.
        final_ignore (set[str]): Set of file/directory names to ignore.
        level (int, optional): Current recursion depth for indentation.

    Returns:
        None
    """
    try:
        safe_name = safe_dir_name or sanitize_name(root_node.name)
        current_path = parent / safe_name
        indent = "   " * level
        if root_node.is_dir:
            handle_dir(safe_name, parent, mode, dry_run, console, indent)

        for node in root_node.children:
            child_indent = "   " * (level + 1)
            try:
                child_safe_name = sanitize_name(node.name)
            except InvalidNodeNameError:
                continue
            if node.name in final_ignore:
                continue  # ignores the child who are in final ignore
            if node.is_dir:
                create_dir(
                    root_node=node,
                    parent=current_path,
                    dry_run=dry_run,
                    console=console,
                    mode=mode,
                    final_ignore=final_ignore,
                    level=level + 1,
                    safe_dir_name=child_safe_name,
                )
            else:
                handle_file(
                    safe_name=child_safe_name,
                    parent=current_path,
                    mode=mode,
                    dry_run=dry_run,
                    console=console,
                    indent=child_indent,
                )

    except InvalidNodeNameError:
        # try/except chamer is this huge because it ignores whole dir if its name is not safe
        console.print(f"[red]InvalidNode:[/red] {root_node.name}")


def user_setted_ignores(
    no_default_ignores: bool,
    uv: bool,
    python: bool,
    node: bool,
    git: bool,
    editor: bool,
    docker: bool,
    rust: bool,
    to_file: str | None,
) -> set[str]:
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
        set[str]: Final set of ignore patterns.
    """

    final_ignore: set[str] = set()
    if not no_default_ignores:
        final_ignore.update(config.DEFAULT_IGNORE_LIST)

    if uv:
        final_ignore.update(config.UV_IGNORE_LIST)
    if python:
        final_ignore.update(config.PYTHON_IGNORES)
    if node:
        final_ignore.update(config.NODE_IGNORES)
    if git:
        final_ignore.update(config.GIT_IGNORES)
    if editor:
        final_ignore.update(config.EDITOR_IGNORES)
    if docker:
        final_ignore.update(config.DOCKER_IGNORES)
    if rust:
        final_ignore.update(config.RUST_IGNORES)

    if to_file:
        final_ignore.add(Path(to_file).name)

    return final_ignore


def read_gitignore(operation_dir: Path) -> list[str]:
    """
    Read and parse a .gitignore file into a list of ignore patterns.

    Ignores empty lines and comments, and trims trailing slashes
    from directory entries.

    Args:
        operation_dir (Path): Directory containing the .gitignore file.

    Raises:
        GitIgnoreFileNotFoundError: If .gitignore file is not found.

    Returns:
        list[str]: List of ignore patterns.
    """

    git_ignore_file = operation_dir / ".gitignore"

    if not git_ignore_file.exists():
        raise GitIgnoreFileNotFoundError()

    # if exists then opens it
    with git_ignore_file.open() as f:
        temp_ignore_list: list[str] = []  # container to store ignoring files/dir
        for line in f:
            line = line.strip()  # clean a line

            if line.lstrip().startswith("#"):
                continue  # ignores for comment
            ig_part = line.strip()  # remove unwanted

            if ig_part != "":
                temp_ignore_list.append(ig_part.rstrip("/"))

    return temp_ignore_list
