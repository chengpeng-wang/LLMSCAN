#!/bin/bash
source_bashrc() {
  if [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
  fi
}

source_bashrc

python3 scan.py \
  --inference-model=gpt-3.5-turbo-0125 \
  --project-path=../benchmark/C/linux \
  --global-temperature=0.0
