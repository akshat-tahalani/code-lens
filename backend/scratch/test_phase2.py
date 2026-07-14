"""
scratch/test_phase2.py

Run this directly to verify all Phase 2 functions work as expected.
Usage (from backend/, with venv active):
    python scratch/test_phase2.py
"""

import sys
import os

# Fix: running a script directly only adds the SCRIPT's own folder
# (scratch/) to sys.path, not backend/ — so `app` can't be found.
# We explicitly add the parent folder (backend/) here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parser import (
    parse_source,
    find_functions,
    get_function_signature,
    find_loops,
    max_loop_depth,
    is_recursive,
    estimate_complexity,
    analyze_file,
)

print("=" * 60)
print("TEST: find_functions + get_function_signature")
print("=" * 60)
code = """
def foo():
    pass

def bar():
    pass
"""
tree = parse_source(code)
funcs = find_functions(tree.root_node)
print(f"{len(funcs)} functions found")
for f in funcs:
    name, params = get_function_signature(f, code)
    print(f"  name={name}  params={params}")

print()
print("=" * 60)
print("TEST: max_loop_depth")
print("=" * 60)
depth_tests = {
    "no_loop": "def f():\n    return 1",
    "single": "def f():\n    for i in range(10):\n        print(i)",
    "nested_double": "def f():\n    for i in range(10):\n        for j in range(10):\n            print(i, j)",
    "nested_triple": "def f():\n    for i in range(10):\n        for j in range(10):\n            for k in range(10):\n                print(i, j, k)",
}
for label, c in depth_tests.items():
    t = parse_source(c)
    func = find_functions(t.root_node)[0]
    print(f"  {label:15s} depth={max_loop_depth(func)}")

print()
print("=" * 60)
print("TEST: is_recursive")
print("=" * 60)
recursion_tests = {
    "not_recursive": "def f(n):\n    return n + 1",
    "factorial_recursive": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
}
for label, c in recursion_tests.items():
    t = parse_source(c)
    func = find_functions(t.root_node)[0]
    print(f"  {label:20s} recursive={is_recursive(func, c)}")

print()
print("=" * 60)
print("TEST: estimate_complexity (5 known-complexity functions)")
print("=" * 60)
complexity_tests = {
    "constant": "def f(a, b):\n    return a + b",
    "linear": "def f(arr):\n    for x in arr:\n        print(x)",
    "quadratic": "def f(arr):\n    for i in arr:\n        for j in arr:\n            print(i, j)",
    "cubic": "def f(arr):\n    for i in arr:\n        for j in arr:\n            for k in arr:\n                print(i, j, k)",
    "factorial_recursive": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
}
for label, c in complexity_tests.items():
    t = parse_source(c)
    func = find_functions(t.root_node)[0]
    name, _ = get_function_signature(func, c)
    result = estimate_complexity(func, c)
    print(f"  {label:20s} ({name}) -> {result}")

print()
print("All Phase 2 tests ran without error.")

print()
print("=" * 60)
print("TEST: analyze_file (full pipeline, multi-function file)")
print("=" * 60)
multi_func_code = """
def constant_lookup(d, key):
    return d[key]

def linear_search(arr, target):
    for x in arr:
        if x == target:
            return True
    return False

def has_duplicate_pair(arr):
    for i in arr:
        for j in arr:
            if i != j and i == j:
                return True
    return False

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def outer_with_helper(arr):
    def helper(x):
        return x * 2
    return [helper(x) for x in arr]
"""

results = analyze_file(multi_func_code)
print(f"{len(results)} top-level functions found (expect 5 — helper should be excluded)")
print()
for r in results:
    print(f"  {r['name']:20s} lines {r['start_line']}-{r['end_line']:<4} "
          f"depth={r['loop_depth']}  recursive={r['is_recursive']!s:5s}  {r['complexity']}")