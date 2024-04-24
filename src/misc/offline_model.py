from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

torch.cuda.empty_cache()

from time import time


def load_offline_model(model_id: str):
    torch.cuda.empty_cache()
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    torch.cuda.empty_cache()
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.float16
    ).to("cuda")
    torch.cuda.empty_cache()
    return model, tokenizer


def infer_offline_model(model, tokenizer, user_prompt: str, t: float):
    t1 = time()
    prompt = f"<s>[INST] {user_prompt.strip()} [/INST]"
    inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)

    output = model.generate(
        inputs.to("cuda")["input_ids"],
        max_new_tokens=200,
        do_sample=True,
        temperature=t,
    )
    output = output[0].to("cpu")
    output_str = tokenizer.decode(
        output[inputs.to("cuda")["input_ids"].shape[1] :], skip_special_tokens=True
    )
    t2 = time()
    print(output_str)
    print(t2 - t1)
    return output_str


if __name__ == "__main__":
    # model_id = "codellama/CodeLlama-7b-Instruct-hf"
    model_id = "/home/chengpeng/LMFlow/output_models/finetuned_CodeLlama-7b-Instruct-hf_dbz_src"
    model, tokenizer = load_offline_model(model_id)

    rules = [
        "- When two values are possibly equal, then the result of subtraction upon them can be 0\n"
        "- When a library function can return any integer, then the returned value of its function call can be 0\n"
        "- If there is a literal 0, then it is exactly 0\n"
    ]

    message = "Here is the rules that can help you identify the possible 0 values:\n"
    message += "\n".join(rules)

    message += "Now I will give you a program. "
    message += "Please identify variables of which the values can be 0 and the line numbers where they are possibly assigned with 0. \n"
    message += "Here is the program\n"

    program = [
        "1 public void foo() throws Throwable",
        "2 \{",
        "3     float data;",
        "4     data = -1.0f;",
        "5 ",
        "6     \{",
        '7         String stringNumber = System.getenv("ADD");',
        "8         if (stringNumber != null)",
        "9         \{",
        "10             try",
        "11             \{",
        "12                 data = Float.parseFloat(stringNumber.trim());",
        "13             \}",
        "14             catch (NumberFormatException exceptNumberFormat)",
        "15             \{",
        '16                 IO.logger.log(Level.WARNING, "Number format exception parsing data from string", exceptNumberFormat);',
        "17             \}",
        "18         \}",
        "19     \}",
        "20 ",
        "21     float y = data;",
        "22     int result = (int)(100.0 / y);",
        "23     IO.writeLine(result);",
        "24 \}",
    ]

    message += "\n".join(program)

    infer_offline_model(model, tokenizer, message, 0.7)
