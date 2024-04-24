import sys
from os import path
import tree_sitter

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
from TSAgent.TS_analyzer import TSAnalyzer
from TSAgent.TS_parser import TSParser
from typing import Tuple, List
from utility.function import *


def find_dbz_src(source_code: str, root_node: tree_sitter.Node) -> List[LocalValue]:
    # TODO: This function should be synthesized automatically
    """
    Find source values for dbz detection
    :param source_code: The source code
    :param root_node: The root node of the parse tree
    :return: The variable names and line numbers of source values
    """
    # Find assignment_expression
    nodes = TSParser.find_nodes(root_node, "assignment_expression")

    # Find local_variable_declaration
    nodes.extend(TSParser.find_nodes(root_node, "init_declarator"))

    # Extract the name info and line number
    lines = []
    for node in nodes:
        is_src_node = False
        # TODO: To detect the dbz bug_candidates in the Juliet test suite, we need to specify more forms of source values,
        #  such as the return value of parseFloat and parseInt
        for child in node.children:
            if (
                child.type == "number_literal"
                and source_code[child.start_byte : child.end_byte] in {"0", "0.0", "0.0F"}
            ):
                is_src_node = True
            if (
                    "atof" in source_code[child.start_byte : child.end_byte] or
                    "atoi" in source_code[child.start_byte: child.end_byte] or
                    "RAND32" in source_code[child.start_byte: child.end_byte]
            ):
                is_src_node = True
        if is_src_node:
            for child in node.children:
                if child.type == "identifier":
                    name = source_code[child.start_byte : child.end_byte]
                    line_number = source_code[: child.start_byte].count("\n") + 1
                    lines.append(LocalValue(name, line_number, ValueType.SRC))

    for node in TSParser.find_nodes(root_node, "call_expression"):
        for sub_child in node.children:
            if sub_child.type == "argument_list":
                for sub_sub_child in sub_child.children:
                    if sub_sub_child.type == "pointer_expression":
                        for sub_sub_sub_child in sub_sub_child.children:
                            if sub_sub_sub_child.type == "identifier":
                                name = source_code[sub_sub_sub_child.start_byte: sub_sub_sub_child.end_byte]
                                line_number = source_code[: sub_sub_sub_child.start_byte].count("\n") + 1
                                lines.append(LocalValue(name, line_number, ValueType.SRC))
    return lines


def find_dbz_sink(source_code: str, root_node: tree_sitter.Node) -> List[LocalValue]:
    # TODO: This function should be synthesized automatically
    """
    Find source values for dbz detection
    :param source_code: The source code
    :param root_node: The root node of the parse tree
    :return: The variable names and line numbers of sink values
    """
    nodes = TSParser.find_nodes(root_node, "binary_expression")
    lines = []
    for node in nodes:
        is_sink_node = False
        for child in node.children:
            if child.type in {"/", "%"}:
                is_sink_node = True
                continue
            if is_sink_node and child.type == "identifier":
                name = source_code[child.start_byte : child.end_byte]
                # If the program is wrapped with ```
                # line_number should be equal to source_code[:child.start_byte].count('\n')
                line_number = source_code[: child.start_byte].count("\n") + 1
                lines.append(LocalValue(name, line_number, ValueType.SINK))
    return lines


def find_xss_src(source_code: str, root_node: tree_sitter.Node) -> List[LocalValue]:
    # TODO: This function should be synthesized automatically
    """
    Find source values for xss detection
    :param source_code: The source code
    :param root_node: The root node of the parse tree
    :return: The variable names and line numbers of source values
    """
    # Find assignment_expression
    nodes = TSParser.find_nodes(root_node, "assignment_expression")

    # Find local_variable_declaration
    nodes.extend(TSParser.find_nodes(root_node, "variable_declarator"))

    # Extract the name info and line number
    lines = []
    for node in nodes:
        is_src_node = False
        for child in node.children:
            if child.type == "call_expression" and (
                "readLine" in source_code[child.start_byte : child.end_byte]
                or "getProperty" in source_code[child.start_byte : child.end_byte]
                or "getCookies" in source_code[child.start_byte : child.end_byte]
                or "getString" in source_code[child.start_byte : child.end_byte]
                or "nextToken" in source_code[child.start_byte : child.end_byte]
                or "getParameter" in source_code[child.start_byte : child.end_byte]
            ):
                is_src_node = True
        if is_src_node:
            for child in node.children:
                if child.type == "identifier":
                    name = source_code[child.start_byte : child.end_byte]
                    line_number = source_code[: child.start_byte].count("\n") + 1
                    lines.append(LocalValue(name, line_number, ValueType.SRC))
    return lines


def find_xss_sink(source_code: str, root_node: tree_sitter.Node) -> List[LocalValue]:
    # TODO: This function should be synthesized automatically
    """
    Find source values for dbz detection
    :param source_code: The source code
    :param root_node: The root node of the parse tree
    :return: The variable names and line numbers of sink values
    """
    nodes = TSParser.find_nodes(root_node, "binary_expression")
    lines = []
    for node in nodes:
        is_sink_node = False
        for child in node.children:
            if child.type in {"/", "%"}:
                is_sink_node = True
                continue
            if is_sink_node and child.type == "identifier":
                name = source_code[child.start_byte : child.end_byte]
                # If the program is wrapped with ```
                # line_number should be equal to source_code[:child.start_byte].count('\n')
                line_number = source_code[: child.start_byte].count("\n") + 1
                lines.append(LocalValue(name, line_number, ValueType.SINK))

    nodes = TSParser.find_nodes(root_node, "call_expression")
    lines = []
    for node in nodes:
        is_sink_function = False
        for sub_node in node.children:
            if (
                sub_node.type == "identifier"
                and source_code[sub_node.start_byte : sub_node.end_byte] == "println"
            ):
                is_sink_function = True
                break
        if is_sink_function:
            for sub_node in node.children:
                if sub_node.type == "argument_list":
                    line_number = source_code[: sub_node.start_byte].count("\n") + 1
                    name = source_code[sub_node.start_byte + 1 : sub_node.end_byte - 1]
                    lines.append(LocalValue(name, line_number, ValueType.SINK))
    return lines
