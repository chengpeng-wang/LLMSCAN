import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
from LMAgent.LM_agent import LMAgent
from config.config import *
from utility.online_model import *
from utility.offline_model import *
from utility.function import *
from utility.environment import *
from utility.logger import *
from TSAgent.TS_synbot import *


class SrcExtractor(LMAgent):
    """
    SrcExtractor class for identifying the source values in the SSI function
    """

    def __init__(
        self,
        src_prompt_config_path: str,
        online_model_name: str,
        offline_model: OfflineModel,
        is_online: bool,
        openai_key: str,
    ) -> None:
        super().__init__()
        self.src_prompt_config_file_path: str = src_prompt_config_path
        system_role, prompt = self.construct_general_prompt(
            self.src_prompt_config_file_path, False
        )
        self.openai_key = openai_key
        if is_online:
            self.model = OnlineModel(
                online_model_name, system_role, self.openai_key, 0.1
            )
        else:
            self.model = offline_model
        self.prompt: str = prompt
        self.srcs: List[LocalValue] = []

        assert (
            "dbz" in self.src_prompt_config_file_path
            or "xss" in self.src_prompt_config_file_path
        )
        if "dbz" in self.src_prompt_config_file_path:
            self.src_identifier = find_dbz_src
        else:
            self.src_identifier = find_xss_src

    def apply(self, function: Function, logger: Logger, is_parse=False) -> None:
        """
        :param function: Function object
        :param logger: Logger object
        :param is_parse: Whether invoke parser instead of apply the LLM
        """
        message = (
            self.prompt
            + "\n```\n"
            + function.lined_SSI_function_without_comments
            + "\n```\n"
        )
        if not is_parse:
            response, input_token_cost, output_token_cost = self.model.infer(
                message, logger
            )
            self.srcs = LMAgent.process_response_item_lines(response, ValueType.SRC)
        else:
            # TODO: we need to synthesize the parser automatically
            # Consider DBZ only.
            self.srcs = self.src_identifier(
                function.SSI_function_without_comments, function.parse_tree.root_node
            )
            tokenized_srcs = []
            for src in self.srcs:
                tokenized_srcs.append(str(src))
            logger.logging(
                "program:\n" + function.lined_SSI_function_without_comments,
                "parser results: " + str(tokenized_srcs),
            )
        return
