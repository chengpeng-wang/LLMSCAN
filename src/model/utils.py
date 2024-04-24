import os
import openai
import google.generativeai as genai

# YYDS OpenAI API
openai.api_base = "https://api.ai-yyds.com/v1"
# keys = os.environ.get("OPENAI_API_KEY_FREE_NO_SYN_PARSER").split(":")
free_keys = os.environ.get("OPENAI_API_KEY_FREE").split(":")
# keys = os.environ.get("OPENAI_API_KEY_FREE_NO_FSCOT").split(":")

# Standard API
standard_keys = os.environ.get("OPENAI_API_KEY").split(":")

# Gemini key
os.environ["REPLICATE_API_TOKEN"] = "r8_cdX9L1f3rRSh3Ivi5eoZDU6Mr5lzeB21p9FQd"
llama_model_name = "meta/codellama-70b-instruct:a279116fe47a0f65701a8817188601e2fe8f4b9e04a518789655ea7b995851bf"
genai.configure(api_key="AIzaSyBW-K1XVGbbVmbyQsjjFywPChYt8nGrbNg")


# llama model
os.environ["REPLICATE_API_TOKEN"] = "r8_cdX9L1f3rRSh3Ivi5eoZDU6Mr5lzeB21p9FQd"
llama_model_name = "meta/codellama-70b-instruct:a279116fe47a0f65701a8817188601e2fe8f4b9e04a518789655ea7b995851bf"
iterative_count_bound = 3

# For checking bug reports
shift_cnt_bound = 15
DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
