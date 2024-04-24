import sys
import os
from os import path
import tree_sitter
from tree_sitter import Language

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from typing import List, Tuple, Dict
from enum import Enum
from data.transform import *
from pathlib import Path


class Function:
    def __init__(
        self,
        function_id: int,
        function_name: str,
        function_code: str,
        start_line_number: int,
        end_line_number: int,
    ) -> None:
        """
        Record basic facts of the function
        """
        self.function_id: int = function_id
        self.function_name: str = function_name
        self.function_code: str = function_code
        self.start_line_number = start_line_number
        self.end_line_number = end_line_number

        self.parse_tree: tree_sitter.Tree = None
        self.is_transformed: bool = False
        self.is_parsed: bool = False

        # field initialization statements
        self.field_inits: Dict[int, str] = {}

        # call site nodes and line numbers (conform to control flow order)
        self.call_site_nodes: List[Tuple[tree_sitter.Node, int]] = []

        # if statement info
        self.if_statements: Dict[Tuple, Tuple] = {}

        # switch statement info
        self.switch_statements: Dict[Tuple, List] = {}

    def set_parse_tree(self, parse_tree: tree_sitter.Tree) -> None:
        self.parse_tree = parse_tree
        self.is_parsed = True
        return

    def set_call_sites(self, call_sites: List[Tuple[tree_sitter.Node, int]]) -> None:
        self.call_site_nodes = call_sites
        return

    def set_field_inits_info(self, field_inits: Dict[int, str]) -> None:
        self.field_inits = field_inits
        return


