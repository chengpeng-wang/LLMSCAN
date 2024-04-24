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

# for node in find_nodes(root, "call_expression"):
#     for sub_child in node.children:
#         # if sub_child.type == "argument_list":
#         #     for sub_sub_child in sub_child.children:
#         #         print(sub_sub_child.type)
#         #         if sub_sub_child.type == "pointer_expression":
#         #             for sub_sub_sub_child in sub_sub_child.children:
#         #                 if sub_sub_sub_child.type == "identifier":
#         #                     print(source_code[sub_sub_sub_child.start_byte:sub_sub_sub_child.end_byte])
#         if sub_child.type == "compound_statement":
#             for sub_sub_child in sub_child.children:
#                 print(sub_sub_child.type)
#             if sub_child.type == "function_declarator":
#                 for sub_sub_children in sub_child.children:
#                     # if sub_sub_children.type == "identifier":
#                     #     method_name = source_code[
#                     #                   sub_sub_children.start_byte: sub_sub_children.end_byte
#                     #                   ]
#                     #     method_code = source_code[
#                     #                   node.start_byte: node.end_byte
#                     #                   ]
#                     #     print(method_name)
#                     #     break
#                     print(sub_sub_children.type)
#                     if sub_sub_children.type == "parameter_list":
#                         for subnode in sub_sub_children.children:
#                             if subnode.type == "parameter_declaration":
#                                 for subsubnode in subnode.children:
#                                     print(subsubnode.type)
#
#                 if method_name != "" and method_code != "":
#                     break
#         method_id = len(methods) + 1
#         methods[method_id] = (method_name, method_code)
#
# # for node in find_nodes(root, "assignment_expression"):
# #     for sub_node in node.children:
# #         print(sub_node.type)
# #         # if sub_node.type == "identifier":
# #         #     print(source_code[sub_node.start_byte:sub_node.end_byte])
#
# exit(0)

for node in find_nodes(root, "if_statement"):
    for sub_node in node.children:
        print("-----------------------------------")
        print(sub_node.type)
        print("-----------------------------------")
        print(source_code[sub_node.start_byte:sub_node.end_byte])

        # print("-----------------------------------")
        # print(source_code[sub_node.start_byte:sub_node.end_byte])
        # for sub_sub_node in sub_node.children:
        #     print("---------------------------")
        #     print(sub_sub_node.type)
        #     print(source_code[sub_sub_node.start_byte:sub_sub_node.end_byte])
        # print("-----------------------------------")
        # print(source_code[sub_node.start_byte:sub_node.end_byte])
        # if sub_node.type != "function_declarator":
        #     continue
        # for sub_sub_node in sub_node.children:
        #     if sub_sub_node.type == "identifier":
        #         print(source_code[sub_sub_node.start_byte:sub_sub_node.end_byte])


# for node in root.children:
#     if node.type == "function_definition":
#         print(source_code[node.start_byte:node.end_byte])
        # for sub_node in node.children:
        #     for sub_sub_node in sub_node.children:
        #         if sub_sub_node.type == "parameter_list":
        #             for sub4node in sub_sub_node.children:
        #                 if sub4node.type == "parameter_declaration":
        #                     idenNode = find_nodes(sub4node, "identifier")[0]
        #                     print(source_code[idenNode.start_byte:idenNode.end_byte])



    #     for sub_child in node.children:
    #
    #         if sub_child.type == "compound_statement":
    #             # print(sub_child.type)
    #             for subsubchild in sub_child.children:
    #                 if subsubchild.type == "declaration":
    #                     # print(sub_child.type)
    #                     for subnode in subsubchild.children:
    #                         print(subnode.type)
    #                 # if sub_sub_child.type == "expression_statement":
    #                 #     for sub_sub_sub_child in sub_sub_child.children:
    #                 #         for sub_node in sub_sub_sub_child.children:
    #                 #             if sub_node.type == "argument_list":
    #                 #                 for sub_sub_node in sub_node.children:
    #                 #                     print(sub_sub_node.type)
    #
    #
    #
    #
    #                         # if sub_sub_child.type == "if_statement":
    #                         #     print(sub_sub_child.type)
    #                         #     print(source_code[sub_sub_child.start_byte:sub_sub_child.end_byte])
    #
    #                 # if sub_child.type == "function_declarator":
    #                 #     # print(sub_child.type)
    #                 #     # print(source_code[sub_child.start_byte:sub_child.end_byte])
    #                 #     for sub_sub_children in sub_child.children:
    #                 #         # print(sub_sub_children.type)
    #                 #         if sub_sub_children.type == "identifier":
    #                 #             print(source_code[sub_sub_children.start_byte:sub_sub_children.end_byte])
    #                 #         # if sub_sub_children.type == "parameter_list":
    #                 #         #     for para_node in sub_sub_children.children:
    #                 #         #         if para_node.type not in {"(", ")", ","}:
    #                 #         #             for para_sub_node in para_node.children:
    #                 #         #                 if para_sub_node.type == "identifier":
    #                 #         #                     print(para_sub_node.type)
    #                 #         #                     print(source_code[para_sub_node.start_byte:para_sub_node.end_byte])


