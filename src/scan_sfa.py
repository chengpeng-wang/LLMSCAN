import os
import shutil
from pipeline.sfa import *
import argparse

from data.transform import *


class BatchRun:
    def __init__(
        self,
        project_path: str,
        inference_model_name: str,
        inference_key_str: str
    ):
        self.project_path = project_path
        self.all_c_files = {}

        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str

        self.batch_run_statistics = {}
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if not file.endswith(".c"):
                    continue
                with open(root + "/" + file, "r") as c_file:
                    print(root + "/" + file)
                    c_file_content = c_file.read()
                    self.all_c_files[root + "/" + file] = c_file_content
        return
    

    def start_batch_run(self) -> None:
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
        pipeline = SFAPipeline(
            project_name,
            self.all_c_files,
            self.inference_model_name,
            self.inference_key_str
        )
        # pipeline.start_detection()
        return


def run_dev_mode():
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
        "--global-temperature",
        choices=["0.0", "0.5", "0.7", "1.0", "1.5", "1.7", "2.0"],
        help="Specify the temperature",
    )

    args = parser.parse_args()

    project_path = args.project_path
    inference_model = args.inference_model
    global_temperature = float(args.global_temperature)

    if "gpt" in inference_model:
        inference_model_key = standard_keys[0]
    else:
        inference_model_key = free_keys[0]

    batch_run = BatchRun(
        project_path,
        inference_model,
        inference_model_key
    )

    # LLMHalSpot should be run before Baselines
    batch_run.start_batch_run()
    return


if __name__ == "__main__":
    run_dev_mode()
