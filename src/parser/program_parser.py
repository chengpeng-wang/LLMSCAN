import os
import sys
from os import path
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Dict, Set

import tree_sitter
from tree_sitter import Language
from tqdm import tqdm
import networkx as nx

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

        # Attention: the parse tree is in the context of the whole file
        self.parse_tree_root_node = function_node  # root node of the parse tree of the current function
        self.call_site_nodes = []   # call site info

        ## Results of AST node type analysis
        self.paras = set([])        # A set of (Expr, int) tuples, where int indicates the index of the parameter

        ## Results of intraprocedural control flow analysis
        self.if_statements = {}     # if statement info
        self.loop_statements = {}   # loop statement info


class TSParser:
    """
    TSParser class for extracting information from source files using tree-sitter.
    """

    def __init__(self, code_in_projects: Dict[str, str], language_setting: str) -> None:
        """
        Initialize TSParser with a collection of source files.
        :param code_in_projects: A dictionary containing the content of source files.
        """
        self.code_in_projects = code_in_projects
        self.language_setting = language_setting

        self.functionRawDataDic = {}
        self.functionNameToId = {}
        self.functionToFile = {}
        self.fileContentDic = {}

        cwd = Path(__file__).resolve().parent.absolute()
        TSPATH = cwd / "../../lib/build/"
        language_path = TSPATH / "my-languages.so"

        # Initialize the parser
        self.parser = tree_sitter.Parser()

        # initilize the language according to language_setting
        if language_setting == "C":
            self.language = Language(str(language_path), "c")
        elif language_setting == "C++":
            self.language = Language(str(language_path), "cpp")
        elif language_setting == "Java":
            self.language = Language(str(language_path), "java")
        elif language_setting == "Python":
            self.language = Language(str(language_path), "python")

        self.parser.set_language(self.language)


    def parse_function_info(self, file_path: str, source_code: str, tree: tree_sitter.Tree) -> None:
        """
        Parse the function information in a source file.
        :param file_path: The path of the source file.
        :param source_code: The content of the source file.
        :param tree: The parse tree of the source file.
        """
        all_function_header_nodes = []

        """
        Currently, we only handle four languages: C, C++, Java, and Python.
        """
        if self.language_setting in ["C", "C++"]:
            # function_declarator
            all_function_nodes = TSAnalyzer.find_nodes_by_type(tree.root_node, "function_definition")
            for node in all_function_nodes:
                for sub_node in node.children:
                    if sub_node.type == "function_declarator":
                        all_function_header_nodes.append(sub_node)
        elif self.language_setting in ["Java"]:
            all_function_header_nodes = TSAnalyzer.find_nodes_by_type(tree.root_node, "method_declaration")
        elif self.language_setting in ["Python"]:
            all_function_header_nodes = TSAnalyzer.find_nodes_by_type(tree.root_node, "function_definition")
        else:
            assert "Wrong language setting"            
    
        for node in all_function_header_nodes:
            function_name = ""
            for sub_node in node.children:
                if sub_node.type == "identifier":
                    function_name = source_code[sub_node.start_byte:sub_node.end_byte]
                    break

            if function_name == "":
                continue

            function_node = node.parent if self.language_setting in ["C", "C++"] else node

            # Initialize the raw data of a function
            start_line_number = source_code[: function_node.start_byte].count("\n") + 1
            end_line_number = source_code[: function_node.end_byte].count("\n") + 1
            function_id = len(self.functionRawDataDic) + 1
            
            self.functionRawDataDic[function_id] = (
                function_name,
                start_line_number,
                end_line_number,
                function_node
            )
            self.functionToFile[function_id] = file_path
            
            if function_name not in self.functionNameToId:
                self.functionNameToId[function_name] = set([])
            self.functionNameToId[function_name].add(function_id)
        return
    

    def parse_project(self) -> None:
        """
        Parse the project.
        """
        pbar = tqdm(total=len(self.code_in_projects), desc="Parsing files")
        for file_path in self.code_in_projects:
            pbar.update(1)
            source_code = self.code_in_projects[file_path]
            tree = self.parser.parse(bytes(source_code, "utf8"))
            self.parse_function_info(file_path, source_code, tree)
            self.fileContentDic[file_path] = source_code
        return


