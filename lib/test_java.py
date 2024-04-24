import tree_sitter
from typing import List

JAVA_LANGUAGE = tree_sitter.Language("build/my-languages.so", "java")

parser = tree_sitter.Parser()
parser.set_language(JAVA_LANGUAGE)


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
with open("java_demo_class.java", "r") as file:
    source_code = file.read()

# Parse the Java code
tree = parser.parse(bytes(source_code, "utf8"))

root = tree.root_node
methods = []

for node in root.children:
    if node.type == "class_declaration":
        for child_node in node.children:
            if child_node.type == "class_body":
                for child_child_node in child_node.children:
                    if child_child_node.type == "method_declaration":
                        targets = find_nodes(child_child_node, "call_expression")
                        for target in targets:
                            is_sink_function = False
                            for sub_target in target.children:
                                if (
                                    sub_target.type == "identifier"
                                    and source_code[
                                        sub_target.start_byte : sub_target.end_byte
                                    ]
                                    == "println"
                                ):
                                    is_sink_function = True
                                    break
                            if is_sink_function:
                                for sub_target in target.children:
                                    if sub_target.type == "argument_list":
                                        print(
                                            source_code[
                                                sub_target.start_byte
                                                + 1 : sub_target.end_byte
                                                - 1
                                            ]
                                        )
                                        break
