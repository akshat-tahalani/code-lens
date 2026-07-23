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

print()
print("=" * 60)
print("TEST: detect_linear_scan_in_loop")
print("=" * 60)

from app.patterns import detect_linear_scan_in_loop

scan_tests = {
    "true_positive_in_check": (
        "def find_common(a, b):\n"
        "    result = []\n"
        "    for x in a:\n"
        "        if x in b:\n"
        "            result.append(x)\n"
        "    return result"
    ),
    "true_positive_index_call": (
        "def find_pos(arr, targets):\n"
        "    for t in targets:\n"
        "        pos = arr.index(t)\n"
        "        print(pos)"
    ),
    "false_positive_in_used_outside_loop": (
        "def check_once(x, lst):\n"
        "    if x in lst:\n"
        "        return True\n"
        "    return False"
    ),
    "fixed_local_set_assignment": (
        "def find_common_set(a, b):\n"
        "    b_set = set(b)\n"
        "    result = []\n"
        "    for x in a:\n"
        "        if x in b_set:\n"
        "            result.append(x)\n"
        "    return result"
    ),
    "known_limitation_set_param": (
        "def find_common_set(a, b_set):\n"
        "    result = []\n"
        "    for x in a:\n"
        "        if x in b_set:\n"
        "            result.append(x)\n"
        "    return result"
    ),
}

for label, code in scan_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_linear_scan_in_loop(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:40s} -> {fired}  {matches}")


print()
print("=" * 60)
print("TEST: detect_repeated_call_in_while_condition")
print("=" * 60)

from app.patterns import detect_repeated_call_in_while_condition

while_tests = {
    "true_positive_len_in_condition": (
        "def process(arr):\n"
        "    i = 0\n"
        "    while i < len(arr):\n"
        "        print(arr[i])\n"
        "        i += 1"
    ),
    "true_positive_expensive_call": (
        "def process(node):\n"
        "    while node != get_root():\n"
        "        node = node.parent"
    ),
    "false_positive_no_call_in_condition": (
        "def countdown(n):\n"
        "    while n > 0:\n"
        "        print(n)\n"
        "        n -= 1"
    ),
    "false_positive_call_only_in_body": (
        "def process(arr, i):\n"
        "    while i > 0:\n"
        "        print(len(arr))\n"
        "        i -= 1"
    ),
}

for label, code in while_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_repeated_call_in_while_condition(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:40s} -> {fired}  {matches}")

print()
print("=" * 60)
print("TEST: detect_constant_bound_loops")
print("=" * 60)

from app.patterns import detect_constant_bound_loops

const_tests = {
    "true_positive_literal": "def f():\n    for i in range(10):\n        print(i)",
    "false_positive_len": "def f(arr):\n    for x in range(len(arr)):\n        print(x)",
    "false_positive_variable": "def f(n):\n    for i in range(n):\n        print(i)",
}

for label, code in const_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_constant_bound_loops(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:30s} -> {fired}  {matches}")


print()
print("=" * 60)
print("TEST: detect_exponential_recursion")
print("=" * 60)

from app.patterns import detect_exponential_recursion

recursion_tests = {
    "true_positive_fib": "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)",
    "false_positive_single_recursion": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "false_positive_no_recursion": "def add(a, b):\n    return a + b",
}

for label, code in recursion_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_exponential_recursion(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:35s} -> {fired}  {matches}")


print()
print("=" * 60)
print("TEST: detect_string_concat_in_loop")
print("=" * 60)

from app.patterns import detect_string_concat_in_loop

concat_tests = {
    "true_positive_string_concat": "def build(words):\n    s = ''\n    for w in words:\n        s += w\n    return s",
    "false_positive_numeric_sum": "def total(nums):\n    s = 0\n    for n in nums:\n        s += n\n    return s",
    "false_positive_list_append": "def build(words):\n    parts = []\n    for w in words:\n        parts.append(w)\n    return ''.join(parts)",
}

for label, code in concat_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_string_concat_in_loop(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:35s} -> {fired}  {matches}")


print()
print("=" * 60)
print("TEST: detect_sort_in_loop")
print("=" * 60)

from app.patterns import detect_sort_in_loop

sort_tests = {
    "true_positive_sorted_call": "def f(arr):\n    for x in arr:\n        arr = sorted(arr)\n        print(arr[0])",
    "true_positive_method_sort": "def f(arr):\n    for x in arr:\n        arr.sort()\n        print(arr[0])",
    "false_positive_sort_before_loop": "def f(arr):\n    arr = sorted(arr)\n    for x in arr:\n        print(x)",
}

for label, code in sort_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_sort_in_loop(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:30s} -> {fired}  {matches}")


print()
print("=" * 60)
print("TEST: detect_front_list_ops_in_loop")
print("=" * 60)

from app.patterns import detect_front_list_ops_in_loop

front_ops_tests = {
    "true_positive_insert_front": "def f(arr, items):\n    for x in items:\n        arr.insert(0, x)",
    "true_positive_pop_front": "def f(arr):\n    while arr:\n        x = arr.pop(0)\n        print(x)",
    "false_positive_append": "def f(arr, items):\n    for x in items:\n        arr.append(x)",
    "false_positive_pop_end": "def f(arr):\n    while arr:\n        x = arr.pop()\n        print(x)",
}

for label, code in front_ops_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_front_list_ops_in_loop(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:30s} -> {fired}  {matches}")

print()
print("=" * 60)
print("TEST: detect_loop_invariant_construction")
print("=" * 60)

from app.patterns import detect_loop_invariant_construction

invariant_tests = {
    "true_positive_rebuild_each_iter": "def f(arr, lookup_source):\n    for x in arr:\n        lookup = set(lookup_source)\n        if x in lookup:\n            print(x)",
    "false_positive_built_before_loop": "def f(arr, lookup_source):\n    lookup = set(lookup_source)\n    for x in arr:\n        if x in lookup:\n            print(x)",
}

for label, code in invariant_tests.items():
    tree = parse_source(code)
    func = find_functions(tree.root_node)[0]
    matches = detect_loop_invariant_construction(func, code)
    fired = "FIRED" if matches else "silent"
    print(f"  {label:35s} -> {fired}  {matches}")


print()
print("=" * 60)
print("TEST: full analyze_file pipeline on a 'worst offender' file")
print("=" * 60)

from app.parser import analyze_file
import json

worst_offender_code = """
def terrible_function(arr, targets, lookup_source):
    result = ''
    for i in arr:
        for j in arr:
            if i in targets:
                result += str(i)
    for x in range(10):
        print(x)
    lookup = set(lookup_source)
    return result

def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
"""

results = analyze_file(worst_offender_code)
for r in results:
    print(f"\n{r['name']}: {r['complexity']} (loop_depth={r['loop_depth']}, recursive={r['is_recursive']})")