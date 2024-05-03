from typing import *
import tree_sitter
from pathlib import Path


def obfuscate(source_code):
    def find_nodes(
        root_node: tree_sitter.Node, node_type: str
    ) -> List[tree_sitter.Node]:
        """
        Find all the nodes with node_type type underlying the root node.
        :param root_node: root node
        :return the list of the nodes with node_type type
        """
        nodes = []
        if root_node.type == node_type:
            nodes.append(root_node)

        for child_node in root_node.children:
            nodes.extend(find_nodes(child_node, node_type))
        return nodes

    cwd = Path(__file__).resolve().parent.parent.absolute()
    TSPATH = cwd / "../lib/build/"
    language_path = TSPATH / "my-languages.so"

    C_LANGUAGE = tree_sitter.Language(str(language_path), "c")

    parser = tree_sitter.Parser()
    parser.set_language(C_LANGUAGE)

    t = parser.parse(bytes(source_code, "utf8"))
    root_node = t.root_node
    nodes = find_nodes(root_node, "comment")

    new_code = source_code

    for node in nodes:
        comment = source_code[node.start_byte : node.end_byte]
        new_code = new_code.replace(comment, "\n" * comment.count("\n"))

    new_code = (
        new_code.replace("good", "foo")
        .replace("bad", "hoo")
        .replace("G2B", "xx")
        .replace("B2G", "yy")
    )
    return new_code


def add_line_numbers(source_code):
    line_number = 0
    new_lines = []
    for line in source_code.split("\n"):
        line_number += 1
        new_line = str(line_number) + "  " + line
        new_lines.append(new_line)
    return "\n".join(new_lines)
