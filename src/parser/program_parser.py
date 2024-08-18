import os
import sys
from os import path
from enum import Enum
from pathlib import Path

import tree_sitter
from tree_sitter import Language
from tqdm import tqdm

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from typing import List, Tuple, Dict

class Function:
    def __init__(
        self,
        function_id: int,
        function_name: str,
        function_code: str,
        start_line_number: int,
        end_line_number: int,
        function_node: tree_sitter.Node,
    ) -> None:
        """
        Record basic facts of the function
        """
        self.function_id = function_id
        self.function_name = function_name
        self.function_code = function_code
        self.start_line_number = start_line_number
        self.end_line_number = end_line_number

        # root node of the parse tree
        # Attention: the parse tree is in the context of the whole file
        self.parse_tree_root_node = function_node

        # call site nodes and line numbers (conform to control flow order)
        self.call_site_nodes = []

        # if statement info
        self.if_statements = {}


class TSParser:
    """
    TSParser class for extracting information from C/C++ files using tree-sitter.
    """

    def __init__(self, code_in_projects: Dict[str, str]) -> None:
        """
        Initialize TSParser with a collection of C/C++ files.
        :param code_in_projects: A dictionary containing the content of C/C++ files.
        """
        self.code_in_projects = code_in_projects
        self.functionRawDataDic = {}
        self.functionNameToId = {}
        self.functionToFile = {}
        self.fileContentDic = {}

        cwd = Path(__file__).resolve().parent.absolute()
        TSPATH = cwd / "../../lib/build/"
        language_path = TSPATH / "my-languages.so"
        self.c_lang = Language(str(language_path), "c")

        # Initialize the parser
        self.parser = tree_sitter.Parser()
        self.parser.set_language(self.c_lang)


    def parse_function_info(self, file_path: str, source_code: str, tree: tree_sitter.Tree) -> None:
        """
        Parse the function information in a C/C++ file.
        :param file_path: The path of the C/C++ file.
        :param source_code: The content of the C/C++ file.
        :param tree: The parse tree of the C/C++ file.
        """
        all_function_nodes = TSAnalyzer.find_nodes_by_type(tree.root_node, "function_definition")
        for node in all_function_nodes:
            # get function name
            function_name = ""
            for sub_node in node.children:
                if sub_node.type != "function_declarator":
                    continue
                for sub_sub_node in sub_node.children:
                    if sub_sub_node.type == "identifier":
                        function_name = source_code[sub_sub_node.start_byte:sub_sub_node.end_byte]
                        break
                if function_name != "":
                    break

            if function_name == "":
                continue

            # Initialize the raw data of a function
            start_line_number = source_code[: node.start_byte].count("\n") + 1
            end_line_number = source_code[: node.end_byte].count("\n") + 1
            function_id = len(self.functionRawDataDic) + 1
            
            self.functionRawDataDic[function_id] = (
                function_name,
                start_line_number,
                end_line_number,
                node
            )
            self.functionToFile[function_id] = file_path
            
            if function_name not in self.functionNameToId:
                self.functionNameToId[function_name] = set([])
            self.functionNameToId[function_name].add(function_id)
        return
    

    def parse_project(self) -> None:
        """
        Parse the C/C++ project.
        """
        cnt = 0
        pbar = tqdm(total=len(self.code_in_projects), desc="Parsing files")
        for c_file_path in self.code_in_projects:
            pbar.update(1)
            # print("Parsing file: ", cnt, "/", len(self.code_in_projects))
            cnt += 1
            source_code = self.code_in_projects[c_file_path]
            tree = self.parser.parse(bytes(source_code, "utf8"))
            self.parse_function_info(c_file_path, source_code, tree)
            self.fileContentDic[c_file_path] = source_code
        return


