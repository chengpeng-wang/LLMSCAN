from analyzer.sanitizer import *
from parser.response_parser import *
from model.detector import *
import json


def start_llm_hal_spot_run(
    java_file,
    code_in_support_files,
    inference_online_model_name,
    inference_key,
    validation_online_model_name,
    validation_key,
    spec_file_name,
    analysis_mode,
    neural_check_strategy,
    is_measure_token_cost,
):
    cnt = 0

    case_name = java_file[java_file.rfind("/") + 1 :].replace(".java", "")
    print(
        "---------------------------------------------------------------------------------------"
    )
    print("Analyzing ", case_name)
    print(
        "---------------------------------------------------------------------------------------"
    )

    is_exist_inference = False
    log_dir_path = str(
        Path(__file__).resolve().parent.parent
        / ("log/initial_inference/" + inference_online_model_name)
    )
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)
    existing_json_file_names = set([])

    for root, dirs, files in os.walk(log_dir_path):
        for file in files:
            if case_name in file:
                is_exist_inference = True
                cnt += 1
                json_file_name = root + "/" + file
                existing_json_file_names.add(json_file_name)
    # if is_exist_inference:
    #     return

    # Verification
    if inference_online_model_name == validation_online_model_name:
        verification_log_file_dir = str(
            Path(__file__).resolve().parent.parent
            / ("log/hal_spot/" + inference_online_model_name)
        )
    else:
        verification_log_file_dir = str(
            Path(__file__).resolve().parent.parent
            / (
                "log/hal_spot/"
                + inference_online_model_name
                + "_"
                + validation_online_model_name
            )
        )
    if not os.path.exists(verification_log_file_dir):
        os.makedirs(verification_log_file_dir)

    is_exist_spot = False

    for root, dirs, files in os.walk(verification_log_file_dir):
        for file in files:
            if case_name in file:
                is_exist_spot = True
                break

    print(is_exist_inference, is_exist_spot)
    if is_exist_spot and is_exist_inference:
        return

    with open(java_file, "r") as file:
        source_code = file.read()
        new_code = delete_comments(source_code)
        lined_new_code = add_line_numbers(new_code)

    total_traces = []

    # Analyze the code with LLM or load existing response
    if not is_exist_inference or analysis_mode == "eager":
        detector = Detector(inference_online_model_name, inference_key, spec_file_name)
        json_file_name = java_file[java_file.rfind("/") + 1 :].replace(".java", "")

        iterative_cnt = 0
        while True:
            output = detector.start_run_model(
                java_file,
                json_file_name,
                log_dir_path,
                source_code,
                lined_new_code,
                code_in_support_files,
                False,
                is_measure_token_cost,
            )
            bug_num, traces, first_report = parse_bug_report(output)
            print(traces)
            if len(traces) == bug_num:
                break
            iterative_cnt += 1
            if iterative_cnt > iterative_count_bound:
                bug_num = 0
                traces = []
                break
        total_traces = traces

        # # Dump initial inference
        # existing_result = {
        #     "response": {
        #         "original code": source_code,
        #         "analyzed code": lined_new_code,
        #         "response": output,
        #         "intput token": 0,
        #         "output token": 0,
        #         "program line": 0
        #     }
        # }
        # output_json_file_name = (Path(log_dir_path).parent.parent / "initial_inference"
        #                          / online_model_name / (case_name + "_" + str(cnt) + ".json"))
        # with open(output_json_file_name, "w") as file:
        #     json.dump(existing_result, file, indent=4)

    else:
        for json_file_name in existing_json_file_names:
            with open(json_file_name) as existing_json_file:
                print(json_file_name)
                existing_result = json.load(existing_json_file)
                print(existing_result)

                output = existing_result["response"]["response"]
                bug_num, traces, report = parse_bug_report(output)

                if bug_num != len(traces):
                    bug_num = 0
                    traces = []

                print(
                    "---------------------------------------------------------------------------------------"
                )
                print("Bug Num: ", bug_num)
                print("Trace Num: ", len(traces))
                print("Lined Code: \n" + lined_new_code)
                print(
                    "---------------------------------------------------------------------------------------"
                )
                total_traces.extend(traces)

    ts_analyzer = TSAnalyzer(java_file, source_code, new_code, code_in_support_files)

    passes = Passes(validation_online_model_name, validation_key, spec_file_name)

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

    history_trace_strs = set([])

    for trace in total_traces:
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

        if str(trace) in history_trace_strs:
            continue
        history_trace_strs.add(str(trace))

        trace_cnt += 1
        cnt_dict["total"] += 1
        cnt_dict_in_single_trace["total"] += 1

        print("--------------------------------------------")
        print("Start to check the trace ", str(trace_cnt))
        print(trace)
        print("--------------------------------------------")

        # src and sink verification
        syntactic_check_result = passes.statement_check(ts_analyzer, trace)
        if syntactic_check_result:
            cnt_dict["syntactic_check"] += 1
            cnt_dict_in_single_trace["syntactic_check"] += 1
        print("syntactic_check_result: ", syntactic_check_result)
        print("--------------------------------------------")

        function_check_result, function_check_output_results = (
            (passes.function_check(ts_analyzer, trace, is_measure_token_cost))
            if neural_check_strategy["function_check"]
            else (True, {})
        )
        if function_check_result:
            cnt_dict["function_check"] += 1
            cnt_dict_in_single_trace["function_check"] += 1
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
        call_graph_check_result = passes.call_graph_check(ts_analyzer, trace)
        if call_graph_check_result:
            cnt_dict["call_graph_check"] += 1
            cnt_dict_in_single_trace["call_graph_check"] += 1
        print("call_graph_check_result: ", call_graph_check_result)
        print("--------------------------------------------")

        # intra-procedural verification
        control_flow_check_result = passes.control_flow_check(ts_analyzer, trace)
        if control_flow_check_result:
            cnt_dict["control_flow_check"] += 1
            cnt_dict_in_single_trace["control_flow_check"] += 1
        print("control_flow_check_result: ", control_flow_check_result)
        print("--------------------------------------------")

        intra_data_flow_check_result, intra_data_flow_check_output_results = (
            (passes.intra_data_flow_check(ts_analyzer, trace, is_measure_token_cost))
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
            passes.escape_check(ts_analyzer, trace, is_measure_token_cost)
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

    print(
        "---------------------------------------------------------------------------------------"
    )
    print(case_name, " is analyzed!")

    output_results = {
        "original code": source_code,
        "analyzed code": lined_new_code,
        "trace_check_results": trace_check_results,
    }

    output_json_file_name = Path(verification_log_file_dir) / (case_name + ".json")
    with open(output_json_file_name, "w") as file:
        json.dump(output_results, file, indent=4)

    print(
        "---------------------------------------------------------------------------------------\n\n"
    )
    return cnt_dict


# Baseline 1 (deprecated)
def start_self_reflection_run(
    java_file, code_in_support_files, online_model_name, key, spec_file_name
):
    case_name = java_file[java_file.rfind("/") + 1 :].replace(".java", "")
    print(
        "---------------------------------------------------------------------------------------"
    )
    print("Analyzing ", case_name)
    print(
        "---------------------------------------------------------------------------------------"
    )

    input_log_dir_path = str(
        Path(__file__).resolve().parent.parent
        / ("log/initial_inference/" + online_model_name)
    )
    self_reflection_output_log_dir_path = str(
        Path(__file__).resolve().parent.parent
        / ("log/self_reflection/" + online_model_name)
    )
    existing_json_file_names = set([])

    for root, dirs, files in os.walk(input_log_dir_path):
        for file in files:
            if case_name in file:
                json_file_name = root + "/" + file
                existing_json_file_names.add(json_file_name)

    with open(java_file, "r") as file:
        source_code = file.read()
        new_code = delete_comments(source_code)
        lined_new_code = add_line_numbers(new_code)

    total_traces_dic = {}

    assert len(existing_json_file_names) > 0

    for json_file_name in existing_json_file_names:
        with open(json_file_name) as existing_json_file:
            existing_result = json.load(existing_json_file)
            output = existing_result["response"]["response"]

            bug_num, traces, first_report = parse_bug_report(output)
            detector = Detector(online_model_name, key, spec_file_name)
            json_file_name_without_suffix = json_file_name[
                json_file_name.rfind("/") + 1 :
            ].replace(".json", "")

            iterative_cnt = 0
            while True:
                print(iterative_cnt, ": start to run the model...")
                output = detector.start_run_model(
                    java_file,
                    json_file_name_without_suffix,
                    self_reflection_output_log_dir_path,
                    source_code,
                    lined_new_code,
                    code_in_support_files,
                    True,
                    False,
                    first_report,
                )
                bug_num, traces, report = parse_bug_report(output)
                if len(traces) == bug_num:
                    break
                iterative_cnt += 1
                if iterative_cnt > iterative_count_bound:
                    bug_num = 0
                    traces = []
                    break

            print("Bug Num: ", bug_num)
            print("Trace Num: ", len(traces))

            existing_result["response"]["response"] = output
            total_traces_dic[
                json_file_name.replace("initial_inference", "self_reflection")
            ] = existing_result

    for json_file_name in total_traces_dic:
        with open(json_file_name, "w") as file:
            json.dump(total_traces_dic[json_file_name], file, indent=4)


# Baseline 2
def start_self_verification_run(
    java_file,
    code_in_support_files,
    online_model_name,
    key,
    spec_file_name,
    is_measure_token_cost,
    step_by_step_verification,
    global_self_consistency_k,
    temperature,
):
    model = LLM(online_model_name, key, temperature)
    case_name = java_file[java_file.rfind("/") + 1 :].replace(".java", "")
    print(
        "---------------------------------------------------------------------------------------"
    )
    print("Analyzing ", case_name)
    print(
        "---------------------------------------------------------------------------------------"
    )

    input_log_dir_path = str(
        Path(__file__).resolve().parent.parent
        / ("log/initial_inference/" + online_model_name)
    )
    existing_json_file_names = set([])

    for root, dirs, files in os.walk(input_log_dir_path):
        for file in files:
            if case_name in file:
                json_file_name = root + "/" + file
                existing_json_file_names.add(json_file_name)

    with open(java_file, "r") as file:
        source_code = file.read()
        new_code = delete_comments(source_code)
        lined_new_code = add_line_numbers(new_code)

    assert len(existing_json_file_names) == 1

    for json_file_name in existing_json_file_names:
        verification_result = []

        output_json_file_name = json_file_name.replace(
            "initial_inference", "self_verification"
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
                            Path(__file__).resolve().parent / "prompt" / spec_file_name,
                            "r",
                        ) as read_file:
                            spec = json.load(read_file)

                        message = spec["task"] + "\n"
                        message += "\n".join(spec["analysis_rules"]) + "\n"
                        message += "\n".join(spec["analysis_examples"]) + "\n"

                        program = ""
                        for support_file in code_in_support_files:
                            program += (
                                "The following is the file " + support_file + ":\n"
                            )
                            program += (
                                "```\n"
                                + code_in_support_files[support_file]
                                + "\n```\n\n"
                            )
                        program += (
                            "The following is the file "
                            + json_file_name[json_file_name.rfind("/") + 1 :]
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
                        ) = model.infer(message, is_measure_token_cost)
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
