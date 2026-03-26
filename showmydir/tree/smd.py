from __future__ import annotations

import fnmatch

from ..config import Node, NodeDict  # noqa: TID252


def node_to_dict(node: Node) -> NodeDict:
    """
    Converts a Node object into a dictionary representation.

    This is used for serializing the tree into JSON or `.smd` format.
    """
    return {
        "name": node.name,
        "is_dir": node.is_dir,
        "size": node.size,
        "has_unknown_size": node.has_unknown_size,
        "logical_size": node.logical_size,
        "is_highlighted": node.is_highlighted,
        "children": [node_to_dict(child) for child in node.children],
    }


def dict_to_node(data: NodeDict) -> Node:
    """
    Reconstructs a Node object from its dictionary representation.

    Used when loading `.smd` or JSON files back into a tree structure.
    """
    return Node(
        name=data["name"],
        is_dir=data["is_dir"],
        size=data["size"],
        has_unknown_size=data["has_unknown_size"],
        logical_size=data["logical_size"],
        is_highlighted=data["is_highlighted"],
        children=[dict_to_node(child) for child in data["children"]],
    )


def search_smd(root_node: Node, pattern: str) -> list[Node]:
    matches: list[Node] = []

    def _search(node: Node):
        if fnmatch.fnmatch(node.name, pattern):
            matches.append(node)
        for child in node.children:
            _search(child)

    _search(root_node)
    return matches