class TSAnalyzer:
    """
    TSAnalyzer class for retrieving necessary facts or functions for LMAgent
    """

    def __init__(
        self,
        code_in_projects: Dict[str, str],
    ) -> None:
        """
        Initialize TSParser with the project path.
        :param code_in_projects: The path of a C/C++ file
        """
        self.ts_parser = TSParser(code_in_projects)
        self.ts_parser.parse_project()

        self.environment = {}
        self.caller_callee_map = {}
        self.callee_caller_map = {}

        cnt = 0
        pbar = tqdm(total=len(self.ts_parser.functionRawDataDic), desc="Analyzing functions")
        for function_id in self.ts_parser.functionRawDataDic:
            # print("Analyzing functions:", cnt, "/", len(self.ts_parser.functionRawDataDic))
            pbar.update(1)
            cnt += 1
            (name, start_line_number, end_line_number, function_node) = (
                self.ts_parser.functionRawDataDic[function_id]
            )
            file_content = self.ts_parser.fileContentDic[self.ts_parser.functionToFile[function_id]]
            function_code = file_content[function_node.start_byte:function_node.end_byte]
            current_function = Function(
                function_id, name, function_code, start_line_number, end_line_number, function_node
            )
            current_function = self.extract_meta_data_in_single_function(current_function, file_content)
            self.environment[function_id] = current_function
        return

    def find_all_top_functions(self) -> List[int]:
        """
        Collect all the main functions, which are ready for analysis
        :return: a list of ids indicating main functions
        """
        main_ids = []
        for function_id in self.ts_parser.functionRawDataDic:
            (name, code, start_line_number, end_line_number) = self.ts_parser.functionRawDataDic[function_id]
            if code.count("\n") < 2:
                continue
            if name in {"main"}:
                main_ids.append(function_id)
        return main_ids

    def find_all_nodes(self, root_node: tree_sitter.Node) -> List[tree_sitter.Node]:
        if root_node is None:
            return []
        nodes = [root_node]
        for child_node in root_node.children:
            nodes.extend(TSAnalyzer.find_all_nodes(child_node))
        return nodes

    @staticmethod
    def find_nodes_by_type(
        root_node: tree_sitter.Node, node_type: str
    ) -> List[tree_sitter.Node]:
        """
        Find all the nodes with the specific type in the parse tree
        :param root_node: the root node of the parse tree
        :param node_type: the type of the nodes to be found
        """
        nodes = []
        if root_node.type == node_type:
            nodes.append(root_node)
        for child_node in root_node.children:
            nodes.extend(TSAnalyzer.find_nodes_by_type(child_node, node_type))
        return nodes

    def find_callee(
        self, function_id: int, source_code: str, call_expr_node: tree_sitter.Node
    ) -> List[int]:
        """
        Find the callee of a function call
        :param function_id: the id of the caller function
        :param source_code: the content of the file
        :param call_expr_node: the node of the function call
        """
        assert call_expr_node.type == "call_expression"
        function_name = ""
        function_name = source_code[call_expr_node.start_byte : call_expr_node.end_byte]
        for sub_child in call_expr_node.children:
            if sub_child.type == "identifier":
                function_name = source_code[sub_child.start_byte:sub_child.end_byte]
                break

        if function_name not in self.ts_parser.functionNameToId:
            return []
        else:
            return self.ts_parser.functionNameToId[function_name]

    def find_if_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        """
        Find all the if statements in the function
        :param source_code: the content of the function
        :param root_node: the root node of the parse tree
        """
        targets = self.find_nodes_by_type(root_node, "if_statement")
        if_statements = {}

        for target in targets:
            condition_str = ""
            condition_line = 0
            true_branch_start_line = 0
            true_branch_end_line = 0
            else_branch_start_line = 0
            else_branch_end_line = 0
            for sub_target in target.children:
                if sub_target.type == "parenthesized_expression":
                    condition_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    condition_str = source_code[
                        sub_target.start_byte : sub_target.end_byte
                    ]
                if "statement" in sub_target.type:
                    true_branch_start_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    true_branch_end_line = (
                        source_code[: sub_target.end_byte].count("\n") + 1
                    )
                if sub_target.type == "else_clause":
                    # TODO: nested else clauses
                    else_branch_start_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    else_branch_end_line = (
                        source_code[: sub_target.end_byte].count("\n") + 1
                    )
            if_statement_end_line = max(true_branch_end_line, else_branch_start_line)
            if_statements[(condition_line, if_statement_end_line)] = (
                condition_line,
                condition_str,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            )
        return if_statements

    def extract_meta_data_in_single_function(
        self, current_function: Function, file_content: str
    ) -> Function:
        """
        Extract meta data in a single function
        :param current_function: the function to be analyzed
        :param file_content: the content of the file
        """
        # Identify call site info and maintain the environment
        all_call_sites = self.find_nodes_by_type(current_function.parse_tree_root_node, "call_expression")
        white_call_sites = []

        for call_site_node in all_call_sites:
            callee_ids = self.find_callee(current_function.function_id, file_content, call_site_node)
            if len(callee_ids) > 0:
                # Update the call graph
                for callee_id in callee_ids:
                    caller_id = current_function.function_id
                    if caller_id not in self.caller_callee_map:
                        self.caller_callee_map[caller_id] = set([])
                    self.caller_callee_map[caller_id].add(callee_id)
                    if callee_id not in self.callee_caller_map:
                        self.callee_caller_map[callee_id] = set([])
                    self.callee_caller_map[callee_id].add(caller_id)

        current_function.call_site_nodes = white_call_sites

        # compute the scope of the if-statements to guide the further path feasibility validation
        if_statements = self.find_if_statements(
            current_function.function_code,
            current_function.parse_tree_root_node,
        )
        current_function.if_statements = if_statements
        return current_function

    def find_function_by_line_number(self, line_number: int) -> List[Function]:
        """
        Find the function that contains the specific line number
        :param line_number: the line number to be searched
        """
        for function_id in self.environment:
            function = self.environment[function_id]
            if function.start_line_number <= line_number <= function.end_line_number:
                return [function]
        return []

    def find_node_by_line_number(
        self, line_number: int
    ) -> List[Tuple[str, tree_sitter.Node]]:
        """
        Find the node that contains the specific line number
        :param line_number: the line number to be searched
        """
        code_node_list = []
        for function_id in self.environment:
            function = self.environment[function_id]
            if (
                not function.start_line_number
                <= line_number
                <= function.end_line_number
            ):
                continue
            all_nodes = TSAnalyzer.find_all_nodes(function.parse_tree_root_node)
            for node in all_nodes:
                start_line = (
                    function.function_code[: node.start_byte].count("\n")
                    + function.start_line_number
                )
                end_line = (
                    function.function_code[: node.end_byte].count("\n")
                    + function.start_line_number
                )
                if start_line == end_line == line_number:
                    code_node_list.append((function.function_code, node))
        return code_node_list
    