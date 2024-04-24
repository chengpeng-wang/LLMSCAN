from openai import OpenAI
import sys
import tiktoken
from utility.logger import Logger
from typing import Tuple
from config.config import *
import time
import signal


class OnlineModel:
    """
    An online inference model using ChatGPT
    """

    def __init__(
        self, engine: str, systemRole: str, openai_key: str, temperature: float
    ) -> None:
        self.engine = engine
        self.systemRole = systemRole
        self.openai_key = openai_key
        self.temperature = temperature
        self.encoding = tiktoken.encoding_for_model(engine)
        return

    def infer(self, message: str, logger: Logger) -> Tuple[str, int, int]:
        print("OpenAI ChatGPT invoked...")

        def timeout_handler(signum, frame):
            raise TimeoutError("ChatCompletion timeout")

        def simulate_ctrl_c(signal, frame):
            raise KeyboardInterrupt("Simulating Ctrl+C")

        input_token_cost = 0
        output_token_cost = 0
        input = [
            {"role": "system", "content": self.systemRole},
            {"role": "user", "content": message},
        ]
        signal.signal(signal.SIGALRM, timeout_handler)

        received = False
        tryCnt = 0
        while not received:
            tryCnt += 1
            time.sleep(2)
            try:
                signal.alarm(20)  # Set a timeout of 20 seconds
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model=self.engine, messages=input, temperature=self.temperature
                )
                signal.alarm(0)  # Cancel the timeout
                output = response.choices[0].message.content
                input_token_cost += len(self.encoding.encode(self.systemRole)) + len(
                    self.encoding.encode(message)
                )
                output_token_cost += len(self.encoding.encode(output))
                logger.logging(message, output)
                print("Inference succeeded...")
                return output, input_token_cost, output_token_cost
            except TimeoutError:
                print("ChatCompletion call timed out")
                received = False
                simulate_ctrl_c(None, None)  # Simulate Ctrl+C effect
            except KeyboardInterrupt:
                print("ChatCompletion cancelled by user")
                return "", input_token_cost, output_token_cost
            except Exception:
                print("API error:", sys.exc_info())
                received = False
            if tryCnt > 5:
                logger.logging(message, "")
                return "", input_token_cost, output_token_cost
