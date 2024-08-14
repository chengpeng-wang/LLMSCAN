import os
import openai
import google.generativeai as genai

# Standard API
standard_keys = os.environ.get("OPENAI_API_KEY").split(":")

# Gemini key
os.environ["REPLICATE_API_TOKEN"] = os.environ.get("REPLICATE_API_TOKEN")
genai.configure(api_key=os.environ.get("GEMINI_KEY"))

iterative_count_bound = 3

# For dev options
scope_count_bound = 10