class TSAnalyzer:
    """
    TSAnalyzer class for retrieving necessary facts or functions for LMAgent
    """

    def __init__(
        self,
        code_in_projects: Dict[str, str],
        language: str,
    ) -> None:
        """
        Initialize TSParser with the project path.
        :param code_in_projects: A dictionary mapping file paths of source files to their contents
        """
        self.ts_parser = TSParser(code_in_projects, language)
        self.ts_parser.parse_project()

        # Each funcntion in the environments maintains the local meta data, including
        # (1) AST node type analysis
        # (2) intraprocedural control flow analysis
        self.environment = {}  

        # Results of call graph analysis
        self.caller_callee_map = {}
        self.callee_caller_map = {}
        self.call_graph = nx.DiGraph()

        pbar = tqdm(total=len(self.ts_parser.functionRawDataDic), desc="Analyzing functions")
        for function_id in self.ts_parser.functionRawDataDic:
            pbar.update(1)
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
        
        pbar.close()

        # initialize call graph
        for caller_id in self.caller_callee_map:
            for callee_id in self.caller_callee_map[caller_id]:
                self.call_graph.add_edge(caller_id, callee_id)

        return
    

    def extract_meta_data_in_single_function(
        self, current_function: Function, file_content: str
    ) -> Function:
        """
        Extract meta data in a single function
        :param current_function: the function to be analyzed
        :param file_content: the content of the file
        """
        # Identify call site info and maintain the environment
        function_call_node_type = ""
        if self.ts_parser.language_setting in ["C", "C++"]:
            function_call_node_type = "call_expression"
        elif self.ts_parser.language_setting in ["Java"]:
            function_call_node_type = "method_invocation"
        elif self.ts_parser.language_setting in ["Python"]:
            function_call_node_type = "call"

        all_call_sites = self.find_nodes_by_type(current_function.parse_tree_root_node, function_call_node_type)
        white_call_sites = []

        # Over-approximate the caller-callee relationship via function names, achieved by find_callee
        for call_site_node in all_call_sites:
            callee_ids = self.find_callee(file_content, call_site_node)
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

        # AST node type analysis
        current_function.paras = self.find_paras(current_function, file_content)

        # Intraprocedural control flow analysis
        file_id = self.ts_parser.functionToFile[current_function.function_id]
        file_content = self.ts_parser.fileContentDic[file_id]

        current_function.if_statements = self.find_if_statements(
            file_content,
            current_function.parse_tree_root_node,
        )

        current_function.loop_statements = self.find_loop_statements(
            file_content,
            current_function.parse_tree_root_node,
        )
        return current_function

    #################################################
    ########## Call Graph Analysis ##################
    #################################################
    @staticmethod
    def get_callee_name_at_call_site(node: tree_sitter.Node, source_code: str, language: str) -> str:
        """
        Get the callee name at the call site.
        :param node: the node of the call site
        :param source_code: the content of the file
        :param language: the language of the source code
        """
        if language in ["C", "C++", "Java"]:
            node_types = [sub_node.type for sub_node in node.children]
            index_of_last_dot = len(node_types) - 1 - node_types[::-1].index(".") if "." in node_types else -1
            function_name_node = node.children[index_of_last_dot + 1]
            return source_code[function_name_node.start_byte:function_name_node.end_byte]
        elif language in ["Python"]:
            for sub_node in node.children:
                if sub_node.type == "attribute":
                    for sub_sub_node in reversed(sub_node.children):
                        if sub_sub_node.type == "identifier":
                            return source_code[sub_sub_node.start_byte:sub_sub_node.end_byte]
        return ""
    
    def find_callee(self, file_content: str, call_site_node: tree_sitter.Node) -> List[int]:
        """
        Find the callee function of the call site.
        :param file_content: the content of the file
        :param call_site_node: the node of the call site
        """
        callee_names = self.get_callee_name_at_call_site(call_site_node, file_content, self.ts_parser.language_setting)
        callee_ids = []
        if callee_names in self.ts_parser.functionNameToId:
            callee_ids = list(self.ts_parser.functionNameToId[callee_names])
        return callee_ids

    #################################################
    ########## AST Node Type Analysis ###############
    #################################################   

    # The following three versions para-extraction functions may be verbose and redundant
    # However, we keep them as they may need to be extended for more complex cases separately in the future

    def find_paras(self, current_function: Function, file_content: str) -> Set[Tuple[str, int, int]]:
        """
        Find the parameters in the function.
        :param file_content: the content of the file
        :param node: the node of the function
        """
        if self.ts_parser.language_setting in ["C", "C++"]:
            return self.extract_paras_in_C_CPP(current_function, file_content)
        elif self.ts_parser.language_setting in ["Java"]:
            return self.extract_paras_in_Java(current_function, file_content)
        elif self.ts_parser.language_setting in ["Python"]:
            return self.extract_paras_in_Python(current_function, file_content)
        return set([])


    def extract_paras_in_C_CPP(self, current_function: Function, file_content: str) -> Set[Tuple[str, int, int]]:
        paras = set([])
        parameters = self.find_nodes_by_type(current_function.parse_tree_root_node, "parameter_declaration")
        index = 0
        for parameter_node in parameters:
            for sub_node in TSAnalyzer.find_nodes_by_type(parameter_node, "identifier"):                
                parameter_name = file_content[sub_node.start_byte:sub_node.end_byte]
                line_number = file_content[:sub_node.start_byte].count("\n") + 1
                paras.add((parameter_name, line_number, index))
                index += 1
        return paras


    def extract_paras_in_Java(self, current_function: Function, file_content: str) -> Set[Tuple[str, int, int]]:
        paras = set([])
        parameters = self.find_nodes_by_type(current_function.parse_tree_root_node, "formal_parameter")
        index = 0
        for parameter_node in parameters:
            for sub_node in TSAnalyzer.find_nodes_by_type(parameter_node, "identifier"):                
                parameter_name = file_content[sub_node.start_byte:sub_node.end_byte]
                line_number = file_content[:sub_node.start_byte].count("\n") + 1
                paras.add((parameter_name, line_number, index))
                index += 1
        return paras
    

    def extract_paras_in_Python(self, current_function: Function, file_content: str) -> Set[Tuple[str, int, int]]:
        paras = set([])
        parameters = self.find_nodes_by_type(current_function.parse_tree_root_node, "parameters")
        index = 0
        for parameter_node in parameters:
            for parameter in parameter_node.children:
                if parameter.type == "identifier":
                    parameter_name = file_content[parameter.start_byte:parameter.end_byte]
                    line_number = file_content[:parameter.start_byte].count("\n") + 1
                    paras.add((parameter_name, line_number, index))
                    index += 1
                elif parameter.type == "typed_parameter":
                    para_identifier_node = parameter.children[0]
                    parameter_name = file_content[para_identifier_node.start_byte:para_identifier_node.end_byte]
                    line_number = file_content[:para_identifier_node.start_byte].count("\n") + 1
                    paras.add((parameter_name, line_number, index))
                    index += 1
        return paras
    
    #################################################
    ########## Control Flow Analysis ################
    #################################################

    # The following three versions if-statement meta-data extraction functions may be verbose and redundant
    # However, we keep them as they may need to be extended for more complex cases separately in the future

    @staticmethod
    def extract_meta_data_of_Java_if_statements(source_code, root_node) -> Dict[Tuple, Tuple]:
        """
        Extract meta data of if statements in Java
        """
        if_statement_nodes = TSAnalyzer.find_nodes_by_type(root_node, "if_statement")
        if_statements = {}

        for if_statement_node in if_statement_nodes:
            condition_str = ""
            condition_start_line = 0
            condition_end_line = 0
            true_branch_start_line = 0
            true_branch_end_line = 0
            else_branch_start_line = 0
            else_branch_end_line = 0

            block_num = 0
            for sub_target in if_statement_node.children:
                if sub_target.type == "parenthesized_expression":
                    condition_start_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    condition_end_line = (
                        source_code[: sub_target.end_byte].count("\n") + 1
                    )
                    condition_str = source_code[
                        sub_target.start_byte : sub_target.end_byte
                    ]
                if sub_target.type == "block":
                    lower_lines = []
                    upper_lines = []
                    for sub_sub_target in sub_target.children:
                        if sub_sub_target.type not in {"{", "}"}:
                            lower_lines.append(source_code[: sub_sub_target.start_byte].count("\n") + 1)
                            upper_lines.append(source_code[: sub_sub_target.end_byte].count("\n") + 1)
                    if len(upper_lines) == 0 or len(lower_lines) == 0:
                        continue
                    
                    if block_num == 0:
                        true_branch_start_line = min(lower_lines)
                        true_branch_end_line = max(upper_lines)
                        block_num += 1
                    elif block_num == 1:
                        else_branch_start_line = min(lower_lines)
                        else_branch_end_line = max(upper_lines)
                        block_num += 1
                if sub_target.type == "expression_statement":
                    true_branch_start_line = source_code[: sub_target.start_byte].count("\n") + 1
                    true_branch_end_line = source_code[: sub_target.end_byte].count("\n") + 1
                    
            if_statement_start_line = source_code[: if_statement_node.start_byte].count("\n") + 1
            if_statement_end_line = source_code[: if_statement_node.end_byte].count("\n") + 1
            line_scope = (if_statement_start_line, if_statement_end_line)
            info = (
                        condition_start_line,
                        condition_end_line,
                        condition_str,
                        (true_branch_start_line, true_branch_end_line),
                        (else_branch_start_line, else_branch_end_line),
                    )
            if_statements[line_scope] = info 
        return if_statements
    

    @staticmethod
    def extract_meta_data_of_C_CPP_if_statements(source_code, root_node) -> Dict[Tuple, Tuple]:
        """
        Extract meta data of if statements in C/C++
        """
        if_statement_nodes = TSAnalyzer.find_nodes_by_type(root_node, "if_statement")
        if_statements = {}

        for if_statement_node in if_statement_nodes:
            condition_str = ""
            condition_start_line = 0
            condition_end_line = 0
            true_branch_start_line = 0
            true_branch_end_line = 0
            else_branch_start_line = 0
            else_branch_end_line = 0

            for sub_target in if_statement_node.children:
                if sub_target.type in ["parenthesized_expression", "condition_clause"]:
                    condition_start_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    condition_end_line = (
                        source_code[: sub_target.end_byte].count("\n") + 1
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
                    else_branch_start_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    else_branch_end_line = (
                        source_code[: sub_target.end_byte].count("\n") + 1
                    )

            if_statement_start_line = source_code[: if_statement_node.start_byte].count("\n") + 1
            if_statement_end_line = source_code[: if_statement_node.end_byte].count("\n") + 1
            line_scope = (if_statement_start_line, if_statement_end_line)
            info = (
                condition_start_line,
                condition_end_line,
                condition_str,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            )
            if_statements[line_scope] = info
        return if_statements
    

    @staticmethod
    def extract_meta_data_of_Python_if_statements(source_code, root_node) -> Dict[Tuple, Tuple]:
        """
        Extract meta data of if statements in Python
        TODO: Current implementation only extract the condition of if-statements
        The branch conditions of elif_clause are not handled.
        """
        if_statement_nodes = TSAnalyzer.find_nodes_by_type(root_node, "if_statement")
        if_statements = {}

        for if_statement_node in if_statement_nodes:
            sub_node_types = if_statement_node.children

            condition_str = source_code[sub_node_types[1].start_byte:sub_node_types[1].end_byte]
            condition_start_line = source_code[: sub_node_types[1].start_byte].count("\n") + 1
            condition_end_line = source_code[: sub_node_types[1].end_byte].count("\n") + 1
            true_branch_start_line = source_code[: sub_node_types[3].start_byte].count("\n") + 1
            true_branch_end_line = source_code[: sub_node_types[3].end_byte].count("\n") + 1

            if "else_clause" in [sub_node.type for sub_node in sub_node_types] or "elif_clause" in [sub_node.type for sub_node in sub_node_types]:
                else_branch_start_line = source_code[: sub_node_types[4].start_byte].count("\n") + 1
                else_branch_end_line = source_code[: if_statement_node.end_byte].count("\n") + 1
            else:
                else_branch_start_line = 0
                else_branch_end_line = 0

            if_statement_start_line = source_code[: if_statement_node.start_byte].count("\n") + 1
            if_statement_end_line = source_code[: if_statement_node.end_byte].count("\n") + 1
            line_scope = (if_statement_start_line, if_statement_end_line)
            info = (
                condition_start_line,
                condition_end_line,
                condition_str,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            )
            if_statements[line_scope] = info
        return if_statements
                

    def find_if_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        """
        Find all the if statements in the function
        :param source_code: the content of the function
        :param root_node: the root node of the parse tree
        """
        if self.ts_parser.language_setting in ["C", "C++"]:
            return self.extract_meta_data_of_C_CPP_if_statements(source_code, root_node)
        elif self.ts_parser.language_setting in ["Java"]:
            return self.extract_meta_data_of_Java_if_statements(source_code, root_node)
        elif self.ts_parser.language_setting in ["Python"]:
            return self.extract_meta_data_of_Python_if_statements(source_code, root_node)


    @staticmethod
    def extract_meta_data_of_Java_loop_statements(source_code, root_node) -> Dict[Tuple, Tuple]:
        loop_statements = {}
        for_statement_nodes = TSAnalyzer.find_nodes_by_type(root_node, "for_statement")
        for_statement_nodes.extend(TSAnalyzer.find_nodes_by_type(root_node, "enhanced_for_statement"))
        while_statement_nodes = TSAnalyzer.find_nodes_by_type(root_node, "while_statement")

        for loop_node in for_statement_nodes:
            loop_start_line = source_code[: loop_node.start_byte].count("\n") + 1
            loop_end_line = source_code[: loop_node.end_byte].count("\n") + 1

            header_line_start = 0
            header_line_end = 0
            header_str = ""
            loop_body_start_line = 0
            loop_body_end_line = 0

            header_start_byte = 0
            header_end_byte = 0

            for loop_child_node in loop_node.children:
                if loop_child_node.type == "(":
                    header_line_start = source_code[: loop_child_node.start_byte].count("\n") + 1
                    header_start_byte = loop_child_node.end_byte
                if loop_child_node.type == ")":
                    header_line_end = source_code[: loop_child_node.end_byte].count("\n") + 1
                    header_end_byte = loop_child_node.start_byte
                    header_str = source_code[header_start_byte: header_end_byte]
                if loop_child_node.type == "block":
                    lower_lines = []
                    upper_lines = []
                    for loop_child_child_node in loop_child_node.children:
                        if loop_child_child_node.type not in {"{", "}"}:
                            lower_lines.append(source_code[: loop_child_child_node.start_byte].count("\n") + 1)
                            upper_lines.append(source_code[: loop_child_child_node.end_byte].count("\n") + 1)
                    loop_body_start_line = min(lower_lines)
                    loop_body_end_line = max(upper_lines)
                if loop_child_node.type == "expression_statement":
                    loop_body_start_line = source_code[: loop_child_node.start_byte].count("\n") + 1
                    loop_body_end_line = source_code[: loop_child_node.end_byte].count("\n") + 1
            loop_statements[(loop_start_line, loop_end_line)] = (
                header_line_start,
                header_line_end,
                header_str,
                loop_body_start_line,
                loop_body_end_line,
            )

        for loop_node in while_statement_nodes:
            loop_start_line = source_code[: loop_node.start_byte].count("\n") + 1
            loop_end_line = source_code[: loop_node.end_byte].count("\n") + 1

            header_line_start = 0
            header_line_end = 0
            header_str = ""
            loop_body_start_line = 0
            loop_body_end_line = 0

            for loop_child_node in loop_node.children:
                if loop_child_node.type == "parenthesized_expression":
                    header_line_start = source_code[: loop_child_node.start_byte].count("\n") + 1
                    header_line_end = source_code[: loop_child_node.end_byte].count("\n") + 1
                    header_str = source_code[loop_child_node.start_byte: loop_child_node.end_byte]
                if loop_child_node.type == "block":
                    lower_lines = []
                    upper_lines = []
                    for loop_child_child_node in loop_child_node.children:
                        if loop_child_child_node.type not in {"{", "}"}:
                            lower_lines.append(source_code[: loop_child_child_node.start_byte].count("\n") + 1)
                            upper_lines.append(source_code[: loop_child_child_node.end_byte].count("\n") + 1)
                    loop_body_start_line = min(lower_lines)
                    loop_body_end_line = max(upper_lines)
            loop_statements[(loop_start_line, loop_end_line)] = (
                header_line_start,
                header_line_end,
                header_str,
                loop_body_start_line,
                loop_body_end_line,
            )
        return loop_statements


    @staticmethod
    def extract_meta_data_of_C_CPP_while_statements(source_code, root_node) -> Dict[Tuple, Tuple]:
        loop_statements = {}
        for_statement_nodes = TSAnalyzer.find_nodes_by_type(root_node, "for_statement")
        while_statement_nodes = TSAnalyzer.find_nodes_by_type(root_node, "while_statement")

        for loop_node in for_statement_nodes:
            loop_start_line = source_code[: loop_node.start_byte].count("\n") + 1
            loop_end_line = source_code[: loop_node.end_byte].count("\n") + 1

            header_line_start = 0
            header_line_end = 0
            header_str = ""
            loop_body_start_line = 0
            loop_body_end_line = 0

            header_start_byte = 0
            header_end_byte = 0

            for loop_child_node in loop_node.children:
                if loop_child_node.type == "(":
                    header_line_start = source_code[: loop_child_node.start_byte].count("\n") + 1
                    header_start_byte = loop_child_node.end_byte
                if loop_child_node.type == ")":
                    header_line_end = source_code[: loop_child_node.end_byte].count("\n") + 1
                    header_end_byte = loop_child_node.start_byte
                    header_str = source_code[header_start_byte: header_end_byte]
                if loop_child_node.type == "block":
                    lower_lines = []
                    upper_lines = []
                    for loop_child_child_node in loop_child_node.children:
                        if loop_child_child_node.type not in {"{", "}"}:
                            lower_lines.append(source_code[: loop_child_child_node.start_byte].count("\n") + 1)
                            upper_lines.append(source_code[: loop_child_child_node.end_byte].count("\n") + 1)
                    loop_body_start_line = min(lower_lines)
                    loop_body_end_line = max(upper_lines)
                if "statement" in loop_child_node.type:
                    loop_body_start_line = source_code[: loop_child_node.start_byte].count("\n") + 1
                    loop_body_end_line = source_code[: loop_child_node.end_byte].count("\n") + 1
            loop_statements[(loop_start_line, loop_end_line)] = (
                header_line_start,
                header_line_end,
                header_str,
                loop_body_start_line,
                loop_body_end_line,
            )

        for loop_node in while_statement_nodes:
            loop_start_line = source_code[: loop_node.start_byte].count("\n") + 1
            loop_end_line = source_code[: loop_node.end_byte].count("\n") + 1

            header_line_start = 0
            header_line_end = 0
            header_str = ""
            loop_body_start_line = 0
            loop_body_end_line = 0

            for loop_child_node in loop_node.children:
                if loop_child_node.type == "parenthesized_expression":
                    header_line_start = source_code[: loop_child_node.start_byte].count("\n") + 1
                    header_line_end = source_code[: loop_child_node.end_byte].count("\n") + 1
                    header_str = source_code[loop_child_node.start_byte: loop_child_node.end_byte]
                if "statement" in loop_child_node.type:
                    lower_lines = []
                    upper_lines = []
                    for loop_child_child_node in loop_child_node.children:
                        if loop_child_child_node.type not in {"{", "}"}:
                            lower_lines.append(source_code[: loop_child_child_node.start_byte].count("\n") + 1)
                            upper_lines.append(source_code[: loop_child_child_node.end_byte].count("\n") + 1)
                    loop_body_start_line = min(lower_lines)
                    loop_body_end_line = max(upper_lines)
            loop_statements[(loop_start_line, loop_end_line)] = (
                header_line_start,
                header_line_end,
                header_str,
                loop_body_start_line,
                loop_body_end_line,
            )
        return loop_statements
    

    @staticmethod
    def extract_meta_data_of_Python_loop_statements(source_code, root_node) -> Dict[Tuple, Tuple]:
        loop_statements = {}
        loop_nodes = TSAnalyzer.find_nodes_by_type(root_node, "for_statement")
        loop_nodes.extend(TSAnalyzer.find_nodes_by_type(root_node, "while_statement"))

        for loop_node in loop_nodes:
            loop_start_line = source_code[: loop_node.start_byte].count("\n") + 1
            loop_end_line = source_code[: loop_node.end_byte].count("\n") + 1

            header_line_start = 0
            header_line_end = 0
            header_str = ""
            loop_body_start_line = 0
            loop_body_end_line = 0

            for loop_child_node in loop_node.children:
                if loop_child_node.type == ":":
                    header_line_start = source_code[: loop_node.start_byte].count("\n") + 1
                    header_line_end = source_code[: loop_child_node.start_byte].count("\n") + 1
                    header_str = source_code[loop_node.start_byte: loop_child_node.start_byte]
                if loop_child_node.type == "block":
                    loop_body_start_line = source_code[: loop_child_node.start_byte].count("\n") + 1
                    loop_body_end_line = source_code[: loop_child_node.end_byte].count("\n") + 1
                    
            loop_statements[(loop_start_line, loop_end_line)] = (
                header_line_start,
                header_line_end,
                header_str,
                loop_body_start_line,
                loop_body_end_line
            )
        return loop_statements
    

    def find_loop_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        """
        Find all the loop statements in the function
        :param source_code: the content of the function
        :param root_node: the root node of the parse tree
        """
        if self.ts_parser.language_setting in ["C", "C++"]:
            return self.extract_meta_data_of_C_CPP_while_statements(source_code, root_node)
        elif self.ts_parser.language_setting in ["Java"]:
            return self.extract_meta_data_of_Java_loop_statements(source_code, root_node)
        elif self.ts_parser.language_setting in ["Python"]:
            return self.extract_meta_data_of_Python_loop_statements(source_code, root_node)


    #################################################
    ########## AST visitor utility ##################
    #################################################

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
    