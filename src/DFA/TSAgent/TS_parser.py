import os
import tree_sitter
from tree_sitter import Language
from typing import Dict, List
from pathlib import Path


class TSParser:
    """
    TSParser class for extracting information from C files using tree-sitter.
    """

    def __init__(self, c_file_path: str) -> None:
        """
        Initialize TSParser with a java file path
        :param c_file_path: The path of a C file.
        """
        self.c_file_path: str = c_file_path
        self.methods: Dict[int, (str, str)] = {}

        cwd = Path(__file__).resolve().parent.absolute()
        TSPATH = cwd / "../../../lib/build/"
        language_path = TSPATH / "my-languages.so"
        # Load the Java language
        self.java_lang: Language = Language(str(language_path), "c")

        # Initialize the parser
        self.parser: tree_sitter.Parser = tree_sitter.Parser()
        self.parser.set_language(self.java_lang)

    @staticmethod
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
            nodes.extend(TSParser.find_nodes(child_node, node_type))
        return nodes

    def extract_single_file(self, file_path: str) -> None:
        """
        Process a single C file and extract method and field information.
        :param file_path: The path of the C file.
        """
        with open(file_path, "r") as file:
            source_code = file.read()

        # Parse the Java code
        tree: tree_sitter.Tree = self.parser.parse(bytes(source_code, "utf8"))

        # Get the root node of the parse tree
        root_node: tree_sitter.Node = tree.root_node

        for node in TSParser.find_nodes(root_node, "function_definition"):
            method_name = ""
            method_code = ""
            for sub_child in node.children:
                if sub_child.type == "function_declarator":
                    for sub_sub_children in sub_child.children:
                        if sub_sub_children.type == "identifier":
                            method_name = source_code[
                                          sub_sub_children.start_byte: sub_sub_children.end_byte
                                          ]
                            method_code = source_code[
                                          node.start_byte: node.end_byte
                                          ]
                            break
                    if method_name != "" and method_code != "":
                        break
            method_id = len(self.methods) + 1
            self.methods[method_id] = (method_name, method_code)
