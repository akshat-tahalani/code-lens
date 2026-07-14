"""
scratch/test_phase3.py

Run this directly to verify Phase 3 pattern detectors.
Usage (from backend/, with venv active):
    python scratch/test_phase3.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parser import parse_source, find_functions
from app.patterns import detect_nested_loop_same_array

print("=" * 60)
print("TEST: detect_nested_loop_same_array")
print("=" * 60)

test_cases = {
    "true_positive_same_array": (
        "def has_dup(arr):\n"
        "    for i in arr:\n"
        "        for j in arr:\n"
        "            if i != j and i == j:\n"
        "                return True\n"
        "    return False"
    ),
    "false_positive_check_different_arrays": (
        "def merge_check(rows, cols):\n"
        "    for r in rows:\n"
        "        for c in cols:\n"
        "            print(r, c)"
    ),
    "false_positive_check_no_nesting": (
        "def total(arr):\n"
        "    s = 0\n"
        "    for x in arr:\n"
        "        s += x\n"
        "    return s"
    ),
}

for label, code in test_cases.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_nested_loop_same_array(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:40s} -> {fired}  {matches}")

print()
print("Expected: true_positive fires, both false_positive cases stay silent.")