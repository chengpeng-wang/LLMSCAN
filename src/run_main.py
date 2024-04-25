import shutil
from pipeline import *
import argparse

from data.transform import *


class BatchRun:
    def __init__(
        self,
        spec_file: str,
        project_name: str,
        inference_model_name: str,
        inference_key_str: str,
        validation_model_name: str,
        validation_key_str: str,
        analysis_mode: str,
    ):
        self.spec_file = spec_file
        self.project_name = project_name
        self.simplified_project_name = self.project_name + "_simplified"
        self.all_c_files = []
        self.all_single_files = []

        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str
        self.validation_model_name = validation_model_name
        self.validation_key_str = validation_key_str

        self.batch_run_statistics = {}
        self.code_in_support_files = {}
        cwd = Path(__file__).resolve().parent.parent.absolute()
        support_dir = str(
            cwd / "benchmark/C/" / self.simplified_project_name / "testcasesupport"
        )
        for root, dirs, files in os.walk(support_dir):
            for file in files:
                with open(root + "/" + file, "r") as support_file:
                    code_in_support_file = support_file.read()
                    self.code_in_support_files[file] = delete_comments(
                        code_in_support_file
                    )
        self.analysis_mode = analysis_mode
        return

    def batch_transform_projects(self) -> None:
        cwd = Path(__file__).resolve().parent.parent.absolute()
        full_project_name = cwd / "benchmark/C/" / self.project_name
        new_full_project_name = cwd / "benchmark/C/" / self.simplified_project_name

        if os.path.exists(new_full_project_name):
            shutil.rmtree(new_full_project_name)
        shutil.copytree(full_project_name, new_full_project_name)

        cluster_list = []
        history = set([])
        for root, dirs, files in os.walk(new_full_project_name):
            for file in files:
                if file.endswith(".c") and file.startswith("CWE"):
                    if not re.search(r"_\d+[a-z]$", file.replace(".c", "")):
                        continue
                    file_path = os.path.join(root, file)
                    match_str = file.replace(".c", "")[0:-1]
                    if file_path in history:
                        continue
                    cluster = []
                    cluster.append(file_path)
                    history.add(file_path)

                    for root2, dirs2, files2 in os.walk(new_full_project_name):
                        for file2 in files2:
                            if file2 in history or "_base.c" in file2:
                                continue
                            full_path2 = os.path.join(root2, file2)
                            if file2.startswith(match_str) and (
                                full_path2 not in history
                            ):
                                cluster.append(full_path2)
                                history.add(full_path2)
                    cluster_list.append(cluster)
        for file_cluster in cluster_list:
            is_class_split = True
            for file_path in file_cluster:
                trim_file_path = file_path.replace(".c", "")
                if not re.search(r"_\d+[a-z]$", trim_file_path):
                    is_class_split = False
            if is_class_split:
                transform_class_split_cluster_files(file_cluster)
            else:
                transform_function_split_cluster_files(file_cluster)

        for root, dirs, files in os.walk(new_full_project_name):
            for file in files:
                if file.endswith(".c") and file.startswith("CWE"):
                    if re.search(r"_\d+$", file.replace(".c", "")):
                        self.all_c_files.append(os.path.join(root, file))

        for full_c_file_path in self.all_c_files:
            if re.search(r"_\d+$", full_c_file_path.replace(".c", "")):
                self.all_single_files.append(full_c_file_path)
        return

    def start_batch_run_llm_hal_spot(
        self,
        main_test_file,
        main_test_track: str,
        project_mode: str,
        neural_check_strategy: Dict[str, bool],
        is_measure_token_cost: bool = False,
    ) -> None:
        self.batch_transform_projects()
        total_false_cnt_dict = {
            "syntactic_check": 0,
            "function_check": 0,
            "call_graph_check": 0,
            "escape_check": 0,
            "control_flow_check": 0,
            "intra_data_flow_check": 0,
            "total": 0,
            "final": 0,
        }

        total_cnt = 0
        inference_log_dir_path = str(
            Path(__file__).resolve().parent / "../../log/initial_inference/"
        )
        if not os.path.exists(inference_log_dir_path):
            os.makedirs(inference_log_dir_path)
        inference_log_dir_path = str(
            Path(__file__).resolve().parent
            / "../../log/initial_inference"
            / self.inference_model_name
        )
        if not os.path.exists(inference_log_dir_path):
            os.makedirs(inference_log_dir_path)

        for c_file in self.all_single_files:
            if project_mode == "single":
                if main_test_file not in c_file:
                    continue
            elif project_mode == "partial":
                if main_test_track not in c_file:
                    continue

            print(c_file)
            total_cnt += 1
            print("Analyze ID: ", total_cnt)

            false_cnt_dict = start_llm_hal_spot_run(
                c_file,
                self.code_in_support_files,
                self.inference_model_name,
                self.inference_key_str,
                self.validation_model_name,
                self.validation_key_str,
                self.spec_file,
                self.analysis_mode,
                neural_check_strategy,
                is_measure_token_cost,
            )
            # total_false_cnt_dict = {key: total_false_cnt_dict[key] + false_cnt_dict[key] for key in false_cnt_dict}

        # print(total_false_cnt_dict)
        return

    def start_batch_baselines(
        self,
        main_test_file,
        main_test_track,
        project_mode: str,
        is_measure_token_cost: bool = False,
        step_by_step_verification: bool = False,
        global_self_consistency_k=1,
        temperature=0.0,
    ) -> None:
        self.batch_transform_projects()

        total_cnt = 0
        for c_file in self.all_single_files:
            if project_mode == "single":
                if main_test_file not in c_file:
                    continue
            elif project_mode == "partial":
                if main_test_track not in c_file:
                    continue

            total_cnt += 1
            print("Analyze ID: ", total_cnt)

            # # Run self-reflection
            # start_self_reflection_run(
            #     c_file,
            #     self.code_in_support_files,
            #     self.validation_model_name,
            #     self.validation_key_str,
            #     self.spec_file
            # )

            # Run self-verification
            start_self_verification_run(
                c_file,
                self.code_in_support_files,
                self.validation_model_name,
                self.validation_key_str,
                self.spec_file,
                is_measure_token_cost,
                step_by_step_verification,
                global_self_consistency_k,
                temperature,
            )
        return


