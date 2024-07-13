import os
import shutil
from pipeline.valueflow import *
import argparse

from data.transform import *


class BatchRun:
    def __init__(
        self,
        spec_file: str,
        project_path: str,
        inference_model_name: str,
        inference_key_str: str,
        validation_model_name: str,
        validation_key_str: str,
        pipeline_mode: str
    ):
        self.spec_file = spec_file
        self.project_path = project_path
        self.all_c_files = {}

        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str
        self.validation_model_name = validation_model_name
        self.validation_key_str = validation_key_str

        self.batch_run_statistics = {}
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if not file.endswith(".c"):
                    continue
                with open(root + "/" + file, "r") as c_file:
                    print(root + "/" + file)
                    c_file_content = c_file.read()
                    self.all_c_files[root + "/" + file] = c_file_content
        self.pipeline_mode = pipeline_mode
        return


    def start_batch_run(
        self,
        neural_check_strategy: Dict[str, bool],
        is_measure_token_cost: bool = False
    ) -> None:
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
            Path(__file__).resolve().parent / "../../log/initial_detection/"
        )
        if not os.path.exists(inference_log_dir_path):
            os.makedirs(inference_log_dir_path)
        inference_log_dir_path = str(
            Path(__file__).resolve().parent
            / "../../log/initial_detection"
            / self.inference_model_name
        )
        if not os.path.exists(inference_log_dir_path):
            os.makedirs(inference_log_dir_path)

        project_name = self.project_path.split("/")[-1]
        pipeline = ValueFlowPipeline(
            project_name,
            self.all_c_files,
            self.inference_model_name,
            self.inference_key_str,
            self.validation_model_name,
            self.validation_key_str,
            self.spec_file,
            self.pipeline_mode
        )
        pipeline.start_detection()
        pipeline.finalize_traces()
        # pipeline.start_sanitization(neural_check_strategy)
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

    models = [
        "gpt-3.5-turbo-0125",
        "gpt-4-turbo-preview",
        "gemini",
        "claude-3-haiku-20240307",
        "claude-3-sonnet-20240229",
        "claude-3-opus-20240229",
    ]

    # Parse command-line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--project-path",
        type=str,
        help="Specify the project path",
    )
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
        "--pipeline-mode",
        choices=["llmhalspot", "baseline"],
        help="Specify the pipeline: llmhalspot or baseline",
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

    project_path = args.project_path
    spec = specs[bug_type_id]
    inference_model = args.inference_model
    validation_model = args.validation_model
    pipeline_mode = args.pipeline_mode

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
        project_path,
        inference_model,
        inference_model_key,
        validation_model,
        validation_model_key,
        pipeline_mode
    )

    # LLMHalSpot should be run before Baselines
    batch_run.start_batch_run(
        neural_check_strategy,
        is_measure_token_cost
    )
    return


if __name__ == "__main__":
    run_dev_mode()
