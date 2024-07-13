from analyzer.sanitizer import *
from parser.response_parser import *
from model.detector import *
import json


class ValueFlowPipeline:
    def __init__(self,
                 project_name,
                 all_c_files,
                 inference_model_name,
                 inference_key_str,
                 validation_model_name,
                 validation_key_str,
                 spec_file,
                 pipeline_mode):
        self.project_name = project_name
        self.all_c_files = all_c_files
        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str
        self.validation_model_name = validation_model_name
        self.validation_key_str = validation_key_str
        self.spec_file = spec_file
        self.pipeline_mode = pipeline_mode
        self.detection_result = []
        self.buggy_traces = []

        self.all_c_obfuscated_files = {}

        for c_file_path in self.all_c_files:
            # self.all_c_obfuscated_files[c_file_path] = obfuscate(self.all_c_files[c_file_path])
            self.all_c_obfuscated_files[c_file_path] = self.all_c_files[c_file_path]
        self.ts_analyzer = TSAnalyzer(self.all_c_obfuscated_files)
        pass

    def start_detection(self):
        print("-----------------------------------------------------------")
        print("Start analyzing", self.project_name)
        print("-----------------------------------------------------------")

        log_dir_path = str(
            Path(__file__).resolve().parent.parent
            / ("log/initial_detection/" + self.inference_model_name + "/" + self.project_name)
        )
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        # Load the source code from the Java file
        single_detector = Detector(self.ts_analyzer, self.inference_model_name, self.inference_key_str, self.spec_file)
        detection_scopes = single_detector.extract_detection_scopes()
        print(len(detection_scopes))

        scope_id = 0
        for detection_scope in detection_scopes:
            if scope_id >= scope_count_bound != -1:
                break
            (start_end_lines, analyze_code) = detection_scope
            # iterative_cnt = 0

            output = single_detector.start_run_model(
                log_dir_path,
                analyze_code,
                self.project_name,
                scope_id
            )
            bug_num, traces, first_report = parse_bug_report(output)
            print(traces)
            # if len(traces) == bug_num:
            #     break
            # iterative_cnt += 1
            # if iterative_cnt > iterative_count_bound:
            #     bug_num = 0
            #     traces = []
            #     break
            self.detection_result.append((start_end_lines, analyze_code, bug_num, traces))
            scope_id += 1
        return

    def finalize_traces(self):
        for (start_end_lines, analyze_code, bug_num, traces) in self.detection_result:
            for trace in traces:
                finalized_trace = []
                for (line_number, _) in trace:
                    for function_id in start_end_lines:
                        (start_line_number, end_line_number) = start_end_lines[function_id]
                        if start_line_number <= line_number <= end_line_number:
                            function_name = self.ts_analyzer.environment[function_id].function_name
                            finalized_trace.append((function_id, function_name, line_number - start_line_number + 1))
                            break
                self.buggy_traces.append(finalized_trace)

            log_dir_path = str(
                Path(__file__).resolve().parent.parent
                / ("log/initial_detection/" + self.inference_model_name + "/" + self.project_name)
            )
            with open(log_dir_path + "/finalized_traces.json", "w") as file:
                json.dump({"finalized_traces": self.buggy_traces}, file, indent=4)
        return

    def start_sanitization(self, neural_check_strategy):
        passes = Passes(self.validation_model_name, self.validation_key_str, self.spec_file)

        if self.inference_model_name == self.validation_model_name:
            verification_log_file_dir = str(
                Path(__file__).resolve().parent.parent / ("log/hal_spot/" + self.inference_model_name)
            )
        else:
            verification_log_file_dir = str(
                Path(__file__).resolve().parent.parent / (
                        "log/hal_spot/" + self.inference_model_name + "_" + self.validation_model_name)
            )
        if not os.path.exists(verification_log_file_dir):
            os.makedirs(verification_log_file_dir)

        for (function_ids, analyze_code, bug_num, traces) in self.detection_result:
            # Syntactic check + Function check
            trace_cnt = 0
            cnt_dict = {
                "syntactic_check": 0,
                "function_check": 0,
                "call_graph_check": 0,
                "escape_check": 0,
                "control_flow_check": 0,
                "intra_data_flow_check": 0,
                "total": 0,
                "final": 0,
            }
            trace_check_results = []

            for trace in traces:
                cnt_dict_in_single_trace = {
                    "syntactic_check": 0,
                    "function_check": 0,
                    "call_graph_check": 0,
                    "escape_check": 0,
                    "control_flow_check": 0,
                    "intra_data_flow_check": 0,
                    "total": 0,
                    "final": 0,
                }

                trace_cnt += 1

                print("--------------------------------------------")
                print("Start to check the trace ", str(trace_cnt))
                print(trace)
                print("--------------------------------------------")

                # src and sink verification
                syntactic_check_result = passes.statement_check(self.single_ts_analyzer, trace)
                if syntactic_check_result:
                    cnt_dict["syntactic_check"] += 1
                    cnt_dict_in_single_trace["syntactic_check"] += 1
                print("syntactic_check_result: ", syntactic_check_result)
                print("--------------------------------------------")

                function_check_result, function_check_output_results = (
                    (passes.function_check(self.single_ts_analyzer, trace))
                    if neural_check_strategy["function_check"]
                    else (True, {})
                )
                if function_check_result:
                    cnt_dict["function_check"] += 1
                    cnt_dict_in_single_trace["function_check"] += 1

                case_name = self.c_file[self.c_file.rfind("/") + 1:].replace(".c", "")

                with open(
                        verification_log_file_dir
                        + "/"
                        + case_name
                        + "_"
                        + str(trace_cnt)
                        + "_function_check.json",
                        "w",
                ) as file:
                    json.dump(function_check_output_results, file, indent=4)
                print("function_check_result: ", function_check_result)
                print("--------------------------------------------")

                # inter-procedural verification
                call_graph_check_result = passes.call_graph_check(self.single_ts_analyzer, trace)
                if call_graph_check_result:
                    cnt_dict["call_graph_check"] += 1
                    cnt_dict_in_single_trace["call_graph_check"] += 1
                print("call_graph_check_result: ", call_graph_check_result)
                print("--------------------------------------------")

                # intra-procedural verification
                control_flow_check_result = passes.control_flow_check(self.single_ts_analyzer, trace)
                if control_flow_check_result:
                    cnt_dict["control_flow_check"] += 1
                    cnt_dict_in_single_trace["control_flow_check"] += 1
                print("control_flow_check_result: ", control_flow_check_result)
                print("--------------------------------------------")

                intra_data_flow_check_result, intra_data_flow_check_output_results = (
                    (passes.intra_data_flow_check(self.single_ts_analyzer, trace))
                    if neural_check_strategy["intra_dataflow_check"]
                    else (True, {})
                )
                if intra_data_flow_check_result:
                    cnt_dict["intra_data_flow_check"] += 1
                    cnt_dict_in_single_trace["intra_data_flow_check"] += 1
                with open(
                        verification_log_file_dir
                        + "/"
                        + case_name
                        + "_"
                        + str(trace_cnt)
                        + "_intra_data_flow_check.json",
                        "w",
                ) as file:
                    json.dump(intra_data_flow_check_output_results, file, indent=4)
                print("intra_data_flow_check_result: ", intra_data_flow_check_result)
                print("--------------------------------------------")

                escape_check_result = (
                    passes.escape_check(self.single_ts_analyzer, trace)
                    if neural_check_strategy["escape_check"]
                    else True
                )
                if escape_check_result:
                    cnt_dict["escape_check"] += 1
                    cnt_dict_in_single_trace["escape_check"] += 1
                print("escape_check_result: ", escape_check_result)
                print("--------------------------------------------")

                if (
                        syntactic_check_result
                        and call_graph_check_result
                        and intra_data_flow_check_result
                        and function_check_result
                        and escape_check_result
                        and intra_data_flow_check_result
                ):
                    cnt_dict["final"] += 1
                    cnt_dict_in_single_trace["final"] += 1

                trace_check_results.append([trace, cnt_dict_in_single_trace])

                print("--------------------------------------------")
                print("Finish checking the trace ", str(trace_cnt))
                print(
                    str(trace),
                    "\n",
                    "- syntactic_check_result: ",
                    syntactic_check_result,
                    "\n",
                    "- function_check_result: ",
                    function_check_result,
                    "\n",
                    "- call_graph_check_result: ",
                    call_graph_check_result,
                    "\n",
                    "- escape_check_result: ",
                    escape_check_result,
                    "\n",
                    "- control_flow_check: ",
                    control_flow_check_result,
                    "\n",
                    "- intra_data_flow_check_result: ",
                    intra_data_flow_check_result,
                )
                print("--------------------------------------------")

            print("----------------------------------------------------------")

            output_results = {
                "analyzed code": add_line_numbers(analyze_code),
                "trace_check_results": trace_check_results,
            }

            # output_json_file_name = Path(verification_log_file_dir) / (case_name + ".json")
            # with open(output_json_file_name, "w") as file:
            #     json.dump(output_results, file, indent=4)
        return

    def start_self_validation(self, step_by_step_verification: bool, global_self_consistency_k: bool, temperature: float):
        model = LLM(self.validation_model_name, self.validation_key_str, temperature)
        case_name = self.c_file[self.c_file.rfind("/") + 1:].replace(".java", "")
        print(
            "---------------------------------------------------------------------------------------"
        )
        print("Analyzing ", case_name)
        print(
            "---------------------------------------------------------------------------------------"
        )

        input_log_dir_path = str(
            Path(__file__).resolve().parent.parent
            / ("log/initial_detection/" + self.validation_model_name)
        )
        existing_json_file_names = set([])

        for root, dirs, files in os.walk(input_log_dir_path):
            for file in files:
                if case_name in file:
                    json_file_name = root + "/" + file
                    existing_json_file_names.add(json_file_name)

        with open(self.c_file, "r") as file:
            source_code = file.read()
            # new_code = obfuscate(source_code)
            new_code = source_code
            lined_new_code = add_line_numbers(new_code)

        assert len(existing_json_file_names) == 1

        for json_file_name in existing_json_file_names:
            verification_result = []

            output_json_file_name = json_file_name.replace(
                "initial_detection", "self_verification"
            )
            strategy = "step_by_step" if step_by_step_verification else "direct_ask"
            output_json_file_name = (
                    output_json_file_name.replace(".json", "")
                    + "_"
                    + strategy
                    + "_"
                    + str(global_self_consistency_k)
                    + "_"
                    + str(temperature)
                    + ".json"
            )

            if os.path.exists(output_json_file_name):
                continue

            with open(json_file_name) as existing_json_file:
                existing_result = json.load(existing_json_file)
                output = existing_result["response"]["response"]

                bug_num, traces, first_report = parse_bug_report(output)
                trace_cnt = 0

                for trace in traces:
                    debug_print("Validating trace", trace_cnt)
                    trace_cnt += 1
                    iterative_cnt = 0
                    input_token_cost = 0
                    output_token_cost = 0
                    answers = []
                    for i in range(global_self_consistency_k):

                        while True:
                            with open(
                                    Path(__file__).resolve().parent / "prompt" / self.spec_file,
                                    "r",
                            ) as read_file:
                                spec = json.load(read_file)

                            message = spec["task"] + "\n"
                            message += "\n".join(spec["analysis_rules"]) + "\n"
                            message += "\n".join(spec["analysis_examples"]) + "\n"

                            program = ""
                            for support_file in self.code_in_support_files:
                                program += (
                                        "The following is the file " + support_file + ":\n"
                                )
                                program += (
                                        "```\n"
                                        + self.code_in_support_files[support_file]
                                        + "\n```\n\n"
                                )
                            program += (
                                    "The following is the file "
                                    + json_file_name[json_file_name.rfind("/") + 1:]
                                    + ":\n"
                            )
                            program += "```\n" + lined_new_code + "\n```\n\n"

                            if step_by_step_verification:
                                message += (
                                        "\n".join(
                                            spec["meta_prompts_with_verification_step_by_step"]
                                        )
                                        + "\n"
                                )
                            else:
                                message += (
                                        "\n".join(
                                            spec["meta_prompts_with_verification_direct_ask"]
                                        )
                                        + "\n"
                                )
                            message = message.replace("<PROGRAM>", program).replace(
                                "<BUG_TRACE>", str(trace)
                            )
                            message = message.replace(
                                "<RE_EMPHASIZE_RULE>", "\n".join(spec["re_emphasize_rules"])
                            )

                            (
                                single_output,
                                single_input_token_cost,
                                single_output_token_cost,
                            ) = model.infer(message)
                            debug_print("------------------Output-------------------------")
                            debug_print(single_output)
                            input_token_cost += single_input_token_cost
                            output_token_cost += single_output_token_cost

                            if (
                                    "yes" in single_output.split("\n")[-1].lower()
                                    or "no" in single_output.split("\n")[-1].lower()
                            ):
                                break
                            if iterative_cnt > iterative_count_bound:
                                break
                        if single_output == "":
                            is_false_positive = False
                        else:
                            is_false_positive = (
                                    "no" in single_output.split("\n")[-1].lower()
                                    or "yes" not in single_output.split("\n")[-1].lower()
                            )
                        debug_print(not is_false_positive)
                        answers.append(not is_false_positive)
                    print("Hit: ", answers.count(True), answers.count(False))
                    is_report = answers.count(True) > answers.count(False)
                    verification_result.append(
                        [trace, output, is_report, input_token_cost, output_token_cost]
                    )

                output_results = {
                    "original code": existing_result["response"]["original code"],
                    "analyzed code": existing_result["response"]["analyzed code"],
                    "verification_result": verification_result,
                }

                with open(output_json_file_name, "w") as file:
                    json.dump(output_results, file, indent=4)
        return
