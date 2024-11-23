import tree_sitter
from typing import List

C_LANGUAGE = tree_sitter.Language("build/my-languages.so", "cpp")

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

with open("../benchmark/C++/demo/01.cpp", "r") as file:
    source_code = file.read()

tree = parser.parse(bytes(source_code, "utf8"))

root = tree.root_node
all_function_nodes = []

all_function_header_nodes = find_nodes(tree.root_node, "function_definition")

function_declaration_nodes = []
for node in all_function_header_nodes:
    for child in node.children:
        print(child.type)

# for node in function_declaration_nodes:
#     function_name = ""
#     for sub_node in node.children:
#         if sub_node.type == "identifier":
#             function_name = source_code[sub_node.start_byte:sub_node.end_byte]
#             break
#         elif sub_node.type == "qualified_identifier":
#             qualified_function_name = source_code[sub_node.start_byte:sub_node.end_byte]
#             function_name = qualified_function_name.split("::")[-1]
#             break
#     print(function_name)

# for node in pointer_expressiones:
#     for child in node.children:
#         if child.type == "qualified_identifier":
#             qualified_function_name = source_code[child.start_byte:child.end_byte]
#             function_name = qualified_function_name.split("::")[-1]
#             print(function_name)
    
