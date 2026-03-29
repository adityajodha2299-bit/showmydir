import json
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console

from .config import CreateMode, Mode, Node, ViewMode
from .helper_main import create_dir, user_setted_ignores
from .tree.ignore import IgnoreManager
from .tree.renderer import FlatRenderer, JsonRenderer, TreeGenerator, TreeRenderer
from .tree.smd import dict_to_node, search_smd

app = typer.Typer(
    help=" Show directory tree (like 'tree') with smart ignore options and depth control."
)


@app.command()
def create_tree(
    smd_path: Path,
    parent: Path | None = None,
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate creation"),
    mode: CreateMode = typer.Option(  # noqa: B008
        CreateMode.SKIP,
        "--mode",
        help="File creation mode: skip (default), ask, or force overwrite",
    ),
    #
    # --- IGNORES ---
    ignore: list[str] = typer.Option(  # noqa: B008
        [],
        "--ignore",
        "-I",
        help="Ignore files or folders (comma-separated or multiple use)."
        " Example: -I '*.log,node_modules'",
    ),
    uv: bool = typer.Option(
        False, "--uv", help="Apply common Python/uv ignore patterns (.venv, pyproject.toml, etc.)"
    ),
    no_default_ignores: bool = typer.Option(
        False,
        "--no-default-ignores",
        help="Disable built-in ignore list (node_modules, .git, etc.)",
    ),
    python: bool = typer.Option(False, "--python-ignore", help="Ignore Python-related files"),
    node: bool = typer.Option(False, "--node-ignore", help="Ignore Node.js-related files"),
    git: bool = typer.Option(False, "--git-ignore", help="Ignore Git-related files"),
    editor: bool = typer.Option(False, "--editor-ignore", help="Ignore editor/OS files"),
    docker: bool = typer.Option(False, "--docker-ignore", help="Ignore Docker-related files"),
    rust: bool = typer.Option(False, "--rust-ignore", help="Ignore Rust-related files"),
):

    parent = parent or Path.cwd()
    smd_path = smd_path.resolve()
    console = Console()

    if not smd_path.exists() or not parent.exists():
        console.print("❌ File/Parent not found", style="bold red")
        raise typer.Exit(code=1)

    with smd_path.open("rt") as f:
        data = json.load(f)

    if data.get("_format") != "showmydir-v1":
        console.print(f"[bold red]❌ Unsupported format:[/bold red] {data.get('_format')}")
        raise typer.Exit(1)

    # Ignores the final
    final_ignore = user_setted_ignores(
        no_default_ignores=no_default_ignores,
        uv=uv,
        python=python,
        node=node,
        git=git,
        editor=editor,
        docker=docker,
        rust=rust,
        to_file=None,
    )
    if ignore:
        for item in ignore:
            for part in item.split(","):
                final_ignore.add(part.strip())

    root_node: Node = dict_to_node(data.get("root"))

    while True:
        answer = input("⚠️ This will create files. Continue? (y/n):") if not dry_run else "y"
        answer = answer.strip().lower()

        if answer == "y":
            console.print(
                "[red][DRY RUN MODE][/red]: (no files will be created)"
            ) if dry_run else ""
            create_dir(
                root_node=root_node,
                parent=parent,
                dry_run=dry_run,
                console=console,
                mode=mode,
                final_ignore=final_ignore,
            )
            break
        if answer == "n":
            typer.echo("Process canceled by user")
            break
        typer.echo("Invalid choice: ❌")


@app.command(help="Installs the .smd extension in vscode")
def install_showmydir_extension():
    vsix_path = Path(__file__).parent / "showmydir-syntax-0.0.1.vsix"
    code_cli = shutil.which("code")  # Only allow existing code CLI

    if not code_cli:
        typer.echo("⚠️ VS Code CLI not found in PATH")
        return

    subprocess.run([code_cli, "--install-extension", str(vsix_path)], check=True)  # noqa: S603
    print("✅ ShowMyDir syntax installed!")


@app.command()
def view(
    file_: Path,
    mode: ViewMode = typer.Option(ViewMode.TREE, "--mode", help="Mode: tree, flat, json"),  # noqa: B008
    show_size: bool = typer.Option(True, "--show-size/--no-show-size"),
    show_disk_size: bool = typer.Option(True, "--show-disk-size/--no-show-disk-size"),
    find: str = typer.Option(None, "--search", "-sch", help="Search .smd/.json file"),
):
    if not file_.exists():
        typer.echo("No such file found")
        raise typer.Exit(code=1)

    with file_.open("rt") as f:
        data = json.load(f)

    if data.get("_format") != "showmydir-v1":
        typer.echo(f"Unsupported format: {data.get('_format')}", err=True)
        raise typer.Exit(1)

    root_dict = data["root"]
    root_node = dict_to_node(root_dict)

    if find:
        match_nodes = search_smd(root_node, find)
        flat = FlatRenderer(
            root=file_,
            pathspecs=IgnoreManager(),
            depth=None,
            show_size=show_size,
            show_size_disk=show_disk_size,
            to_file=None,
            highlighted_files=set(),
        )
        for match in match_nodes:
            flat.render(match, Path(file_), find_mode=True)
    elif mode == ViewMode.JSON:
        typer.echo(json.dumps(data, indent=2))
    elif mode == ViewMode.TREE:
        TreeRenderer(show_size=show_size, show_disk=show_disk_size).render(root_node)
    elif mode == ViewMode.FLAT:
        flat = FlatRenderer(
            root=file_,
            depth=None,
            show_size=show_size,
            show_size_disk=show_disk_size,
            to_file=None,
            highlighted_files=set(),
            pathspecs=IgnoreManager(),
        )
        flat.render(
            node=root_node,
        )


