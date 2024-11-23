#!/bin/bash
source_bashrc() {
  if [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
  fi
}

source_bashrc

python3 scan.py \
  --project-path ../benchmark/Python \
  --language Python \
  --inference-model gpt-3.5-turbo-0125 \
  --global-temperature 0.0 \
  --scanners metascan
  