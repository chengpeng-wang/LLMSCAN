import tree_sitter
from typing import List

C_LANGUAGE = tree_sitter.Language("build/my-languages.so", "c")

parser = tree_sitter.Parser()
parser.set_language(C_LANGUAGE)


def find_nodes(root_node: tree_sitter.Node, node_type: str) -> List[tree_sitter.Node]:
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

# Read the Java file
with open("../benchmark/C/demo/01.c", "r") as file:
    source_code = file.read()

# Parse the Java code
tree = parser.parse(bytes(source_code, "utf8"))

root = tree.root_node
functions = {}

nodes = find_nodes(root, "pointer_declarator")

for node in nodes:
    for child in node.children:
        print(child.type)