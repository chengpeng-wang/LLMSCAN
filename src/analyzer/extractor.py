import sys
from os import path
import tree_sitter

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from parser.program_parser import *
from typing import Tuple, List


def find_dbz_src(source_code: str, root_node: tree_sitter.Node):
    # TODO: This function should be synthesized automatically
    """
    Find source values for dbz detection
    :param source_code: The source code
    :param root_node: The root node of the parse tree
    :return: The variable names and line numbers of source values
    """
    # Find assignment_expression
    nodes = TSAnalyzer.find_nodes_by_type(root_node, "assignment_expression")

    # Find local_variable_declaration
    nodes.extend(TSAnalyzer.find_nodes_by_type(root_node, "declaration"))

    sources = []
    for node in nodes:
        is_src_node = False
        for child in node.children:
            if (
                    child.type == "number_literal"
                    and source_code[child.start_byte: child.end_byte] in {"0", "0.0", "0.0f", "0.0F"}
            ):
                is_src_node = True
            if child.type == "call_expression":
                for sub_child in child.children:
                    if sub_child.type == "identifier":
                        function_name = source_code[sub_child.start_byte:sub_child.end_byte]
                        if function_name in {"atoi", "atof"}:
                            is_src_node = True
                            break
        if is_src_node:
            for child in node.children:
                if child.type == "identifier":
                    name = source_code[child.start_byte: child.end_byte]
                    line_number = source_code[: child.start_byte].count("\n") + 1
                    sources.append((name, line_number))
                    print(name, line_number)
    return sources


def find_dbz_sink(source_code: str, root_node: tree_sitter.Node):
    """
    Find source values for dbz detection
    :param source_code: The source code
    :param root_node: The root node of the parse tree
    :return: The variable names and line numbers of sink values
    """
    nodes = TSAnalyzer.find_nodes_by_type(root_node, "binary_expression")
    sinks = []
    for node in nodes:
        is_sink_node = False
        for child in node.children:
            if child.type in {"/", "%"}:
                is_sink_node = True
                continue
            if is_sink_node:
                name = source_code[child.start_byte : child.end_byte]
                line_number = source_code[: child.start_byte].count("\n") + 1
                sinks.append((name, line_number))
    return sinks
