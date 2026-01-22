#!/usr/bin/env bash

if [[ "$1" != "--data-dir" || -z "$2" ]]; then
  echo "Error: missing required argument --data-dir"
  echo "Usage: $0 --data-dir <path>"
  exit 1
fi

DATA_DIR="$2"

tail -c 31 "$DATA_DIR"
