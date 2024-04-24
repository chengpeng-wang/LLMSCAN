import os
import shutil
from pathlib import Path


class Logger:
    """
    Dump the response of LLMs
    """

    phase_id = 0

    def __init__(self, proj_path: str, method_id: int, logger_id: int) -> None:
        self.method_id = method_id
        self.logger_id = logger_id
        self.proj_path = proj_path
        cwd = Path(__file__).resolve().parent
        self.log_dir_path = str(
            cwd / "../../../log/bug" / self.proj_path.split("/")[-1]
        )
        if not os.path.exists(self.log_dir_path):
            os.makedirs(self.log_dir_path)
        self.log_file_path = (
            self.log_dir_path
            + "/"
            + "log_"
            + str(self.logger_id)
            + "_"
            + str(self.method_id)
            + ".txt"
        )
        self.count = 0
        return

    def set_inference_id(self, inference_id: int) -> None:
        self.inference_id = inference_id

    def logging(self, prompt: str, response: str):
        with open(self.log_file_path, "a") as file:
            self.count += 1
            Logger.phase_id += 1
            file.write("------------------------------------------\n")
            file.write("Program Phase " + str(Logger.phase_id) + "\n")
            file.write("------------------------------------------\n")
            file.write("Function Round " + str(self.count) + "\n")
            file.write("------------------------------------------\n")
            file.write("Prompt:\n")
            file.write("------------------------------------------\n")
            file.write(prompt)
            file.write("\n------------------------------------------\n")
            file.write("Response:\n")
            file.write("------------------------------------------\n")
            file.write(response)
            file.write("\n------------------------------------------\n\n")
