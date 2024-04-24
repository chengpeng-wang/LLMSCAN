from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from utility.logger import Logger
from typing import Tuple


class OfflineModel:
    """
    An offline inference model using Code Llama
    """

    def __init__(self, model_path: str, temperature: float) -> None:
        self.model_path = model_path
        self.temperature = temperature
        torch.cuda.empty_cache()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        torch.cuda.empty_cache()
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=torch.float16
        ).to("cuda")
        return

    def infer(self, message: str, logger: Logger) -> Tuple[str, int, int]:
        prompt = f"<s>[INST] {message.strip()} [/INST]"
        torch.cuda.empty_cache()
        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)

        torch.cuda.empty_cache()
        output = self.model.generate(
            inputs.to("cuda")["input_ids"],
            max_new_tokens=200,
            do_sample=True,
            temperature=self.temperature,
        )
        output = output[0].to("cpu")

        torch.cuda.empty_cache()
        output_str = self.tokenizer.decode(
            output[inputs.to("cuda")["input_ids"].shape[1] :], skip_special_tokens=True
        )
        logger.logging(message, output_str)
        return output_str, 0, 0
