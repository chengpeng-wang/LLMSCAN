#!/bin/bash

# Set the path of the log directory relative to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../log"

source_bashrc() {
  if [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
  fi
}

source_bashrc

#bug type: apt, ci, npd, xss, dbz
#model: gpt-3.5-turbo-0125, gpt-4-turbo-preview, gemini, claude-3-haiku-20240307

python3 run_main.py \
  --bug-type=dbz \
  --inference-model=gpt-3.5-turbo-0125 \
  --validation-model=gpt-3.5-turbo-0125 \
  --analysis-mode=eager \
  --project-mode=single \
  --pipeline-mode=llmhalspot \
  -intra-dataflow-check \
  -function-check \
  --global-temperature=0.0 \
  --self-consistency-k=1

#python3 run_main.py \
#  --bug-type=apt \
#  --inference-model=gpt-3.5-turbo-0125 \
#  --validation-model=gpt-3.5-turbo-0125 \
#  --analysis-mode=lazy \
#  --project-mode=partial \
#  --engine=llmhalspot \
#  -intra-dataflow-check \
#  -function-check 2>&1 | tee ../log/console/console_gpt-3.5-turbo-0125_partial_CWE36_Absolute_Path_Traversal__console_readLine.txt
#
#python3 run_main.py \
#  --bug-type=ci \
#  --inference-model=gpt-3.5-turbo-0125 \
#  --validation-model=gpt-3.5-turbo-0125 \
#  --analysis-mode=lazy \
#  --project-mode=partial \
#  --engine=llmhalspot \
#  -intra-dataflow-check \
#  -function-check 2>&1 | tee ../log/console/console_gpt-3.5-turbo-0125_partial_CWE78_OS_Command_Injection__database.txt
#
#python3 run_main.py \
#  --bug-type=npd \
#  --inference-model=gpt-3.5-turbo-0125 \
#  --validation-model=gpt-3.5-turbo-0125 \
#  --analysis-mode=lazy \
#  --project-mode=partial \
#  --engine=llmhalspot \
#  -intra-dataflow-check \
#  -function-check 2>&1 | tee ../log/console/console_gpt-3.5-turbo-0125_partial_CWE476_NULL_Pointer_Dereference__binary_if.txt
#
#python3 run_main.py \
#  --bug-type=xss \
#  --inference-model=gpt-3.5-turbo-0125 \
#  --validation-model=gpt-3.5-turbo-0125 \
#  --analysis-mode=lazy \
#  --project-mode=partial \
#  --engine=llmhalspot \
#  -intra-dataflow-check \
#  -function-check 2>&1 | tee ../log/console/console_gpt-3.5-turbo-0125_partial_CWE80_XSS__CWE182_Servlet_connect_tcp.txt
#
#python3 run_main.py \
#  --bug-type=dbz \
#  --inference-model=gpt-3.5-turbo-0125 \
#  --validation-model=gpt-3.5-turbo-0125 \
#  --analysis-mode=lazy \
#  --project-mode=partial \
#  --engine=llmhalspot \
#  -intra-dataflow-check \
#  -function-check 2>&1 | tee ../log/console/console_gpt-3.5-turbo-0125_partial_CWE369_Divide_by_Zero__float_connect_tcp_divide.txt