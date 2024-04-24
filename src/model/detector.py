import json
import openai
import time
import signal
import os
import tiktoken
import sys
from pathlib import Path
from model.llm import *
from typing import Dict
from model.utils import *


class Detector:
    def __init__(self, online_model_name: str, key, spec_file_name: str):
        self.online_model_name = online_model_name
        self.key = key
        self.model = LLM(self.online_model_name, self.key, 0)
        self.spec_file_name = spec_file_name

    def start_run_model(
        self,
        file_name: str,
        json_file_name: str,
        log_file_path: str,
        original_code: str,
        analyzed_code: str,
        code_in_support_files: Dict[str, str],
        is_reflection: bool = False,
        is_measure_token_cost: bool = False,
        previous_report: str = "",
    ):
        with open(
            Path(__file__).resolve().parent.parent / "prompt" / self.spec_file_name,
            "r",
        ) as read_file:
            spec = json.load(read_file)
        message = spec["task"] + "\n"
        message += "\n".join(spec["analysis_rules"]) + "\n"
        message += "\n".join(spec["output_constraints"]) + "\n"
        message += "\n".join(spec["analysis_examples"]) + "\n"

        program = ""
        for support_file in code_in_support_files:
            program += "The following is the file " + support_file + ":\n"
            program += "```\n" + code_in_support_files[support_file] + "\n```\n\n"
        program += (
            "The following is the file " + file_name[file_name.rfind("/") + 1 :] + ":\n"
        )
        program += "```\n" + analyzed_code + "\n```\n\n"

        if not is_reflection:
            message += "\n".join(spec["meta_prompts_without_reflection"]) + "\n"
            message = message.replace("<PROGRAM>", program)
            message = message.replace("<RE_EMPHASIZE_RULE>", "\n".join(spec["re_emphasize_rules"]))
        else:
            message += "\n".join(spec["meta_prompts_with_reflection"]) + "\n"
            message = message.replace("<PROGRAM>", program).replace(
                "<PREVIOUS_REPORT>", previous_report
            )
            message = message.replace("<RE_EMPHASIZE_RULE>", "\n".join(spec["re_emphasize_rules"]))

        response, input_token_cost, output_token_cost = self.model.infer(message, is_measure_token_cost)

        debug_print("------------------------------")
        debug_print(message)
        debug_print("------------------------------")
        debug_print(response)
        debug_print("------------------------------")
        debug_print(file_name)
        debug_print("------------------------------")
        output_results = {
            "original code": original_code,
            "analyzed code": analyzed_code,
            "response": response,
            "all program size": len(program.split("\n")),
            "input_token_cost": input_token_cost,
            "output_token_cost": output_token_cost
        }

        with open(log_file_path + "/" + json_file_name + ".json", "w") as file:
            json.dump({"response": output_results}, file, indent=4)
        return response