def run_dev_mode():
    bug_types = [
        "juliet-test-suite-DBZ",
        "juliet-test-suite-NPD",
        "juliet-test-suite-XSS",
        "juliet-test-suite-CI",
        "juliet-test-suite-APT",
    ]
    specs = ["dbz.json", "npd.json", "xss.json", "ci.json", "apt.json"]
    main_test_files = [
        "CWE369_Divide_by_Zero__float_connect_socket_02",
        "CWE476_NULL_Pointer_Dereference__StringBuilder_07",
        "CWE80_XSS__Servlet_URLConnection_75",
        "CWE78_OS_Command_Injection__connect_tcp_06",
        "CWE36_Absolute_Path_Traversal__connect_tcp_14",
    ]
    main_test_tracks = [
        "CWE369_Divide_by_Zero__float_connect_socket",
        "CWE476_NULL_Pointer_Dereference__StringBuilder",
        "CWE80_XSS__Servlet_URLConnection",
        "CWE78_OS_Command_Injection__connect_tcp",
        "CWE36_Absolute_Path_Traversal__connect_tcp",
    ]

    models = [
        "gpt-3.5-turbo-0125",
        "gpt-4-turbo-preview",
        "gemini",
        "claude-3-haiku-20240307",
        "claude-3-sonnet-20240229",
        "claude-3-opus-20240229",
    ]

    modes = ["lazy", "eager"]

    # Parse command-line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bug-type",
        choices=["xss", "dbz", "npd", "ci", "apt"],
        help="Specify the bug type",
    )
    parser.add_argument(
        "--inference-model",
        choices=[
            "gpt-3.5-turbo-0125",
            "gpt-4-turbo-preview",
            "claude-3-opus-20240229",
            "gemini",
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
        ],
        help="Specify LLM model for Inference",
    )
    parser.add_argument(
        "--validation-model",
        choices=[
            "gpt-3.5-turbo-0125",
            "gpt-4-turbo-preview",
            "claude-3-opus-20240229",
            "gemini",
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
        ],
        help="Specify LLM model for Validation",
    )

    parser.add_argument(
        "--analysis-mode",
        choices=["lazy", "eager"],
        help="Specify analysis mode: lazy (load original reports) or eager (re-analyze)",
    )
    parser.add_argument(
        "--project-mode",
        choices=["single", "partial", "all"],
        help="Specify the project mode: a single file, a single track, and all files",
    )
    parser.add_argument(
        "--engine",
        choices=["llmhalspot", "baseline"],
        help="Specify the analyzer: llmhalspot or baseline",
    )

    parser.add_argument(
        "-function-check", action="store_true", help="Enable function check"
    )
    parser.add_argument(
        "-escape-check", action="store_true", help="Enable escape check"
    )
    parser.add_argument(
        "-intra-dataflow-check", action="store_true", help="Enable intra dataflow check"
    )

    parser.add_argument(
        "-measure-token-cost", action="store_true", help="Measure token cost"
    )
    parser.add_argument(
        "--global-temperature",
        choices=["0.0", "0.5", "0.7", "1.0", "1.5", "1.7", "2.0"],
        help="Specify the temperature",
    )

    parser.add_argument(
        "-step-by-step-verification",
        action="store_true",
        help="Enable the step-by-step verification",
    )
    parser.add_argument(
        "--self-consistency-k",
        choices=["1", "3", "5", "7", "9", "11", "13", "15", "17", "19"],
        help="Specify the temperature",
    )

    args = parser.parse_args()

    bug_type_id = -1
    if args.bug_type == "dbz":
        bug_type_id = 0
    elif args.bug_type == "npd":
        bug_type_id = 1
    elif args.bug_type == "xss":
        bug_type_id = 2
    elif args.bug_type == "ci":
        bug_type_id = 3
    elif args.bug_type == "apt":
        bug_type_id = 4

    bug_type = bug_types[bug_type_id]
    project_name = bug_types[bug_type_id]
    main_test_file = main_test_files[bug_type_id]
    main_test_track = main_test_tracks[bug_type_id]

    spec = specs[bug_type_id]
    inference_model = args.inference_model
    validation_model = args.validation_model
    analysis_mode = args.analysis_mode
    project_mode = args.project_mode

    is_measure_token_cost = args.measure_token_cost
    step_by_step_verification = args.step_by_step_verification

    global_temperature = float(args.global_temperature)
    global_self_consistency_k = int(args.self_consistency_k)

    neural_check_strategy = {
        "function_check": args.function_check,
        "escape_check": args.escape_check,
        "intra_dataflow_check": args.intra_dataflow_check,
    }

    if "gpt" in inference_model:
        inference_model_key = standard_keys[0]
    else:
        inference_model_key = free_keys[0]

    if "gpt" in validation_model:
        validation_model_key = standard_keys[0]
    else:
        validation_model_key = free_keys[0]

    batch_run = BatchRun(
        spec,
        project_name,
        inference_model,
        inference_model_key,
        validation_model,
        validation_model_key,
        analysis_mode,
    )

    # LLMHalSpot should be run before Baselines
    if args.engine == "llmhalspot":
        batch_run.start_batch_run_llm_hal_spot(
            main_test_file,
            main_test_track,
            project_mode,
            neural_check_strategy,
            is_measure_token_cost,
        )
    elif args.engine == "baseline":
        batch_run.start_batch_baselines(
            main_test_file,
            main_test_track,
            project_mode,
            is_measure_token_cost,
            step_by_step_verification,
            global_self_consistency_k,
            temperature=global_temperature,
        )


