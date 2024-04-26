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
with open("c_demo_program.c", "r") as file:
    source_code = file.read()

# Parse the Java code
tree = parser.parse(bytes(source_code, "utf8"))

root = tree.root_node
methods = {}

nodes = find_nodes(root, "call_expression")
for node in nodes:
    for child in node.children:
        if child.type == "identifier":
            method_name = source_code[child.start_byte: child.end_byte]
            print(method_name)




# nodes = find_nodes(root, "assignment_expression")
#
# # Find local_variable_declaration
# nodes.extend(find_nodes(root, "declaration"))
#
# # Extract the name info and line number
# lines = []
# for node in nodes:
#     is_src_node = False
#     for child in node.children:
#         if (
#                 child.type == "number_literal"
#                 and source_code[child.start_byte: child.end_byte] in {"0", "0.0", "0.0f", "0.0F"}
#         ):
#             is_src_node = True
#         if child.type == "call_expression":
#             for sub_child in child.children:
#                 if sub_child.type == "identifier":
#                     function_name = source_code[sub_child.start_byte:sub_child.end_byte]
#                     if function_name in {"atoi", "atof"}:
#                         is_src_node = True
#                         break
#     if is_src_node:
#         for child in node.children:
#             if child.type == "identifier":
#                 name = source_code[child.start_byte: child.end_byte]
#                 line_number = source_code[: child.start_byte].count("\n") + 1
#                 lines.append((name, line_number))
#                 print(name, line_number)