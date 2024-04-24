from openai import *
import sys
import tiktoken
from typing import Tuple
from model.utils import *
import time
import signal
from pathlib import Path
import replicate
import google.generativeai as genai


class LLM:
    """
    An online inference model using ChatGPT
    """

    def __init__(
            self, online_model_name: str, openai_key: str, temperature: float
    ) -> None:
        self.online_model_name = online_model_name
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-0125")
        self.openai_key = openai_key
        self.temperature = temperature
        self.systemRole = "You are a experienced Java programmer and good at understanding Java programs."
        return

    def infer(self, message: str, is_measure_cost: bool = False) -> Tuple[str, int, int]:
        print(self.online_model_name, "is running")
        output = ""
        if "gemini" in self.online_model_name:
            output = self.infer_with_gemini(message)
        elif "claude" in self.online_model_name:
            output = self.infer_claude(message)
        elif "gpt" in self.online_model_name:
            output = self.infer_with_openai_model(message)
        input_token_cost = 0 if not is_measure_cost else len(self.encoding.encode(self.systemRole)) + len(
            self.encoding.encode(message)
        )
        output_token_cost = 0 if not is_measure_cost else len(self.encoding.encode(output))
        return output, input_token_cost, output_token_cost

    def infer_with_gemini(self, message: str) -> str:
        def timeout_handler(signum, frame):
            raise TimeoutError("ChatCompletion timeout")

        def simulate_ctrl_c(signal, frame):
            raise KeyboardInterrupt("Simulating Ctrl+C")

        gemini_model = genai.GenerativeModel('gemini-pro')
        signal.signal(signal.SIGALRM, timeout_handler)

        received = False
        tryCnt = 0
        while not received:
            tryCnt += 1
            time.sleep(2)
            try:
                signal.alarm(50)  # Set a timeout of 50 seconds
                message = self.systemRole + "\n" + message

                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_DANGEROUS",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ]

                response = gemini_model.generate_content(message, safety_settings=safety_settings,
                                                         generation_config=genai.types.GenerationConfig(temperature=self.temperature))
                time.sleep(2)
                signal.alarm(0)  # Cancel the timeout
                output = response.text
                print("Inference succeeded...")
                return output
            except TimeoutError:
                print("ChatCompletion call timed out")
                received = False
                simulate_ctrl_c(None, None)  # Simulate Ctrl+C effect
            except KeyboardInterrupt:
                print("ChatCompletion cancelled by user")
                received = False
                continue
            except Exception:
                print("API error:", sys.exc_info())
                return ""
            if tryCnt > 5:
                return ""

    def infer_claude(self, message: str) -> str:
        start_time = time.time()

        def timeout_handler(signum, frame):
            raise TimeoutError("ChatCompletion timeout")

        def simulate_ctrl_c(signal, frame):
            raise KeyboardInterrupt("Simulating Ctrl+C")

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
                signal.alarm(60)  # Set a timeout of 20 seconds
                openai.api_key = self.openai_key
                response = openai.ChatCompletion.create(
                    model=self.online_model_name, messages=input, temperature=self.temperature
                )
                signal.alarm(0)  # Cancel the timeout
                output = response.choices[0].message.content
                print("Inference succeeded...")
                return output
            except TimeoutError:
                print("ChatCompletion call timed out")
                received = False
                simulate_ctrl_c(None, None)  # Simulate Ctrl+C effect
            except KeyboardInterrupt:
                print("ChatCompletion cancelled by user")
                return ""
            except Exception:
                print("API error:", sys.exc_info())
                received = False
            if tryCnt > 5:
                return ""

    # Temporarily deprecated
    def infer_with_openai_model(self, message):
        def timeout_handler(signum, frame):
            raise TimeoutError("ChatCompletion timeout")

        def simulate_ctrl_c(signal, frame):
            raise KeyboardInterrupt("Simulating Ctrl+C")

        model_input = [
            {
                "role": "system",
                "content": self.systemRole,
            },
            {"role": "user", "content": message},
        ]

        received = False
        tryCnt = 0
        output = ""

        signal.signal(signal.SIGALRM, timeout_handler)
        while not received:
            tryCnt += 1
            time.sleep(2)
            try:
                signal.alarm(100)  # Set a timeout of 100 seconds

                # OpenAI version: 24.0
                # Use OpenAI official APIs
                client = OpenAI(api_key=standard_keys[0])
                response = client.chat.completions.create(
                    model=self.online_model_name, messages=model_input, temperature=self.temperature
                )

                # ## OpenAI version: 0.28.0
                # openai.api_key = free_keys[0]
                # response = openai.ChatCompletion.create(
                #     model=self.online_model_name, messages=model_input, temperature=0
                # )

                signal.alarm(0)  # Cancel the timeout
                output = response.choices[0].message.content
                break
            except TimeoutError:
                print("ChatCompletion call timed out")
                received = False
                simulate_ctrl_c(None, None)  # Simulate Ctrl+C effect
            except KeyboardInterrupt:
                print("ChatCompletion cancelled by user")
                output = ""
                break
            except Exception:
                print("API error:", sys.exc_info())
                received = False
            if tryCnt > 5:
                output = ""
        return output
