from ..config import Bytes, FormatedSize, Node, colour  # noqa: TID252


def format_bytes(bytes_size: Bytes | float | None, dim: bool = True) -> FormatedSize:
    if bytes_size is None:  # for permission errors
        return FormatedSize("no access", "red")
    if bytes_size < 1024:
        return FormatedSize(f"{bytes_size} B", "dim white" if dim else "white")
    if bytes_size < 1_048_576:
        return FormatedSize(f"{bytes_size / 1024:.2f} KB", "dim green" if dim else "green")
    if bytes_size < 1_073_741_824:
        return FormatedSize(f"{bytes_size / 1_048_576:.2f} MB", "dim yellow" if dim else "yellow")
    return FormatedSize(f"{bytes_size / 1_073_741_824:.2f} GB", "dim red" if dim else "red")


def choose_file_colour(is_dir: bool, is_highlighted: bool) -> colour:
    if is_highlighted:
        return "bold bright_blue"
    if is_dir:
        return "cyan"
    return "green"


def format_node_size(
    node: Node, show_size: bool, show_disk: bool, dim: bool = True
) -> FormatedSize:
    parts = []

    size_data = format_bytes(node.logical_size, dim)
    logical_str = size_data.size

    if show_size:  # if should show size
        if node.has_unknown_size:
            parts.append(f"{logical_str} (~)")  # AND system dont allow the actual size of file/dir
        else:
            parts.append(logical_str)  # AND system allow to get size of dir/file

    # for directories, also show disk size if not false
    if node.is_dir:
        disk_data = format_bytes(node.size, dim)
        disk_size, disk_colour = disk_data.size, disk_data.colour
        if show_disk:
            parts.append(f"Disk: {disk_size}")
        return FormatedSize((" | ").join(parts), (size_data.colour if show_disk else disk_colour))

    # Now here only files remains
    if show_size:
        return FormatedSize(logical_str, size_data.colour)
    return FormatedSize("", "")
