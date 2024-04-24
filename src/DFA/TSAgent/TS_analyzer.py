import sys
from os import path
import tree_sitter

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from config.config import *
from TSAgent.TS_parser import TSParser
from typing import List, Tuple
from utility.function import *


class TSAnalyzer:
    """
    TSAnalyzer class for retrieving necessary facts or functions for LMAgent
    """

    def __init__(self, java_file_path: str) -> None:
        """
        Initialize TSParser with the project path.
        Currently we only analyze a single java file
        :param java_file_path: The path of a java file
        """
        self.java_file_path: str = java_file_path
        self.ts_parser: TSParser = TSParser(java_file_path)
        self.ts_parser.extract_single_file(self.java_file_path)
        self.main_ids: List[int] = self.find_all_top_functions()
        self.tmp_variable_count = 0

    def find_all_top_functions(self) -> List[int]:
        """
        Collect all the main functions, which are ready for analysis
        :return: a list of ids indicating main functions
        """
        # self.methods: Dict[int, (str, str)] = {}
        main_ids = []
        for method_id in self.ts_parser.methods:
            (name, code) = self.ts_parser.methods[method_id]
            if code.count("\n") < 2:
                continue
            if name.endswith("_good") or name.endswith("_bad"):
                main_ids.append(method_id)
        return main_ids

    def find_callee(
        self, method_id: int, source_code: str, call_site_node: tree_sitter.Node
    ) -> List[int]:
        """
        Find callees that invoked by a specific method.
        Attention: call_site_node should be derived from source_code directly
        :param method_id: caller function id
        :param file_path: the path of the file containing the caller function
        :param source_code: the content of the source file
        :param call_site_node: the node of the call site. The type is 'method_invocation'
        :return the list of the ids of called functions
        """
        assert call_site_node.type == "call_expression"
        method_name = ""
        for node2 in call_site_node.children:
            if node2.type == "identifier":
                method_name = source_code[node2.start_byte : node2.end_byte]
                break

        # Grep callees with names
        callee_ids = []
        for method_id in self.ts_parser.methods:
            (name, code) = self.ts_parser.methods[method_id]
            if name == method_name:
                callee_ids.append(method_id)
        return callee_ids

    @staticmethod
    def find_function_parameters(
        source_code: str, root_node: tree_sitter.Node
    ) -> List[LocalValue]:
        """
        Extract the (formal) parameter info of a function
        :param source_code: the source code of a function
        :param root_node: the root node of the parse tree of the function
        :return the list of args, including arg names, type names, and indexes.
        """
        paras = []
        paras_nodes: List[tree_sitter.Node] = TSParser.find_nodes(
            root_node, "parameter_list"
        )
        para_index = 1
        for para_node in paras_nodes[0].children:
            if para_node.type == "parameter_declaration":
                identifier_nodes = TSParser.find_nodes(para_node, "identifier")
                para_sub_node = identifier_nodes[0]
                para_name = source_code[
                    para_sub_node.start_byte : para_sub_node.end_byte
                ]
                paras.append(LocalValue(para_name, 1, ValueType.PARA, para_index))
                para_index += 1
                break
        return paras

    @staticmethod
    def find_function_returns(
        source_code: str, root_node: tree_sitter.Node
    ) -> List[LocalValue]:
        """
        Extract the (formal) return info of a function
        :param source_code: the source code of a function
        :param root_node: the root node of the parse tree of the function
        :return the list of return value, including variable name and the line number
        """
        rets = []
        ret_nodes: List[tree_sitter.Node] = TSParser.find_nodes(
            root_node, "return_statement"
        )
        for ret_node in ret_nodes:
            ret_stmt = source_code[ret_node.start_byte:ret_node.end_byte]
            return_var = ret_stmt.replace("return ", "").replace(";", "")
            line_num = source_code[: ret_node.start_byte].count("\n") + 1
            rets.append(LocalValue(return_var, line_num, ValueType.RET))
        return rets

    @staticmethod
    def find_call_site_args(
        source_code: str, call_site_node: tree_sitter.Node, line_number: int
    ) -> List[LocalValue]:
        """
        Extract the input info of a call site
        :param source_code: the source code of a function
        :param call_site_node: the node of a call site
        :param line_number: the line number of the call site
        :return the list of input variable names and the indexes
        """
        inputs = []
        index = 1
        for node in call_site_node.children:
            if node.type == "argument_list":
                for child in node.children:
                    if child.type in {"(", ")"}:
                        continue
                    input_var = source_code[child.start_byte : child.end_byte]
                    inputs.append(
                        LocalValue(input_var, line_number, ValueType.ARG, index)
                    )
                    index += 1
        return inputs

    @staticmethod
    def find_call_site_outputs(
        source_code: str,
        root_node: tree_sitter.Node,
        call_site_node: tree_sitter.Node,
        line_number: int,
    ) -> List[LocalValue]:
        """
        Extract the output info of a call site
        :param source_code: the source code of a function
        :param root_node: the root node of a function
        :param call_site_node: the node of a call site
        :param line_number: the line number of a call site
        :return the list of output variable name and line number
        """
        outputs = []

        # Find assignment_expression
        nodes = TSParser.find_nodes(root_node, "assignment_expression")

        # Find local_variable_declaration
        nodes.extend(TSParser.find_nodes(root_node, "init_declarator"))

        # Extract the name info and line number
        for node in nodes:
            if source_code[: node.start_byte].count("\n") == source_code[
                : call_site_node.start_byte
            ].count("\n"):
                for child in node.children:
                    if child.type == "identifier":
                        name = source_code[child.start_byte : child.end_byte]
                        outputs.append(LocalValue(name, line_number, ValueType.OUT))
        assert len(outputs) <= 1
        return outputs

    def find_if_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        targets = TSParser.find_nodes(root_node, "if_statement")
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
                if sub_target.type == "compound_statement":
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
            if_statement_end_line = max(true_branch_end_line, else_branch_start_line)
            if_statements[(condition_line, if_statement_end_line)] = (
                condition_line,
                condition_str,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            )
        return if_statements
