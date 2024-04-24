import sys
from os import path
import json

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
from LMAgent.LM_agent import LMAgent
from config.config import *
from utility.online_model import *
from utility.offline_model import *
from utility.function import *
from utility.logger import *
from typing import List, Tuple


class IntraFlowPropagator(LMAgent):
    """
    IntraFlowPropagator class for checking whether source can flow to sink in the SSI function
    """

    def __init__(
        self, file_path, online_model_name, offline_model, is_online, openai_key
    ) -> None:
        super().__init__()
        self.ifp_file_path = file_path
        system_role = self.fetch_system_role()
        self.openai_key = openai_key
        if is_online:
            self.model = OnlineModel(
                online_model_name, system_role, self.openai_key, 0.1
            )
        else:
            self.model = offline_model
        self.prompt = self.construct_prompt_skeleton()
        self.response = ""

    def apply(
        self,
        function: Function,
        srcs: List[LocalValue],
        sinks: List[LocalValue],
        logger: Logger,
        is_reflexion: bool = False,
    ) -> Tuple[
        List[Tuple[LocalValue, LocalValue]], List[Tuple[LocalValue, LocalValue]]
    ]:
        """
        :param function: SSI function
        :param srcs: The src info
        :param sinks: The sink info
        :param logger: The logger
        :param is_reflexion: whether apply the reflexion for precision enhancement
        """
        reachable_pairs = []
        unreachable_pairs = []
        with open(self.prompt_config_file_base / self.ifp_file_path, "r") as read_file:
            dump_config_dict = json.load(read_file)
        question_template = dump_config_dict["question_template"]

        for src in srcs:
            for sink in sinks:
                # When two points are the same, then src must flow to sink
                # Handle the case where the fields are assigned with sensitive values directly
                if src.line_number == sink.line_number:
                    reachable_pairs.append((src, sink))
                    continue

                # Avoid analyzing existing reachable pairs
                is_exist_reachable = False
                for existing_start, existing_end in function.reachable_summaries:
                    if str(src) == str(existing_start) and str(sink) == str(
                        existing_end
                    ):
                        is_exist_reachable = True
                        break
                if is_exist_reachable:
                    reachable_pairs.append((src, sink))
                    continue

                # Avoid analyzing existing unreachable pairs
                is_exist_unreachable = False
                for existing_start, existing_end in function.unreachable_summaries:
                    if str(src) == str(existing_start) and str(sink) == str(
                        existing_end
                    ):
                        is_exist_unreachable = True
                        break
                if is_exist_unreachable:
                    unreachable_pairs.append((src, sink))
                    continue

                question = (
                    question_template.replace("<SRC_NAME>", src.name)
                    .replace("<SRC_LINE>", str(src.line_number))
                    .replace("<SINK_NAME>", sink.name)
                    .replace("<SINK_LINE>", str(sink.line_number))
                )

                if src.name == sink.name:
                    cmp = "the same"
                else:
                    cmp = "different"

                if sink.v_type in {ValueType.ARG, ValueType.SINK}:
                    used = "used"
                else:
                    used = ""

                question = question.replace("<CMP>", cmp)
                question = question.replace("<USED>", used)

                message = self.prompt
                message = message.replace(
                    "<PROGRAM>", function.lined_SSI_function_without_comments
                )
                message = message.replace("<QUESTION>", question)
                message = message.replace("<ANSWER>", self.fetch_answer_format())

                is_reachable = False
                while True:
                    if not is_reflexion:
                        output, input_token_cost, output_token_cost = self.model.infer(
                            message, logger
                        )
                        self.total_input_token_cost += input_token_cost
                        self.total_output_token_cost += output_token_cost
                        self.response = output
                    else:
                        (
                            first_response,
                            input_token_cost,
                            output_token_cost,
                        ) = self.model.infer(message, logger)
                        self.total_input_token_cost += input_token_cost
                        self.total_output_token_cost += output_token_cost

                        yes_no_vector_previous = self.process_yes_no_list_in_response(
                            first_response
                        )
                        previous_answer = yes_no_vector_previous[0].lower()

                        reflexion_cnt = 0

                        while True:
                            reflexion_cnt += 1
                            if reflexion_cnt > 5:
                                break
                            message_reflexion = message
                            message_reflexion += (
                                "This is your previous answer with explanation:\n"
                            )
                            message_reflexion += "```\n" + first_response + "\n```\n"
                            message_reflexion += "Critique your previous answer and answer the question again."

                            (
                                response,
                                input_token_cost,
                                output_token_cost,
                            ) = self.model.infer(message_reflexion, logger)
                            self.total_input_token_cost += input_token_cost
                            self.total_output_token_cost += output_token_cost
                            self.response = response

                            yes_no_vector = self.process_yes_no_list_in_response(
                                response
                            )
                            answer = yes_no_vector[0].lower()
                            if answer == previous_answer:
                                break
                            previous_answer = answer
                            first_response = response

                    yes_no_vector = LMAgent.process_yes_no_list_in_response(
                        self.response
                    )
                    if len(yes_no_vector) == 0:
                        continue
                    if yes_no_vector[0] == "Yes":
                        is_reachable = True
                    break

                if is_reachable:
                    reachable_pairs.append((src, sink))
                else:
                    unreachable_pairs.append((src, sink))
        return reachable_pairs, unreachable_pairs

    def construct_prompt_skeleton(self) -> str:
        """
        Construct the prompt according to prompt config file
        :return: The prompt
        """
        with open(self.prompt_config_file_base / self.ifp_file_path, "r") as read_file:
            dump_config_dict = json.load(read_file)
        prompt = dump_config_dict["task"]
        # prompt += "\n" + "\n".join(dump_config_dict["analysis_rules"])
        # prompt += "\n" + "\n".join(dump_config_dict["analysis_examples"])
        prompt += "\n" + "".join(dump_config_dict["meta_prompts"])
        return prompt

    def fetch_system_role(self):
        with open(self.prompt_config_file_base / self.ifp_file_path, "r") as read_file:
            dump_config_dict = json.load(read_file)
        role = dump_config_dict["system_role"]
        return role

    def fetch_answer_format(self) -> str:
        with open(self.prompt_config_file_base / self.ifp_file_path, "r") as read_file:
            dump_config_dict = json.load(read_file)
        answer_format = dump_config_dict["answer_format"]
        return "\n".join(answer_format)
