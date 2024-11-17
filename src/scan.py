import os
import argparse
from model.utils import *
from pipeline.apiscan import *
from pipeline.metascan import *

class BatchScan:
    def __init__(
        self,
        project_path: str,
        language: str,
        inference_model_name: str,
        inference_key_str: str,
        temperature: float,
        scanners: list
    ):
        """
        Initialize BatchScan object with project details.
        """
        self.project_path = project_path
        self.language = language
        self.scanners = scanners

        self.all_files = {}
        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str
        self.temperature = temperature
        self.batch_scan_statistics = {}

        suffix = ""
        if self.language == "C":
            suffix = ".c"
        elif self.language == "C++":
            suffix = ".cpp"
        elif self.language == "Java":
            suffix = ".java"
        elif self.language == "Python":
            suffix = ".py"
        
        # Load all files with the specified suffix in the project path
        self.travese_files(project_path, {suffix})

    def start_batch_scan(self) -> None:
        """
        Start the batch scan process.
        """
        project_name = self.project_path.split("/")[-2] + "_" + self.project_path.split("/")[-1]

        if "apiscan" in self.scanners:
            apiscan_pipeline = APIScanPipeline(
                project_name,
                self.language,
                self.all_files,
                self.inference_model_name,
                self.inference_key_str,
                self.temperature
            )
            apiscan_pipeline.start_scan()

        if "metascan" in self.scanners:
            metascan_pipeline = MetaScanPipeline(
                project_name,
                self.language,
                self.all_files,
                self.inference_model_name,
                self.inference_key_str,
                self.temperature
            )
            metascan_pipeline.start_scan()
    
    def travese_files(self, project_path: str, suffix: set) -> None:
        """
        Traverse all files in the project path.
        """
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.split(".")[-1] not in suffix:
                    continue
                with open(os.path.join(root, file), "r") as c_file:
                    c_file_content = c_file.read()
                    self.all_files[os.path.join(root, file)] = c_file_content
            for dir in dirs:
                self.travese_files(os.path.join(root, dir), suffix)


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
        "--language",
        choices=[
            "C",
            "C++",
            "Java",
            "Python"
        ],
        help="Specify the language",
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
    parser.add_argument(
        "--scanners",
        nargs='+',
        choices=["apiscan", "metascan"],
        help="Specify which scanners to invoke",
    )

    args = parser.parse_args()
    project_path = args.project_path
    language = args.language
    inference_model = args.inference_model
    global_temperature = float(args.global_temperature)
    scanners = args.scanners if args.scanners else []
    inference_model_key = standard_keys[0]

    batch_scan = BatchScan(
        project_path,
        language,
        inference_model,
        inference_model_key,
        global_temperature,
        scanners
    )
    print("Starting batch scan...")
    batch_scan.start_batch_scan()


if __name__ == "__main__":
    run_dev_mode()