class TSParser:
    """
    TSParser class for extracting information from Java files using tree-sitter.
    """

    def __init__(self, java_file_path: str) -> None:
        """
        Initialize TSParser with a java file path
        :param java_file_path: The path of a java file.
        """
        self.java_file_path: str = java_file_path
        self.methods: Dict[int, (str, str, int, int)] = {}
        self.classToFunctions: Dict[str, List[int]] = {}
        self.classToFields: Dict[str, List[int]] = {}
        self.fields: Dict[int, str] = {}
        self.fields_init: Dict[int, str] = {}

        self.fileToPackage: Dict[str, str] = {}
        self.fileToImports: Dict[str, set[str]] = {}
        self.fileToClasses: Dict[str, set[str]] = {}
        self.functionToFile: Dict[int, str] = {}
        self.packageToClasses: Dict[str, set[str]] = {}

        self.static_field_info: Dict[str, str] = {}

        cwd = Path(__file__).resolve().parent.absolute()
        TSPATH = cwd / "../../lib/build/"
        language_path = TSPATH / "my-languages.so"
        # Load the Java language
        self.java_lang: Language = Language(str(language_path), "java")

        # Initialize the parser
        self.parser: tree_sitter.Parser = tree_sitter.Parser()
        self.parser.set_language(self.java_lang)

    def parse_package_info(
        self, file_path: str, source_code: str, root_node: tree_sitter.Tree
    ) -> str:
        """
        Extract package, Assume only have one package declaration
        :param file_path: The path of the Java file.
        :param source_code: The content of the source code
        :param root_node: The root node the parse tree
        :return package name
        """
        package_code = ""
        for node in root_node.children:
            if node.type == "package_declaration":
                for child_node in node.children:
                    if child_node.type in {"scoped_identifier", "identifier"}:
                        package_code = source_code[
                            child_node.start_byte : child_node.end_byte
                        ]
                        if package_code != "":
                            break
                self.fileToPackage[file_path] = package_code
                break
        return package_code

    def parse_import_info(
        self, file_path: str, source_code: str, root_node: tree_sitter.Tree
    ) -> None:
        """
        Extract imported packages or classes
        :param file_path: The path of the Java file.
        :param source_code: The content of the source code
        :param root_node: The root node the parse tree
        """
        for node in root_node.children:
            import_code = ""
            if node.type == "import_declaration":
                for child_node in node.children:
                    if child_node.type in {"scoped_identifier", "identifier"}:
                        import_code = source_code[
                            child_node.start_byte : child_node.end_byte
                        ]
                    if import_code == "":
                        continue
                    if file_path not in self.fileToImports:
                        self.fileToImports[file_path] = set([])
                    self.fileToImports[file_path].add(import_code)

    def parse_class_declaration_info(
        self,
        file_path: str,
        source_code: str,
        package_name: str,
        root_node: tree_sitter.Tree,
    ) -> None:
        """
        Extract class declaration info: class name, fields, and methods
        :param file_path: The path of the Java file.
        :param source_code: The content of the source code
        :param package_name: The package name
        :param root_node: The root node the parse tree
        """
        for node in root_node.children:
            class_name = ""
            if node.type == "class_declaration":
                # Extract class name
                for child_node in node.children:
                    if child_node.type == "identifier":
                        class_name = source_code[
                            child_node.start_byte : child_node.end_byte
                        ]
                        break
                if file_path not in self.fileToClasses:
                    self.fileToClasses[file_path] = set([])
                self.fileToClasses[file_path].add(class_name)
                if package_name not in self.packageToClasses:
                    self.packageToClasses[package_name] = set([])
                self.packageToClasses[package_name].add(class_name)

                # Extract method name and method content
                for child_node in node.children:
                    if child_node.type == "class_body":
                        for child_child_node in child_node.children:
                            # Extract methods
                            if child_child_node.type == "method_declaration":
                                method_name = ""
                                for child_child_child_node in child_child_node.children:
                                    if child_child_child_node.type == "identifier":
                                        method_name = source_code[
                                            child_child_child_node.start_byte : child_child_child_node.end_byte
                                        ]
                                        break
                                method_code = source_code[
                                    child_child_node.start_byte : child_child_node.end_byte
                                ]
                                start_line_number = (
                                    source_code[: child_child_node.start_byte].count(
                                        "\n"
                                    )
                                    + 1
                                )
                                end_line_number = (
                                    source_code[: child_child_node.end_byte].count("\n")
                                    + 1
                                )
                                method_id = len(self.methods) + 1
                                self.methods[method_id] = (
                                    method_name,
                                    method_code,
                                    start_line_number,
                                    end_line_number,
                                )
                                if class_name not in self.classToFunctions:
                                    self.classToFunctions[class_name] = []
                                self.classToFunctions[class_name].append(method_id)
                                self.functionToFile[method_id] = file_path

                            # Extract fields
                            if child_child_node.type == "field_declaration":
                                for child_child_child_node in child_child_node.children:
                                    if (
                                        child_child_child_node.type
                                        == "variable_declarator"
                                    ):
                                        for (
                                            child_child_child_child_node
                                        ) in child_child_child_node.children:
                                            if (
                                                child_child_child_child_node.type
                                                == "identifier"
                                            ):
                                                field_id = len(self.fields)
                                                self.fields[field_id] = source_code[
                                                    child_child_child_child_node.start_byte : child_child_child_child_node.end_byte
                                                ]
                                                self.fields_init[field_id] = (
                                                    source_code[
                                                        child_child_child_node.start_byte : child_child_child_node.end_byte
                                                    ]
                                                )
                                                if class_name not in self.classToFields:
                                                    self.classToFields[class_name] = []
                                                self.classToFields[class_name].append(
                                                    field_id
                                                )

    def extract_single_file(self, file_path, source_code: str) -> None:
        # Parse the Java code
        tree: tree_sitter.Tree = self.parser.parse(bytes(source_code, "utf8"))

        # Get the root node of the parse tree
        root_node: tree_sitter.Node = tree.root_node

        # Obtain package, import, and class info
        package_name = self.parse_package_info(file_path, source_code, root_node)
        self.parse_import_info(file_path, source_code, root_node)
        self.parse_class_declaration_info(
            file_path, source_code, package_name, root_node
        )

    def extract_static_field_from_support_files(self, support_files):
        def find_nodes(
            root_node: tree_sitter.Node, node_type: str
        ) -> List[tree_sitter.Node]:
            nodes = []
            if root_node.type == node_type:
                nodes.append(root_node)

            for child_node in root_node.children:
                nodes.extend(find_nodes(child_node, node_type))
            return nodes

        for support_file in support_files:
            source_code = support_files[support_file]

            # Parse the Java code
            tree: tree_sitter.Tree = self.parser.parse(bytes(source_code, "utf8"))

            # Get the root node of the parse tree
            root_node: tree_sitter.Node = tree.root_node
            class_body_items = find_nodes(root_node, "class_declaration")

            for class_body_item in class_body_items:
                class_name = ""
                for child_node in class_body_item.children:
                    if child_node.type == "identifier":
                        class_name = source_code[
                            child_node.start_byte : child_node.end_byte
                        ]
                    elif child_node.type == "class_body":
                        for child_child_node in child_node.children:
                            if child_child_node.type == "field_declaration":
                                if (
                                    " static "
                                    in source_code[
                                        child_child_node.start_byte : child_child_node.end_byte
                                    ]
                                ):
                                    for field_token in child_child_node.children:
                                        if field_token.type == "variable_declarator":
                                            info_str = source_code[
                                                field_token.start_byte : field_token.end_byte
                                            ]
                                            field_name = info_str.split("=")[0].rstrip()
                                            assigned_value = info_str.split("=")[
                                                1
                                            ].lstrip()
                                            self.static_field_info[
                                                class_name + "." + field_name
                                            ] = (
                                                class_name
                                                + "."
                                                + field_name
                                                + " = "
                                                + assigned_value
                                            )

    def get_pretty_ast(self, file_path: str) -> str:
        """
        Print the extracted AST in a pretty format.
        """
        with open(file_path, "r") as file:
            source_code = file.read()

        # parse source code
        tree: tree_sitter.Tree = self.parser.parse(bytes(source_code, "utf8"))

        def traverse(node: tree_sitter.Node, depth: int) -> str:
            ret = ""
            for child in node.children:
                code = source_code[child.start_byte : child.end_byte]
                ret += "\n" + "  " * depth + f"[{child.type}] '{code}'"
                ret += traverse(child, depth + 1)
            return ret

        # prettify AST
        # return tree.root_node.sexp()
        return traverse(tree.root_node, 0)

    def get_ast(self, file_path: str) -> tree_sitter.Tree:
        """
        Return the AST of a Java file.
        """
        with open(file_path, "r") as file:
            source_code = file.read()

        # parse source code
        tree: tree_sitter.Tree = self.parser.parse(bytes(source_code, "utf8"))

        return tree


