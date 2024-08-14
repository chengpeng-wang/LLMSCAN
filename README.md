# LLMSCAN

LLMSCAN is a tool designed to parse and analyze source code to instantiate LLM-based program analysis. Based on Tree-sitter, it provides functionality to identify and extract functions from the source code, along with their metadata such as name, line numbers, parameters, call sites, and other program constructs. Importantly, it achieves light-weighted call graph analysis based on parsing, which enables more effective code browsing and navigation for real-world programs.

## Features

- Parse source code using Tree-sitter.
- Browse code for prompting-based static analysis.
- Easily extendable for multiple programming languages.

## Installation

1. Clone the repository:
    ```sh
    git clone git@github.com:PurCL/LLMSCAN.git
    cd LLMSCAN
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Ensure you have the Tree-sitter library and language bindings installed:
    ```sh
    cd lib
    python build.py
    ```

4. Configure the keys:
    ```sh
    export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey1:sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey2:sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey3:sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey4 >> ~/.bashrc
    ```
    We suggest including multiple keys to facilitate parallel analysis with high throughput.

    Similarly, the other two keys can be set as follows:
    ```sh
    export REPLICATE_API_TOKEN=xxxxxx >> ~/.bashrc
    export GEMINI_KEY=xxxxxx >> ~/.bashrc
    ```

## Quick Start

1. Prepare the project that you want to analyze. Here we use the Linux kernel as an example:
    ```sh
    cd benchmark
    mkdir C && cd C
    git clone git@github.com:torvalds/linux.git
    ```

2. Run the analysis to detect the misuse of `mhi_alloc_controller`:
    ```sh
    cd src
    ./run.sh
    ```

The output files are dumped in the directory `log`, including the bug reports (in `detect_result.json`) and analyzed functions (in `probe_scope.json`).

## How to Extend

### More Program Facts

You can implement your own analysis by adding more modules, such as more parsing-based primitives (in `parser/program_parser`) and prompts (in `prompt/apiscan_prompt.py` or other user-defined prompt files).

### More Bug Types

As a simple demo, we only concentrate on API misuse detection and show three misuse patterns in `prompt/apiscan_prompt.py`. In particular, we only analyze the misuse of `mhi_alloc_controller`. You can comment or delete the following code snippet in `pipeline/apiscan.py` to analyze the other two API misuses:
```python
if sensitive_function != "mhi_alloc_controller":
    continue
```

### More Programming Languages

The framework is language-agnostic. To migrate the current C/C++ analysis to other programming languages, please refer to the grammar files in the corresponding Tree-sitter libraries and refactor the code in `parser/program_parser.py`. Basically, you only need to change the node types when invoking `find_nodes_by_type`.

Here are the links to grammar files in Tree-sitter libraries targeting mainstream programming languages:

- C: https://github.com/tree-sitter/tree-sitter-c/blob/master/src/grammar.json
- C++: https://github.com/tree-sitter/tree-sitter-cpp/blob/master/src/grammar.json
- Java: https://github.com/tree-sitter/tree-sitter-java/blob/master/src/grammar.json
- Python: https://github.com/tree-sitter/tree-sitter-python/blob/master/src/grammar.json
- JavaScript: https://github.com/tree-sitter/tree-sitter-javascript/blob/master/src/grammar.json

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact

For any questions or suggestions, please contact [stephenw.wangcp@gmail.com](mailto:stephenw.wangcp@gmail.com).
