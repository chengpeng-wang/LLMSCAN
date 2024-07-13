import json
import openai
import time
import signal
import os
import tiktoken
import sys
from pathlib import Path
from model.llm import *
from typing import Dict
from model.utils import *
from parser.program_parser import *
from analyzer.extractor import *


class Detector:
    def __init__(self, ts_analyzer: TSAnalyzer, online_model_name: str, key, spec_file_name: str):
        self.ts_analyzer = ts_analyzer
        self.online_model_name = online_model_name
        self.key = key
        self.model = LLM(self.online_model_name, self.key, 0)
        self.spec_file_name = spec_file_name
        
        
    def extract_detection_sfa_scopes(self):
        print("Start extracting detection scopes")
        target_function_ids = {}
        for function_id in self.ts_analyzer.ts_parser.functionRawDataDic:
            function_root_node = self.ts_analyzer.environment[function_id].parse_tree.root_node
            function_code = self.ts_analyzer.environment[function_id].function_code
            all_call_sites = self.ts_analyzer.find_nodes_by_type(function_root_node, "call_expression")
            is_target = False
            for call_site in all_call_sites:
                if function_code[call_site.start_byte:call_site.end_byte].find("BN_secure_new") != -1:
                    is_target = True
                if function_code[call_site.start_byte:call_site.end_byte].find("BN_free") != -1:
                    is_target = False
            if is_target:
                target_function_ids[function_id] = self.ts_analyzer.environment[function_id].function_name
        print("Finish extracting detection scopes")
        return target_function_ids
    
    
    def start_run_sfa_check(self, function_code: str):
        prompt = """
        Task: If a function BN_secure_new() is called, i.e., `p = BN_secure_new();`, then we have invoke BN_free(p) after the last use of p. 
        Otherwise, please report a resource leak bug.
        Please check the function body. If it violate the above rule, please report it as a resource bug.
        Here is the function:
        {function_code}
        Please think step by step and give the answer in the following format:
        Answer: [Your explanation]
        Yes/No.
        Specifically, the second line should contain Yes if there is a bug. Otherwise, it should contain No.
        """
        response, input_token_cost, output_token_cost = self.model.infer(prompt.replace("{function_code}", function_code), False)
        print(response)
        return response
        
        

    def extract_detection_scopes(self, is_on_demand: bool = True):
        if not is_on_demand:
            analyzed_code = ""
            start_end_lines = {}
            last_line_number = 0
            for function_id in self.ts_analyzer.ts_parser.functionRawDataDic:
                function_content = self.ts_analyzer.ts_parser.functionRawDataDic[function_id]
                analyzed_code += function_content + "\n"
                new_last_line_number = analyzed_code.count("\n")
                start_end_lines[function_id] = (last_line_number + 1, new_last_line_number)
                last_line_number = new_last_line_number
            return [(start_end_lines, analyzed_code)]

        function_srcs_dict = {}
        function_sinks_dict = {}

        for function_id in self.ts_analyzer.environment:
            function = self.ts_analyzer.environment[function_id]
            sources = find_dbz_src(function.function_code, function.parse_tree.root_node)
            if len(sources) != 0:
                function_srcs_dict[function_id] = sources
            sinks = find_dbz_sink(function.function_code, function.parse_tree.root_node)
            if len(sinks) != 0:
                function_sinks_dict[function_id] = sinks

        for source_function_id in function_srcs_dict:
            print("------------------------------------")
            print(self.ts_analyzer.environment[source_function_id].function_code)

        for sink_function_id in function_sinks_dict:
            print("------------------------------------")
            print(self.ts_analyzer.environment[sink_function_id].function_code)

        scope_str_sets = set([])
        scopes = []
        for (start_end_lines, analyze_code) in self.extract_top_down_detection_scopes(function_srcs_dict, function_sinks_dict):
            scope_str = str(sorted(list(start_end_lines.keys())))
            if scope_str not in scope_str_sets:
                scopes.append((start_end_lines, analyze_code))
                scope_str_sets.add(scope_str)

        for (start_end_lines, analyze_code) in self.extract_bottom_up_detection_scopes(function_srcs_dict, function_sinks_dict):
            scope_str = str(sorted(list(start_end_lines.keys())))
            if scope_str not in scope_str_sets:
                scopes.append((start_end_lines, analyze_code))
                scope_str_sets.add(scope_str)

        for (start_end_lines, analyze_code) in scopes:
            print("--------------------------------------------------")
            print(add_line_numbers(analyze_code))
            for function_id in start_end_lines:
                print(self.ts_analyzer.environment[function_id].function_name, start_end_lines[function_id])
            print("--------------------------------------------------\n")
        return scopes

    def extract_top_down_detection_scopes(self, function_srcs_dict, function_sinks_dict):
        scopes = []
        top_down_call_stacks = []
        for function_id in function_srcs_dict:
            transitive_callees = self.compute_transitive_callees(function_id, self.ts_analyzer.caller_callee_map)
            for transitive_callee in transitive_callees:
                if transitive_callee not in function_sinks_dict:
                    continue
                if len(function_sinks_dict[transitive_callee]) == 0:
                    continue
                source_function_id = function_id
                sink_function_id = transitive_callee
                single_top_down_call_stack = self.compute_top_down_call_stacks_from_src_to_sink(source_function_id,
                                                                                                sink_function_id,
                                                                                                self.ts_analyzer.caller_callee_map)
                top_down_call_stacks.extend(single_top_down_call_stack)

        for call_stack in top_down_call_stacks:
            analyzed_code = ""
            start_end_lines = {}
            last_line_number = 0
            for function_id in call_stack:
                function_content = self.ts_analyzer.environment[function_id].function_code
                analyzed_code += function_content + "\n"
                new_last_line_number = analyzed_code.count("\n")
                start_end_lines[function_id] = (last_line_number + 1, new_last_line_number)
                last_line_number = new_last_line_number
            scopes.append((start_end_lines, analyzed_code))
        return scopes

    def extract_bottom_up_detection_scopes(self, function_srcs_dict, function_sinks_dict):
        scopes = []
        bottom_up_call_stacks = []
        for function_id in function_sinks_dict:
            transitive_callers = self.compute_transitive_callers(function_id, self.ts_analyzer.callee_caller_map)
            for transitive_caller in transitive_callers:
                if transitive_caller not in function_srcs_dict:
                    continue
                if len(function_srcs_dict[transitive_caller]) == 0:
                    continue
                source_function_id = transitive_caller
                sink_function_id = function_id
                single_bottom_up_call_stack = self.compute_bottom_up_call_stacks_from_src_to_sink(source_function_id,
                                                                                                sink_function_id,
                                                                                                self.ts_analyzer.callee_caller_map)
                bottom_up_call_stacks.extend(single_bottom_up_call_stack)

        for call_stack in bottom_up_call_stacks:
            analyzed_code = ""
            start_end_lines = {}
            last_line_number = 0
            for function_id in call_stack:
                function_content = self.ts_analyzer.environment[function_id].function_code
                analyzed_code += function_content + "\n"
                new_last_line_number = analyzed_code.count("\n")
                start_end_lines[function_id] = (last_line_number + 1, new_last_line_number)
                last_line_number = new_last_line_number
            scopes.append((start_end_lines, analyzed_code))
        return scopes

    def start_run_model(
        self,
        log_file_path: str,
        analyzed_code: str,
        project_name: str,
        scope_id: int,
    ):
        with open(
            Path(__file__).resolve().parent.parent / "prompt" / self.spec_file_name,
            "r",
        ) as read_file:
            spec = json.load(read_file)
        message = spec["task"] + "\n"
        message += "\n".join(spec["analysis_rules"]) + "\n"
        message += "\n".join(spec["output_constraints"]) + "\n"
        message += "\n".join(spec["analysis_examples"]) + "\n"

        analyzed_code = add_line_numbers(analyzed_code)
        program = "```\n" + analyzed_code + "\n```\n\n"

        message += "\n".join(spec["meta_prompts_without_reflection"]) + "\n"
        message = message.replace("<PROGRAM>", program)
        message = message.replace(
            "<RE_EMPHASIZE_RULE>", "\n".join(spec["re_emphasize_rules"])
        )

        response, input_token_cost, output_token_cost = self.model.infer(
            message, False
        )

        debug_print("------------------------------")
        debug_print(message)
        debug_print("------------------------------")
        debug_print(response)
        debug_print("------------------------------")
        output_results = {
            "analyzed code": analyzed_code,
            "response": response,
            "all program size": len(program.split("\n")),
            "input_token_cost": input_token_cost,
            "output_token_cost": output_token_cost,
        }

        with open(log_file_path + "/" + project_name + "_" + str(scope_id) + ".json", "w") as file:
            json.dump({"response": output_results}, file, indent=4)
        return response

    def compute_transitive_callers(self, function_id: int, callee_caller_map, visited=None) -> List[int]:
        if visited is None:
            visited = set()
        transitive_callers = []
        if function_id not in callee_caller_map or function_id in visited:
            return transitive_callers
        visited.add(function_id)
        for caller_id in callee_caller_map[function_id]:
            transitive_callers.append(caller_id)
            transitive_callers.extend(self.compute_transitive_callers(caller_id, callee_caller_map, visited))
        return transitive_callers

    def compute_transitive_callees(self, function_id: int, caller_callee_map, visited=None) -> List[int]:
        if visited is None:
            visited = set()
        transitive_callees = []
        if function_id not in caller_callee_map or function_id in visited:
            return transitive_callees
        visited.add(function_id)
        for callee_id in caller_callee_map[function_id]:
            transitive_callees.append(callee_id)
            transitive_callees.extend(self.compute_transitive_callees(callee_id, caller_callee_map, visited))
        return transitive_callees

    def compute_bottom_up_call_stacks_from_src_to_sink(self, src_function_id: int, sink_function_id: int,
                                                       callee_caller_map, visited=None) -> List[List[int]]:
        if visited is None:
            visited = set()
        bottom_up_call_stacks = []
        if src_function_id == sink_function_id:
            return [[src_function_id]]
        if src_function_id not in callee_caller_map or src_function_id in visited:
            return bottom_up_call_stacks
        visited.add(src_function_id)
        for caller_id in callee_caller_map[src_function_id]:
            if caller_id == sink_function_id:
                bottom_up_call_stacks.append([caller_id])
            else:
                for call_stack in self.compute_bottom_up_call_stacks_from_src_to_sink(caller_id, sink_function_id,
                                                                                      callee_caller_map, visited):
                    call_stack.append(caller_id)
                    bottom_up_call_stacks.append(call_stack)
        return bottom_up_call_stacks

    def compute_top_down_call_stacks_from_src_to_sink(self, src_function_id: int, sink_function_id: int,
                                                      caller_callee_map, visited=None) -> List[List[int]]:
        if visited is None:
            visited = set()
        top_down_call_stacks = []
        if src_function_id == sink_function_id:
            return [[src_function_id]]
        if src_function_id not in caller_callee_map or src_function_id in visited:
            return top_down_call_stacks
        visited.add(src_function_id)
        for callee_id in caller_callee_map[src_function_id]:
            if callee_id == sink_function_id:
                top_down_call_stacks.append([callee_id])
            else:
                for call_stack in self.compute_top_down_call_stacks_from_src_to_sink(callee_id, sink_function_id,
                                                                                     caller_callee_map, visited):
                    call_stack.append(callee_id)
                    top_down_call_stacks.append(call_stack)
        return top_down_call_stacks
