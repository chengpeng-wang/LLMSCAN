import copy
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from TSAgent.TS_analyzer import TSAnalyzer
from TSAgent.TS_parser import TSParser
from TSAgent.TS_transformer import TSFunctionTransformer
from utility.function import *
from utility.logger import Logger
from utility.environment import Environment
from TSAgent.TS_transformer import TSFunctionTransformer
from LMAgent.spec.src_extractor import SrcExtractor
from LMAgent.spec.sink_extractor import SinkExtractor
from LMAgent.flow.intra_flow_propagator import IntraFlowPropagator
from LMAgent.flow.inter_flow_validator import InterFlowValidator


class DFA:
    """
    DFA class is the main engine of LLM-driven data-flow analysis
    """

    def __init__(
        self,
        c_file_path: str,
        src_spec_file_path: str,
        sink_spec_file_path: str,
        flow_propagator_file_path: str,
        flow_validator_file_path: str,
        online_model_name: str,
        offline_model_path: str,
        intra_reflexion: bool,
        is_path_sensitivity: bool,
        validate_reflexion: bool,
        is_solving_refine: bool,
        solving_refine_number: int,
        is_online: bool,
        openai_key: str,
    ) -> None:
        """
        Initialize DFA with a C file path.
        Currently we only analyze a single C file
        :param c_file_path: The path of the C file.
        """
        self.c_file_path: str = c_file_path
        self.proj_path = self.c_file_path[
            self.c_file_path.rfind("/") + 1 : self.c_file_path.rfind(".c")
        ]
        self.ts_analyzer = TSAnalyzer(c_file_path)
        self.main_ids = self.ts_analyzer.main_ids
        self.online_model_name = online_model_name
        self.offline_model_path = offline_model_path

        self.intra_reflexion = intra_reflexion
        self.is_path_sensitivity = is_path_sensitivity
        self.validate_reflexion = validate_reflexion
        self.is_solving_refine = is_solving_refine
        self.solving_refine_number = solving_refine_number

        # src/sink spec path
        self.src_spec_file_path = src_spec_file_path
        self.sink_spec_file_path = sink_spec_file_path
        self.flow_propagator_file_path = flow_propagator_file_path
        self.flow_validator_file_path = flow_validator_file_path

        # Eliminate the comments
        self.function_transformer = TSFunctionTransformer(self.ts_analyzer)

        # LM agent list
        # self.offline_model = OfflineModel(offline_model_path, 0.1)
        self.offline_model = None
        self.src_extractor = SrcExtractor(
            self.src_spec_file_path,
            self.online_model_name,
            self.offline_model,
            is_online,
            openai_key,
        )
        self.sink_extractor = SinkExtractor(
            self.sink_spec_file_path,
            self.online_model_name,
            self.offline_model,
            is_online,
            openai_key,
        )

        self.ifp_propagator = IntraFlowPropagator(
            self.flow_propagator_file_path,
            self.online_model_name,
            self.offline_model,
            is_online,
            openai_key,
        )

        self.validator = InterFlowValidator(
            self.flow_validator_file_path,
            self.online_model_name,
            self.offline_model,
            is_online,
            openai_key,
        )

        # logger configuration
        self.logger_cnt = 0

        # clear previous log
        cwd = Path(__file__).resolve().parent
        self.log_dir_path = str(cwd / "../../log/bug" / self.proj_path.split("/")[-1])

        if os.path.exists(self.log_dir_path):
            shutil.rmtree(self.log_dir_path)
        os.makedirs(self.log_dir_path)
        shutil.copy(c_file_path, self.log_dir_path)

        # Environment
        self.environment = Environment()

        # Bug candidates before validation
        self.bug_candidates: Dict[
            int, List[List[Tuple[int, LocalValue]]]
        ] = {}  # function_id --> bug traces

        # Bug candidates after validation
        self.bugs: Dict[
            int, List[List[Tuple[int, LocalValue]]]
        ] = {}  # function_id --> bug traces
        return

    def extract_call_meta_data_in_single_function(
        self, current_function: Function
    ) -> Function:
        """
        :param current_function: Function object
        :return: Function object with updated parse tree and call info
        """
        tree: tree_sitter.Tree = self.ts_analyzer.ts_parser.parser.parse(
            bytes(current_function.SSI_function_without_comments, "utf8")
        )
        current_function.set_parse_tree(tree)
        root_node: tree_sitter.Node = tree.root_node

        # Identify call site info and maintain the environment
        all_call_sites = TSParser.find_nodes(root_node, "call_expression")
        white_call_sites = []

        for call_site_node in all_call_sites:
            callee_ids = self.ts_analyzer.find_callee(
                current_function.function_id,
                current_function.SSI_function_without_comments,
                call_site_node,
            )
            if len(callee_ids) > 0:
                line_number = (
                    current_function.SSI_function_without_comments[
                        : call_site_node.start_byte
                    ].count("\n")
                    + 1
                )

                # Update the environment
                for callee_id in callee_ids:
                    self.environment.insert_caller_callee_pair(
                        current_function.function_id, line_number, callee_id
                    )

                # Extract arg and output info for each call site
                args: List[LocalValue] = TSAnalyzer.find_call_site_args(
                    current_function.SSI_function_without_comments,
                    call_site_node,
                    line_number,
                )
                outputs = TSAnalyzer.find_call_site_outputs(
                    current_function.SSI_function_without_comments,
                    current_function.parse_tree.root_node,
                    call_site_node,
                    line_number,
                )

                current_function.update_line_to_call_site_info(
                    line_number, call_site_node, args, outputs, callee_ids
                )
                white_call_sites.append((call_site_node, line_number))

        current_function.set_call_sites(white_call_sites)

        # Identify parameters and rets
        paras = TSAnalyzer.find_function_parameters(
            current_function.SSI_function_without_comments,
            current_function.parse_tree.root_node,
        )
        print("hitttt: ", len(paras))


        rets = TSAnalyzer.find_function_returns(
            current_function.SSI_function_without_comments,
            current_function.parse_tree.root_node,
        )
        current_function.set_para_ret_info(paras, rets)

        # compute the scope of the if-statements to guide the further path feasibility validation
        if_statements = self.ts_analyzer.find_if_statements(
            current_function.SSI_function_without_comments,
            current_function.parse_tree.root_node,
        )
        current_function.if_statements = if_statements

        return current_function

    def construct_summary_start_end_points(
        self, current_function: Function, start_para_indexes: set[int], logger: Logger
    ) -> Tuple[List[LocalValue], List[LocalValue]]:
        # Extract the source and sink values
        self.src_extractor.apply(
            current_function, logger, True
        )  # True: use parser to localize source values

        self.sink_extractor.apply(
            current_function, logger, True
        )  # True: use parser to localize sink values

        # Compute intra-procedural summaries
        # TODO: to be optimized. The summaries can be computed in a more demand-driven manner

        # summary srcs: source values, output values of call sites, arg values of current function
        summary_srcs: List[LocalValue] = self.src_extractor.srcs

        # summary sinks: sink values, input values of call sites, return values of current function
        summary_sinks: List[LocalValue] = self.sink_extractor.sinks

        print(current_function.paras)

        # set interesting parameters and return values as the sources and sinks, respectively
        for para in current_function.paras:
            if para.index in start_para_indexes:
                summary_srcs.append(para)

        summary_sinks.extend(current_function.rets)

        # set output values and (actual) arguments as the sources and sinks, respectively
        for line_number in current_function.line_to_call_site_info:
            (
                call_site_node,
                args,
                outputs,
                callee_ids,
            ) = current_function.line_to_call_site_info[line_number]
            summary_srcs.extend(outputs)
            summary_sinks.extend(args)

        # deduplicate srcs/sinks
        unique_summary_srcs = []
        unique_summary_sinks = []
        for i in range(len(summary_srcs)):
            is_appear = False
            for j in range(i):
                if str(summary_srcs[i]) == str(summary_srcs[j]):
                    is_appear = True
                    break
            if not is_appear:
                unique_summary_srcs.append(summary_srcs[i])

        for i in range(len(summary_sinks)):
            is_appear = False
            for j in range(i):
                if str(summary_sinks[i]) == str(summary_sinks[j]):
                    is_appear = True
                    break
            if not is_appear:
                unique_summary_sinks.append(summary_sinks[i])
        return unique_summary_srcs, unique_summary_sinks

    @staticmethod
    def check_context_realizability(
        context_ids: List[int], context_id: int
    ) -> Tuple[bool, List[int]]:
        """
        :param context_ids: current context
        :param context_id: current function id
        :return whether the context_ids ++ context_id is realizable. Update the context if realizable
        """
        if len(context_ids) == 0:
            return True, [context_id]
        last_context_id = context_ids[-1]
        new_context_ids = copy.deepcopy(context_ids)
        if last_context_id < 0 < context_id:
            if last_context_id + context_id != 0:
                return False, new_context_ids
            else:
                new_context_ids.pop()
                return True, new_context_ids
        new_context_ids.append(context_id)
        return True, new_context_ids

    def extended_CFL_reachability_search(
        self,
        function_id: int,
        context_ids: List[int],
        trace: List[Tuple[int, LocalValue]],
    ) -> List[List[Tuple[int, LocalValue]]]:
        """
        :param function_id: current function
        :param context_ids: current call stack, used to achieve context sensitivity
        :param trace: previous trace starting from source nodes
        :return all the extended-CFL-reachable traces taking a trace in traces as the prefix and reaching a sink
        """
        assert self.environment.is_analyzed(function_id)
        assert len(trace) > 0
        (current_function_id, current_node) = trace[-1]
        assert current_function_id == function_id

        function = self.environment.analyzed_functions[function_id]
        bug_traces = []

        for summary in function.reachable_summaries:
            (start, end) = summary
            if current_node != start:
                continue
            if end.v_type == ValueType.SINK:
                trace_augmented_to_sink = copy.deepcopy(trace)
                trace_augmented_to_sink.append((function_id, end))
                bug_traces.append(trace_augmented_to_sink)
                continue
            if end.v_type == ValueType.ARG:
                (_, _, _, callee_ids) = function.line_to_call_site_info[end.line_number]
                for callee_id in callee_ids:
                    (
                        is_realizable,
                        augmented_context_ids,
                    ) = DFA.check_context_realizability(context_ids, callee_id * (-1))
                    if is_realizable:
                        trace_augmented_from_arg = copy.deepcopy(trace)
                        trace_augmented_from_arg.append((function_id, end))
                        callee_para_value = self.environment.analyzed_functions[
                            callee_id
                        ].find_para_value_by_index(end.index)
                        trace_augmented_from_arg.append((callee_id, callee_para_value))

                        bug_traces_augmented_from_arg = (
                            self.extended_CFL_reachability_search(
                                callee_id,
                                augmented_context_ids,
                                trace_augmented_from_arg,
                            )
                        )
                        bug_traces.extend(bug_traces_augmented_from_arg)
                continue
            if end.v_type == ValueType.RET:
                caller_sites = self.environment.callee_caller_map[function_id]
                for caller_id, line_number in caller_sites:
                    (
                        is_realizable,
                        augmented_context_ids,
                    ) = DFA.check_context_realizability(context_ids, caller_id)
                    if is_realizable:
                        augmented_context_ids = copy.deepcopy(context_ids)
                        augmented_context_ids.append(caller_id)

                        trace_augmented_from_ret = copy.deepcopy(trace)
                        trace_augmented_from_ret.append((function_id, end))
                        caller_function = self.environment.analyzed_functions[caller_id]
                        output_values = (
                            caller_function.find_output_value_by_line_number(
                                line_number
                            )
                        )
                        if len(output_values) == 0:
                            continue

                        caller_output_value = output_values[0]
                        trace_augmented_from_ret.append(
                            (caller_id, caller_output_value)
                        )

                        bug_traces_augmented_from_ret = (
                            self.extended_CFL_reachability_search(
                                caller_id,
                                augmented_context_ids,
                                trace_augmented_from_ret,
                            )
                        )
                        bug_traces.extend(bug_traces_augmented_from_ret)
                continue

            # error prone
            if end.v_type == ValueType.FIELD:
                # analyze callee
                for caller_id, line_number in self.environment.caller_callee_map:
                    if caller_id == function_id:
                        for callee_id in self.environment.caller_callee_map[
                            (caller_id, line_number)
                        ]:
                            (
                                is_realizable,
                                augmented_context_ids,
                            ) = DFA.check_context_realizability(
                                context_ids, callee_id * (-1)
                            )
                            if is_realizable:
                                trace_augmented_from_field = copy.deepcopy(trace)
                                trace_augmented_from_field.append((function_id, end))
                                for (
                                    callee_src,
                                    callee_sink,
                                ) in self.environment.analyzed_functions[
                                    callee_id
                                ].reachable_summaries:
                                    if callee_src.v_type != ValueType.FIELD:
                                        continue
                                    if callee_src.name == end.name:
                                        trace_augmented_from_field.append(
                                            (callee_id, callee_src)
                                        )

                                        bug_traces_augmented_from_field = (
                                            self.extended_CFL_reachability_search(
                                                callee_id,
                                                augmented_context_ids,
                                                trace_augmented_from_field,
                                            )
                                        )
                                        bug_traces.extend(
                                            bug_traces_augmented_from_field
                                        )

                # analyze caller
                for callee_id in self.environment.callee_caller_map:
                    if callee_id == function_id:
                        for (
                            caller_id,
                            line_number,
                        ) in self.environment.callee_caller_map[callee_id]:
                            (
                                is_realizable,
                                augmented_context_ids,
                            ) = DFA.check_context_realizability(context_ids, caller_id)
                            if is_realizable:
                                trace_augmented_from_field = copy.deepcopy(trace)
                                trace_augmented_from_field.append((function_id, end))
                                for (
                                    caller_src,
                                    caller_sink,
                                ) in self.environment.analyzed_functions[
                                    caller_id
                                ].reachable_summaries:
                                    if caller_src.v_type != ValueType.FIELD:
                                        continue
                                    if caller_src.name == end.name:
                                        trace_augmented_from_field.append(
                                            (callee_id, caller_src)
                                        )

                                        bug_traces_augmented_from_field = (
                                            self.extended_CFL_reachability_search(
                                                caller_id,
                                                augmented_context_ids,
                                                trace_augmented_from_field,
                                            )
                                        )
                                        bug_traces.extend(
                                            bug_traces_augmented_from_field
                                        )
                continue
        return bug_traces

    def search_from_srcs_in_single_function(
        self, function_id: int
    ) -> List[List[Tuple[int, LocalValue]]]:
        """
        :param function_id: current function
        :return all the traces starting from the source to the function with function_id and ending at the sink
        """
        bug_traces = []
        function = self.environment.analyzed_functions[function_id]
        srcs = []
        for summary in function.reachable_summaries:
            (start, end) = summary
            if start in srcs:
                continue
            if start.v_type == ValueType.SRC:
                srcs.append(start)
                traces_from_src = self.extended_CFL_reachability_search(
                    function_id, [], [(function_id, start)]
                )
                bug_traces.extend(traces_from_src)
        return bug_traces

    def analyze_function(self, function_id: int, start_para_indexes: set[int]) -> None:
        """
        :param function_id: function id
        :param start_para_indexes: the indexes of interesting parameters
        """
        """
        Analysis Steps:
        1. Preprocessing: Transformation + Call site extraction
        2. Intra-procedural summary generation: Generate summaries from start points to end points
                Start points: source values, output values of call sites, arg values of current function
                End points: sink values, intput values of call sites, return values of current function
        3. Inter-procedural analysis: Process callees of current function on demand
        """
        self.logger_cnt += 1
        logger = Logger(self.proj_path, function_id, self.logger_cnt)

        # Avoid redundantly analyzing the same function
        if self.environment.is_analyzed(function_id):
            print("always existed: ", str(function_id))
            current_function = self.environment.analyzed_functions[function_id]
        else:
            print("Preprocessing...")
            (name, original_function) = self.ts_analyzer.ts_parser.methods[function_id]
            print(name)
            print(function_id)
            current_function = Function(function_id, name, original_function)

            self.function_transformer.transform(
                function_id, current_function.original_function
            )
            current_function.SSI_function = self.function_transformer.SSI

            current_function.SSI_function_without_comments = (
                self.function_transformer.SSI_without_comments
            )
            current_function.lined_SSI_function_without_comments = (
                self.function_transformer.lined_SSI_function_without_comments
            )

            # print(current_function.lined_SSI_function_without_comments)
            # print(current_function.SSI_function_without_comments)

            current_function.parse_tree = self.ts_analyzer.ts_parser.parser.parse(
                bytes(self.function_transformer.SSI_without_comments, "utf8")
            )
            current_function = self.extract_call_meta_data_in_single_function(
                current_function
            )

        # TODO: This will introduce redundancy in the summary generation
        (summary_srcs, summary_sinks) = self.construct_summary_start_end_points(
            current_function, start_para_indexes, logger
        )

        for src in summary_srcs:
            print(str(src))

        print("Generating intra-procedural summaries...")
        reachable_summaries, unreachable_summaries = self.ifp_propagator.apply(
            current_function, summary_srcs, summary_sinks, logger, self.intra_reflexion
        )
        current_function.extend_function_summaries(
            reachable_summaries, unreachable_summaries
        )
        self.environment.set_analyzed_function(function_id, current_function)

        # Process callees
        print("Processing callees...")
        for call_site_node, line_number in current_function.call_site_nodes:
            (_, args, rets, callee_ids) = current_function.line_to_call_site_info[
                line_number
            ]
            # TODO: We need to merge states here. Currently, we only use consider one possible callee
            callee_id = callee_ids[0]
            para_indexes = set([])

            for start, end in reachable_summaries:
                if end.line_number != line_number:
                    continue
                if end.v_type == ValueType.ARG:
                    para_indexes.add(end.index)
            print("Analyzing the function: ", str(function_id))
            print(para_indexes, callee_id, "\n")
            (callee_function_name, callee_function) = self.ts_analyzer.ts_parser.methods[callee_id]
            print(callee_function_name)
            self.analyze_function(callee_id, para_indexes)

        # CFL reachability solving
        bug_traces = self.search_from_srcs_in_single_function(function_id)
        self.bug_candidates[function_id] = bug_traces
        return

    def analyze(self) -> None:
        """
        Process each main function
        """
        print("Analyzing......")
        for main_id in self.main_ids:
            self.analyze_function(main_id, set([]))
        return

    def debug(self) -> None:
        print("Debugging......")
        for function_id in self.environment.analyzed_functions:
            self.environment.analyzed_functions[function_id].print_function_summary()
        return

    def validate(self) -> None:
        print("Validating......")
        if not self.is_path_sensitivity:
            for src_function_id in self.bug_candidates:
                for trace in self.bug_candidates[src_function_id]:
                    if src_function_id not in self.bugs:
                        self.bugs[src_function_id] = []
                    self.bugs[src_function_id].append(trace)
        else:
            for src_function_id in self.bug_candidates:
                for trace in self.bug_candidates[src_function_id]:
                    self.logger_cnt += 1
                    logger = Logger(self.proj_path, src_function_id, self.logger_cnt)
                    if self.validator.apply(
                        self.environment,
                        trace,
                        logger,
                        self.validate_reflexion,
                        self.is_solving_refine,
                        self.solving_refine_number,
                    ):
                        if src_function_id not in self.bugs:
                            self.bugs[src_function_id] = []
                        self.bugs[src_function_id].append(trace)
        return

    def report(self) -> None:
        print("Reporting......")
        bug_report = {}
        bug_number = 0
        bug_items = []
        bug_candidates = []
        for src_function_id in self.bugs:
            bug_number += len(self.bugs[src_function_id])
            for trace in self.bugs[src_function_id]:
                bug_item = []
                for function_id, value in trace:
                    node = {
                        "function_id": function_id,
                        "function_name": self.environment.analyzed_functions[
                            function_id
                        ].function_name,
                        "value name": value.name,
                        "line number": value.line_number,
                    }
                    bug_item.append(node)
                bug_items.append(bug_item)
        for src_function_id in self.bug_candidates:
            for trace in self.bug_candidates[src_function_id]:
                bug_candidate = []
                for function_id, value in trace:
                    node = {
                        "function_id": function_id,
                        "function_name": self.environment.analyzed_functions[
                            function_id
                        ].function_name,
                        "value name": value.name,
                        "line number": value.line_number,
                    }
                    bug_candidate.append(node)
                bug_candidates.append(bug_candidate)
        bug_report["bug_item_number"] = bug_number
        bug_report["bug_candidate_number"] = len(bug_candidates)
        bug_report["bug_items"] = bug_items
        bug_report["bug_candidates"] = bug_candidates

        with open(self.log_dir_path + "/report.json", "w") as file:
            json.dump(bug_report, file, indent=4)

        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        current_date = datetime.now().strftime("%Y-%m-%d")

        cwd = Path(__file__).resolve().parent
        log_dir_path = str(cwd / "../../log/date" / current_date)
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        log_dir_path = str(
            cwd
            / "../../log/date"
            / current_date
            / (self.proj_path.split("/")[-1] + "_" + current_time)
        )
        result_path = str(cwd / "../../log/bug" / self.proj_path.split("/")[-1])
        shutil.copytree(result_path, log_dir_path)

        print("Report generated!\n")
        return

    def compute_total_token_cost(self):
        # LM agent list
        input_cost = 0
        output_cost = 0

        input_cost += self.src_extractor.total_input_token_cost
        output_cost += self.src_extractor.total_output_token_cost

        input_cost += self.sink_extractor.total_input_token_cost
        output_cost += self.sink_extractor.total_output_token_cost

        input_cost += self.ifp_propagator.total_input_token_cost
        output_cost += self.ifp_propagator.total_output_token_cost

        input_cost += self.validator.total_input_token_cost
        output_cost += self.validator.total_output_token_cost
        return input_cost, output_cost
