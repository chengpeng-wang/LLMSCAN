from typing import Tuple

def parse_bug_report(response: str) -> Tuple[bool, bool]:
    is_buggy = "yes" in response.strip().lower()
    is_ill_formed = "yes" not in response.strip().lower() and "no" not in response.strip().lower()
    return is_buggy, is_ill_formed

# TODO: Define the response parsers for different forms of LLM responses