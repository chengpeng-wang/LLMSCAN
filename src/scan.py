import os
import argparse
from model.utils import *
from pipeline.apiscan import *


class BatchScan:
    def __init__(
        self,
        project_path: str,
        inference_model_name: str,
        inference_key_str: str,
        temperature: float
    ):
        self.project_path = project_path
        self.all_c_files = {}

        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str
        self.temperature = temperature

        self.batch_scan_statistics = {}
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if not file.endswith(".c"):
                    continue
                with open(root + "/" + file, "r") as c_file:
                    print(root + "/" + file)
                    c_file_content = c_file.read()
                    self.all_c_files[root + "/" + file] = c_file_content
        return


    def start_batch_scan(self) -> None:
        project_name = self.project_path.split("/")[-1]
        pipeline = APIScanPipeline(
            project_name,
            self.all_c_files,
            self.inference_model_name,
            self.inference_key_str,
            self.temperature
        )
        pipeline.start_detection()
        return


def run_dev_mode():
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
            "gemini"
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

    batch_scan = BatchScan(
        project_path,
        inference_model,
        inference_model_key,
        global_temperature
    )

    # LLMHalSpot should be run before Baselines
    batch_scan.start_batch_scan()
    return


if __name__ == "__main__":
    run_dev_mode()
