import openai
import json
from config.config import *
from utility.offline_inference import *
from utility.online_inference import *


def extract_program_answer(output: str):
    outputs = output.split("\n")
    isBegin = False
    isEnd = False
    program_lines = []
    answer_lines = []
    for s in outputs:
        if isBegin:
            program_lines.append(s)
        if isEnd:
            answer_lines.append(s)
        if s == "```":
            if isBegin is False:
                isBegin = True
                program_lines.append(s)
            else:
                isBegin = False
                isEnd = True
    return "\n".join(program_lines), "\n".join(answer_lines)


def produce_response_data(n: int):
    user_prompts = [
        "Please generate a Java code snippet line by line such that the following requirements",
        "- Requirement 1: The code should have 4 LoC ~ 8 LoC.",
        "- Requirement 2: Each line should be labeled with a line number at the beginning.",
        "- Requirement 3: The code snippet should contain one or several statements assigning variables with the values that are potentially equal to 0.",
        "The output should contain two parts: (1) The code snippet; (2) the line numbers where the variables are assigned with 0.",
        "The output format should be : ",
        "```",
        "[CODE SNIPPET]",
        "```",
        "- Line [NUMBER], the variable [VAR NAME]",
        "- Line [NUMBER], the variable [VAR NAME]",
        "Remember: The line info of variables should be listed line by line.",
        "You answer should begin with ```. The code should be surrounded by a pair of ```.",
    ]

    samples = [
        [
            "```",
            "1 int x = 0;",
            "2 int y = 1;",
            "3 int z = 2;",
            "4",
            '5 System.out.println("x = " + x);',
            "```",
            "- Line 1: variable x",
            "",
        ],
        [
            "```",
            "1 int a = 1;",
            "2 int b = 1;",
            "3 a = 0;",
            "4",
            '5 System.out.println("a = " + a);',
            "```",
            "- Line 3: variable a",
            "",
        ],
        [
            "```",
            "1 int x = 1;",
            "2 int y = 1;",
            "3 x = 0;",
            "```",
            "- Line 3: variable x",
            "",
        ],
        [
            "```",
            "1 void foo(int z) \{",
            "2   int a = z;",
            "3   int y = 1;",
            '4   System.out.println("a = " + a);',
            "5   a = 0;",
            "6 \}",
            "```",
            "- Line 5: variable a",
            "",
        ],
        [
            "```",
            "1 int x = 0;",
            "2 int y = 1;",
            "3 x = 1;",
            "4 x = 0;",
            "```",
            "- Line 1: variable x",
            "- Line 4: variable x",
            "",
        ],
        [
            "```",
            "1 if (y > 0)",
            "2   z = 1",
            "3 else",
            "4   z = 0;",
            "```",
            "- Line 4: variable z",
            "",
        ],
        [
            "```",
            "1  void goo(int a) \{" "2  int z;",
            "3  if (a > 0)",
            "4    z = 1",
            "5  else",
            "6    z = 0;",
            "7  \}",
            "```",
            "- Line 6: variable z",
            "",
        ],
        [
            "```",
            "1  void goo(int a) \{" "2  int z = 1;",
            "3  for (int i = 0; i < a; i++)\{",
            "4    if (i % 2 == 1)",
            "5      z = 0;",
            "6   \}",
            "7  \}",
            "```",
            "- Line 5: variable z",
            "",
        ],
    ]

    user_prompt = "\n".join(user_prompts) + "\n"
    user_prompt += "Here are several samples:\n"
    for sample in samples:
        user_prompt += "Example:\n"
        user_prompt += "\n".join(sample)
        user_prompt += "\n"
    outputs = []

    # # Offline model: Bad performance. Generated data in low quality
    # model_id = "/home/chengpeng/LMFlow/output_models/finetuned_CodeLlama-7b-Instruct-hf"
    # model, tokenizer = load_offline_model(model_id)
    # for i in range(n):
    #     print("----------------------------------")
    #     print(i)
    #     print("----------------------------------")
    #     print(user_prompt)
    #     print("----------------------------------")

    #     output = infer_offline_model(model, tokenizer, user_prompt, 0.7)
    #     print(output)
    #     print("----------------------------------\n")
    #     outputs.append(output)

    # Online model: GPT3.5, good performance, data in high quality
    engine = "gpt-3.5-turbo"
    t = 0.9
    systemRole = "You are a good Java programmer."

    for i in range(n):
        print("----------------------------------")
        print(i)
        # print("----------------------------------")
        # print(user_prompt)
        # print("----------------------------------")
        openai.api_key = keys[i % len(keys)]
        recieved = False
        while not recieved:
            output = infer_online_model(
                engine, systemRole, user_prompt, openai.api_key, t
            )
            if output is None:
                continue
            recieved = True
            print(output)
            print("----------------------------------\n")
            program, answer = extract_program_answer(output)
            print("program:")
            print(program)
            print("answer:")
            print(answer)
            if (
                len(program.split("\n")) < 3
                or "Line" not in answer
                or "variable" not in answer
            ):
                recieved = False

        outputs.append({"response": output, "program": program, "answer": answer})
        with open("../data/fine_tune/dbz_src_data_02.json", "w") as f:
            json.dump({"data": outputs}, f, indent=4)
    return outputs


def prepare_fine_tune_dbz_src_data():
    rules = [
        "- When two values are possibly equal, then the result of subtraction upon them can be 0\n"
        "- When a library function can return any integer, then the returned value of its function call can be 0\n"
        "- If there is a literal 0, then it is exactly 0\n"
    ]

    message = "Here is the rules that can help you identify the possible 0 values:\n"
    message += "\n".join(rules)
    # message += "Here are several examples: \n"
    # message += "\n".join(few_shot_samples)

    message += "Now I will give you a program. "
    message += "Please identify variables of which the values can be 0 and the line numbers where they are possibly assigned with 0. \n"
    message += "Here is the program\n"

    raw_data_path = "../data/fine_tune/dbz_src_data.json"
    with open(raw_data_path, "r") as f:
        response_records = json.load(f)["data"]

    fine_tune_data = {}
    fine_tune_data["type"] = "text2text"
    fine_tune_data["instances"] = []

    for record in response_records:
        program = record["program"].rstrip("\n")
        answer = record["answer"].rstrip("\n")
        input_str = message + program
        output_str = answer
        fine_tune_data["instances"].append({"input": input_str, "output": output_str})

    with open("../data/fine_tune/dbz_src_fine_tune_data.json", "w") as f:
        json.dump(fine_tune_data, f, indent=4)
    return
