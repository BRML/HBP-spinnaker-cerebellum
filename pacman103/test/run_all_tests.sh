#!/bin/sh

# Run all test_*.py files in the test directory
python -m unittest discover --start-directory="$(dirname "$0")"