class TSAnalyzer:
    """
    TSAnalyzer class for retrieving necessary facts or functions for LMAgent
    """

    def __init__(
        self,
        java_file_path: str,
        original_code: str,
        analyzed_code: str,
        support_files: Dict[str, str],
    ) -> None:
        """
        Initialize TSParser with the project path.
        Currently we only analyze a single java file
        :param java_file_path: The path of a java file
        """
        self.java_file_path: str = java_file_path
        self.ts_parser: TSParser = TSParser(java_file_path)
        self.original_code = original_code
        self.analyzed_code = analyzed_code
        self.support_files = support_files

        self.ts_parser.extract_single_file(self.java_file_path, self.analyzed_code)
        self.ts_parser.extract_static_field_from_support_files(self.support_files)

        self.environment = {}
        self.caller_callee_map = {}
        self.callee_caller_map = {}

        for function_id in self.ts_parser.methods:
            (name, function_code, start_line_number, end_line_number) = (
                self.ts_parser.methods[function_id]
            )
            current_function = Function(
                function_id, name, function_code, start_line_number, end_line_number
            )
            current_function.parse_tree = self.ts_parser.parser.parse(
                bytes(function_code, "utf8")
            )
            current_function = self.extract_call_meta_data_in_single_function(
                current_function
            )
            self.environment[function_id] = current_function

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
            (name, code, start_line_number, end_line_number) = self.ts_parser.methods[
                method_id
            ]
            if code.count("\n") < 2:
                continue
            if name in {"main"}:
                main_ids.append(method_id)
        return main_ids

    @staticmethod
    def find_all_nodes(root_node: tree_sitter.Node) -> List[tree_sitter.Node]:
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
        nodes = []
        if root_node.type == node_type:
            nodes.append(root_node)
        for child_node in root_node.children:
            nodes.extend(TSAnalyzer.find_nodes_by_type(child_node, node_type))
        return nodes

    def find_callee(
        self, method_id: int, source_code: str, call_site_node: tree_sitter.Node
    ) -> List[int]:
        """
        Find callees that invoked by a specific method.
        Attention: call_site_node should be derived from source_code directly
        :param method_id: caller function id
        :param file_path: the path of the file containing the caller function
        :param source_code: the content of the source file
        :param call_site_node: the node of the call site. The type is 'call_expression'
        :return the list of the ids of called functions
        """
        assert call_site_node.type == "call_expression"
        method_name = ""
        previous_str = ""
        current_str = ""
        for node2 in call_site_node.children:
            previous_str = current_str
            current_str = source_code[node2.start_byte : node2.end_byte]
            if node2.type == "argument_list":
                method_name = previous_str
                break

        # Grep callees with names
        callee_ids = []
        for class_name in self.ts_parser.classToFunctions:
            for method_id in self.ts_parser.classToFunctions[class_name]:
                if method_id not in self.ts_parser.methods:
                    continue
                (name, code, start_line_number, end_line_number) = (
                    self.ts_parser.methods[method_id]
                )
                if name == method_name:
                    callee_ids.append(method_id)
        return callee_ids

    def find_class_by_function(self, function_id: int) -> str:
        class_name = ""
        for name in self.ts_parser.classToFunctions:
            if function_id in self.ts_parser.classToFunctions[name]:
                class_name = name
                break
        return class_name

    def find_available_fields(self, function_id: int) -> Dict[int, str]:
        class_name = self.find_class_by_function(function_id)
        if class_name not in self.ts_parser.classToFields:
            return {}
        field_ids_to_names = {}
        for field_id in self.ts_parser.classToFields[class_name]:
            field_ids_to_names[field_id] = self.ts_parser.fields[field_id]
        return field_ids_to_names

    def find_field_initialization(self, function_id: int) -> Dict[int, str]:
        class_name = self.find_class_by_function(function_id)
        if class_name not in self.ts_parser.classToFields:
            return {}
        field_inits = {}
        for field_id in self.ts_parser.classToFields[class_name]:
            field_inits[field_id] = self.ts_parser.fields_init[field_id]
        return field_inits

    def find_if_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        targets = self.find_nodes_by_type(root_node, "if_statement")
        if_statements = {}

        # print(add_line_numbers(source_code))

        for target in targets:
            condition_str = ""
            condition_line = 0
            true_branch_start_line = 0
            true_branch_end_line = 0
            else_branch_start_line = 0
            else_branch_end_line = 0
            block_num = 0
            for sub_target in target.children:
                if sub_target.type == "condition":
                    condition_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    condition_str = source_code[
                        sub_target.start_byte : sub_target.end_byte
                    ]
                if sub_target.type == "block":
                    if block_num == 0:
                        true_branch_start_line = (
                            source_code[: sub_target.start_byte].count("\n") + 1
                        )
                        true_branch_end_line = (
                            source_code[: sub_target.end_byte].count("\n") + 1
                        )
                        block_num += 1
                    elif block_num == 1:
                        else_branch_start_line = (
                            source_code[: sub_target.start_byte].count("\n") + 1
                        )
                        else_branch_end_line = (
                            source_code[: sub_target.end_byte].count("\n") + 1
                        )
                        block_num += 1
            if_statement_end_line = max(true_branch_end_line, else_branch_start_line)
            if_statements[(condition_line, if_statement_end_line)] = (
                condition_line,
                condition_str,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            )
            # print("------------------")
            # print(condition_line, if_statement_end_line)
            # print(condition_line)
            # print(condition_str)
            # print(true_branch_start_line, true_branch_end_line)
            # print(else_branch_start_line, else_branch_end_line)
            # print("------------------\n")
        return if_statements

    def find_switch_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        targets = self.find_nodes_by_type(root_node, "switch_expression")
        switch_statements = {}
        for target in targets:
            parenthesized_node = self.find_nodes_by_type(
                target, "parenthesized_expression"
            )[0]
            condition_line = (
                source_code[: parenthesized_node.start_byte].count("\n") + 1
            )
            parenthesized_node_str = source_code[
                parenthesized_node.start_byte : parenthesized_node.end_byte
            ]
            switch_statement_start_line = condition_line
            switch_statement_end_line = source_code[: target.end_byte].count("\n") + 1

            case_group = self.find_nodes_by_type(target, "switch_block_statement_group")
            items = []
            for case_item in case_group:
                case_start_line = source_code[: case_item.start_byte].count("\n") + 1
                case_end_line = source_code[: case_item.end_byte].count("\n") + 1

                switch_label_node = self.find_nodes_by_type(case_item, "switch_label")[
                    0
                ]
                switch_label = source_code[
                    switch_label_node.start_byte : switch_label_node.end_byte
                ]
                if "case " in switch_label:
                    label_str = switch_label.replace("case ", "").lstrip().rstrip()
                else:
                    label_str = ""
                items.append((label_str, case_start_line, case_end_line))

            switch_statements[
                (switch_statement_start_line, switch_statement_end_line)
            ] = (parenthesized_node_str, items)
        return switch_statements

    def extract_call_meta_data_in_single_function(
        self, current_function: Function
    ) -> Function:
        """
        :param current_function: Function object
        :return: Function object with updated parse tree and call info
        """
        tree: tree_sitter.Tree = self.ts_parser.parser.parse(
            bytes(current_function.function_code, "utf8")
        )
        current_function.set_parse_tree(tree)
        root_node: tree_sitter.Node = tree.root_node

        # Identify call site info and maintain the environment
        all_call_sites = self.find_nodes_by_type(root_node, "call_expression")
        white_call_sites = []

        for call_site_node in all_call_sites:
            callee_ids = self.find_callee(
                current_function.function_id,
                current_function.function_code,
                call_site_node,
            )
            if len(callee_ids) > 0:
                line_number = (
                    current_function.function_code[: call_site_node.start_byte].count(
                        "\n"
                    )
                    + 1
                )

                # Update the call graph
                for callee_id in callee_ids:
                    caller_id = current_function.function_id
                    if caller_id not in self.caller_callee_map:
                        self.caller_callee_map[caller_id] = set([])
                    self.caller_callee_map[caller_id].add(callee_id)
                    if callee_id not in self.callee_caller_map:
                        self.callee_caller_map[callee_id] = set([])
                    self.callee_caller_map[callee_id].add(caller_id)

        current_function.set_call_sites(white_call_sites)

        # compute the shared fields that can be accessed by the current function
        field_inits = self.find_field_initialization(current_function.function_id)
        current_function.set_field_inits_info(field_inits)

        # compute the scope of the if-statements to guide the further path feasibility validation
        if_statements = self.find_if_statements(
            current_function.function_code,
            current_function.parse_tree.root_node,
        )
        current_function.if_statements = if_statements

        # compute the scope of the switch statements to guide the further path feasibility validation
        switch_statements = self.find_switch_statements(
            current_function.function_code,
            current_function.parse_tree.root_node,
        )
        current_function.switch_statements = switch_statements
        return current_function

    def find_function_by_line_number(self, line_number: int) -> List[Function]:
        for function_id in self.environment:
            function = self.environment[function_id]
            if function.start_line_number <= line_number <= function.end_line_number:
                return [function]
        return []

    def find_node_by_line_number(
        self, line_number: int
    ) -> List[Tuple[str, tree_sitter.Node]]:
        code_node_list = []
        for function_id in self.environment:
            function = self.environment[function_id]
            if (
                not function.start_line_number
                <= line_number
                <= function.end_line_number
            ):
                continue
            all_nodes = TSAnalyzer.find_all_nodes(function.parse_tree.root_node)
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

    def collect_syntactic_types(self, node_list: List[Tuple[str, tree_sitter.Node]]):
        syntactic_types = set([])
        for code, node in node_list:
            if "expression" in node.type or "declarator" in node.type:
                sub_nodes = self.find_all_nodes(node)
                for sub_node in sub_nodes:
                    if (
                        any(char.isalpha() for char in sub_node.type)
                        and "identifier" not in sub_node.type
                        and "declarator" not in sub_node.type
                    ):
                        syntactic_types.add(sub_node.type)
        return syntactic_types