def run_release_mode():
    bug_types = [
        "juliet-test-suite-DBZ",
        "juliet-test-suite-NPD",
        "juliet-test-suite-XSS",
        "juliet-test-suite-CI",
        "juliet-test-suite-APT",
    ]

    bug_names = [
        "Divide_by_Zero",
        "NULL_Pointer_Dereference",
        "XSS",
        "OS_Command_Injection",
        "Absolute_Path_Traversal",
    ]

    specs = ["dbz.json", "npd.json", "xss.json", "ci.json", "apt.json"]

    models = [
        "gpt-3.5-turbo-0125",
        "gpt-4-turbo-preview",
        "gemini",
        "claude-3-haiku-20240307",
        "claude-3-sonnet-20240229",
        "claude-3-opus-20240229",
    ]

    modes = ["lazy", "eager"]

    # Parse command-line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bug-type",
        choices=["xss", "dbz", "npd", "ci", "apt"],
        help="Specify the bug type",
    )
    parser.add_argument(
        "--inference-model",
        choices=[
            "gpt-3.5-turbo-0125",
            "gpt-4-turbo-preview",
            "claude-3-opus-20240229",
            "gemini",
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
        ],
        help="Specify LLM model for Inference",
    )
    parser.add_argument(
        "--validation-model",
        choices=[
            "gpt-3.5-turbo-0125",
            "gpt-4-turbo-preview",
            "claude-3-opus-20240229",
            "gemini",
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
        ],
        help="Specify LLM model for Validation",
    )

    parser.add_argument(
        "--analysis-mode",
        choices=["lazy", "eager"],
        help="Specify analysis mode: lazy (load original reports) or eager (re-analyze)",
    )
    parser.add_argument(
        "--project-mode",
        choices=["single", "partial", "all"],
        help="Specify the project mode: a single file, a single track, and all files",
    )
    parser.add_argument(
        "--engine",
        choices=["llmhalspot", "baseline"],
        help="Specify the analyzer: llmhalspot or baseline",
    )

    parser.add_argument(
        "-function-check", action="store_true", help="Enable function check"
    )
    parser.add_argument(
        "-escape-check", action="store_true", help="Enable escape check"
    )
    parser.add_argument(
        "-intra-dataflow-check", action="store_true", help="Enable intra dataflow check"
    )

    parser.add_argument(
        "-measure-token-cost", action="store_true", help="Measure token cost"
    )
    parser.add_argument(
        "--global-temperature",
        choices=["0.0", "0.5", "0.7", "1.0", "1.5", "1.7", "2.0"],
        help="Specify the temperature",
    )

    parser.add_argument(
        "-step-by-step-verification",
        action="store_true",
        help="Enable the step-by-step verification",
    )
    parser.add_argument(
        "--self-consistency-k",
        choices=["1", "3", "5", "7", "9", "11", "13", "15", "17", "19"],
        help="Specify the temperature",
    )

    args = parser.parse_args()

    assert args.project_mode == "all"
    assert args.engine == "llmhalspot"

    bug_type_id = -1
    if args.bug_type == "dbz":
        bug_type_id = 0
    elif args.bug_type == "npd":
        bug_type_id = 1
    elif args.bug_type == "xss":
        bug_type_id = 2
    elif args.bug_type == "ci":
        bug_type_id = 3
    elif args.bug_type == "apt":
        bug_type_id = 4

    case_path = str(Path(__file__).resolve().parent.parent / "log/case/")
    case_json_files = [file for file in os.listdir(case_path)]

    test_cases = []
    for case_json_file in case_json_files:
        if bug_names[bug_type_id] in case_json_file:
            file_path = os.path.join(case_path, case_json_file)
            with open(file_path, "r") as json_file:
                test_cases = json.load(json_file)["cases"]

    for main_test_file in test_cases:
        spec = specs[bug_type_id]
        inference_model = args.inference_model
        validation_model = args.validation_model
        analysis_mode = args.analysis_mode
        project_mode = "single"

        bug_type = bug_types[bug_type_id]
        project_name = bug_types[bug_type_id]
        main_test_track = "all track"  # Not used
        is_measure_token_cost = args.measure_token_cost
        step_by_step_verification = args.step_by_step_verification

        global_temperature = float(args.global_temperature)
        global_self_consistency_k = int(args.self_consistency_k)

        neural_check_strategy = {
            "function_check": args.function_check,
            "escape_check": args.escape_check,
            "intra_dataflow_check": args.intra_dataflow_check,
        }

        if "gpt" in inference_model:
            inference_model_key = standard_keys[0]
        else:
            inference_model_key = free_keys[0]

        if "gpt" in validation_model:
            validation_model_key = standard_keys[0]
        else:
            validation_model_key = free_keys[0]

        batch_run = BatchRun(
            spec,
            project_name,
            inference_model,
            inference_model_key,
            validation_model,
            validation_model_key,
            analysis_mode,
        )

        batch_run.start_batch_run_llm_hal_spot(
            main_test_file,
            main_test_track,
            project_mode,
            neural_check_strategy,
            is_measure_token_cost,
        )


if __name__ == "__main__":
    run_dev_mode()