@app.command()
def tree(
    # ignores
    ignore: list[str] = typer.Option(  # noqa: B008
        [],
        "--ignore",
        "-I",
        help="Ignore files or folders (comma-separated or multiple use)."
        " Example: -I '*.log,node_modules'",
    ),
    uv: bool = typer.Option(
        False,
        "--uv-ignore",
        help="Apply common Python/uv ignore patterns (.venv, pyproject.toml, etc.)",
    ),
    no_default_ignores: bool = typer.Option(
        False,
        "--no-default-ignores",
        help="Disable built-in ignore list (node_modules, .git, etc.)",
    ),
    python: bool = typer.Option(False, "--python-ignore", help="Ignore Python-related files"),
    node: bool = typer.Option(False, "--node-ignore", help="Ignore Node.js-related files"),
    git: bool = typer.Option(False, "--git-ignore", help="Ignore Git-related files"),
    editor: bool = typer.Option(False, "--editor-ignore", help="Ignore editor/OS files"),
    docker: bool = typer.Option(False, "--docker-ignore", help="Ignore Docker-related files"),
    rust: bool = typer.Option(False, "--rust-ignore", help="Ignore Rust-related files"),
    depth: int | None = typer.Option(
        None, "--depth", "-d", help="Limit recursion depth (e.g., -d 2)"
    ),
    root: Path | None = typer.Option(  # noqa: B008
        None,
        "--root",
        "-r",
        "--path",
        help="Root directory (default: current directory)",
    ),
    show_size: bool = typer.Option(
        True,
        "--show-size/--no-show-size",
        help="Toggle file size display",
    ),
    show_disk_size: bool = typer.Option(
        False, "--show-disk-size/--no-show-disk-size", help="Toggle dir disk size display"
    ),
    mode_of_viewing: Mode = typer.Option(  # noqa: B008
        Mode.TREE,
        "--mode",
        help="Mode: tree (default), flat, json",
    ),
    git_ignore: bool = typer.Option(
        True,
        "--gitignore/--no-gitignore",
        help="Reads gitignore files and excludes those files",
    ),
    highlights: list[str] = typer.Option(  # noqa: B008
        [],
        "--highlight",
        help="Highlight files matching patterns (e.g. '*.py', 'main.py')",
    ),
    file_saver: str = typer.Option(
        None,
        "--output",
        "-o",
        help="save the tree into file.",
    ),
):
    final_ignore = set()
    highlighted_set = set() if not highlights else set(highlights)

    # Checks the correct root path
    operation_dir = (root or Path.cwd()).resolve()
    if not operation_dir.exists():
        typer.echo(f"PathNotFoundError: {operation_dir} not exists")
        raise typer.Exit(code=1)

    # PathSpecs Ignores
    pt_specs_ig = IgnoreManager()
    pt_specs_ig.manage_pattern_list(
        no_default_ignores=no_default_ignores,
        uv=uv,
        python=python,
        node=node,
        git=git,
        editor=editor,
        docker=docker,
        rust=rust,
        to_file=file_saver,
    )
    pt_specs_ig.add_pattern(ignore)
    if git_ignore:
        pt_specs_ig.load_gitignore_file(operation_dir)
    pt_specs_ig.compile()

    # if user stated some ignores files/dirs
    if ignore:
        for item in ignore:
            for part in item.split(","):
                final_ignore.add(part.strip())

    # Mode of viewing
    if mode_of_viewing == Mode.TREE:
        TreeGenerator(
            root=operation_dir,
            ignore=pt_specs_ig,
            depth=depth,
            show_size=show_size,
            show_size_disk=show_disk_size,
            to_file=file_saver,
            highlighted_files=highlighted_set,
        )
    elif mode_of_viewing == Mode.FLAT:
        FlatRenderer(
            root=operation_dir,
            depth=depth,
            show_size=show_size,
            show_size_disk=show_disk_size,
            to_file=file_saver,
            highlighted_files=highlighted_set,
            pathspecs=pt_specs_ig,
        ).call_render(operation_dir)

    elif mode_of_viewing == Mode.JSON:
        file_name = Path(file_saver) if file_saver else None
        if file_name and file_name.suffix not in [".smd", ".json"]:
            typer.echo("JSON mode requires .smd or .json file", err=True)
            raise typer.Exit(1)

        JsonRenderer(
            root=operation_dir,
            ignore=pt_specs_ig,
            depth=depth,
            show_size=show_size,
            show_size_disk=show_disk_size,
            to_file=file_saver,
            highlighted_files=highlighted_set,
        )

    elif mode_of_viewing == Mode.SUMMARY:
        typer.echo("summary mode coming soon...")


# @app.callback()
def terminal_user_interface():
    pass


def main():
    app(prog_name="showmydir")


if __name__ == "__main__":
    main()
