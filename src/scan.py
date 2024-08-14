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
        """
        Initialize BatchScan object with project details.
        """
        self.project_path = project_path
        self.all_c_files = {}
        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str
        self.temperature = temperature
        self.batch_scan_statistics = {}

        # Load all .c files in the project path
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if not file.endswith(".c"):
                    continue
                with open(os.path.join(root, file), "r") as c_file:
                    print(os.path.join(root, file))
                    c_file_content = c_file.read()
                    self.all_c_files[os.path.join(root, file)] = c_file_content

    def start_batch_scan(self) -> None:
        """
        Start the batch scan process.
        """
        project_name = self.project_path.split("/")[-1]
        pipeline = APIScanPipeline(
            project_name,
            self.all_c_files,
            self.inference_model_name,
            self.inference_key_str,
            self.temperature
        )
        pipeline.start_detection()

def run_dev_mode():
    """
    Run in development mode by parsing arguments and starting the batch scan.
    """
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
    inference_model_key = standard_keys[0]

    batch_scan = BatchScan(
        project_path,
        inference_model,
        inference_model_key,
        global_temperature
    )
    batch_scan.start_batch_scan()

if __name__ == "__main__":
    run_dev_mode()
