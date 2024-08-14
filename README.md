# LLMSCAN

LLMSCAN is a tool designed to parse and analyze source code to instantiate LLM-based program analysis. Based on Tree-sitter, it provides functionality to identify and extract functions from the source code, along with their metadata such as name, line numbers, parameters, call sites, and other program constructs.

## Features

- Parse source code using Tree-sitter.
- Extract functions and their metadata.
- Easy to be extended for multiple programming languages.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/LLMSCAN.git
    cd LLMSCAN
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Configure the keys
    ```sh
    export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey1:sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey2:sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey3:sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxkey4 > ~/.bashrc
    ```
    Here, we suggest including multiple keys, which can facilitate the parallel analysis with high throughput.

    Similarly, the other two keys can be set as follows:

    ```sh
    export REPLICATE_API_TOKEN=xxxxxx > ~/.bashrc
    export GEMINI_KEY=xxxxxx > ~/.bashrc
    ```

## Quick Start

1. Ensure you have the Tree-sitter library and language bindings installed.
    ```sh
    cd lib
    python build.py
    ```

2. Prepare the project that you want to analyze. Here we use Linux kernel as an example.

    ```sh
    cd benchmark
    mkdir C
    git clone git@github.com:torvalds/linux.git
    ```

3. Run the analysis to detect the misuse of `mhi_alloc_controller`:
    ```sh
    cd src
    cd run.sh
    ```

The output files are dumped in the directory `log`, including the bug reports (in `detect_result.json`) and analyzed functions (in `probe_scope.json`).

## How to Extend

### More Program Facts

You can implement your own analysis by adding more modules, such as more parsing-based primitives (in `parser/program_parser`) and prompts (in `prompt/apiscan_prompt.py` or other user-defined prompt files)

### More Bug Types

As a simple demo, we only concentrate on API misuse detection and show three misuse patterns in `prompt/apiscan_prompt.py`. In particular, we only analyze the misuse of `mhi_alloc_controller`. You can comment or delete the following code snippet in `pipeline/apiscan.py` to analyze other two API misues.

```python
if sensitive_function != "mhi_alloc_controller":
    continue
```

## More Programming Languages

The framework is language agonositic. To migrate the current C/C++ analysis to other programming languages, please refer the grammar files in the corresponding Tree-sitter libraries and refactor the code in `parser/program_parser.py`. Basically, you only need to change the node types when invoking `find_nodes_by_type`.

Here are the links to grammar files Tree-sitter libraries targeting mainstream programming langugages:

- C:https://github.com/tree-sitter/tree-sitter-c/blob/master/src/grammar.json

- C++: https://github.com/tree-sitter/tree-sitter-cpp/blob/master/src/grammar.json

- Java: https://github.com/tree-sitter/tree-sitter-java/blob/master/src/grammar.json

- Python: https://github.com/tree-sitter/tree-sitter-python/blob/master/src/grammar.json

- JavaScript: https://github.com/tree-sitter/tree-sitter-javascript/blob/master/src/grammar.json


## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact

For any questions or suggestions, please contact [stephenw.wangcp@gmail.com](mailto:stephenw.wangcp@gmail.com).