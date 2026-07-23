"""
scratch/benchmark.py

Measures analyze_file() response time across file sizes, to verify
we're comfortably within the sub-200ms target discussed in Step 12.

Usage (from backend/, with venv active):
    python scratch/benchmark.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parser import analyze_file


def generate_test_file(num_functions: int) -> str:
    """
    Generate a synthetic Python file with `num_functions` functions,
    each containing a mix of loops, so we can test at realistic scale.
    """
    functions = []
    for i in range(num_functions):
        functions.append(f"""
def function_{i}(arr):
    result = []
    for x in arr:
        for y in arr:
            if x != y and x == y:
                result.append(x)
    for j in range(10):
        print(j)
    return result
""")
    return "\n".join(functions)


def benchmark(label: str, code: str, runs: int = 5):
    """
    Run analyze_file() `runs` times and report average time in ms.
    Multiple runs reduce noise from one-off system hiccups.
    """
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        analyze_file(code)
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)

    avg = sum(times) / len(times)
    print(f"{label:30s} avg={avg:7.2f}ms  min={min(times):7.2f}ms  max={max(times):7.2f}ms")


if __name__ == "__main__":
    print("=" * 60)
    print("CodeLens analyze_file() Benchmark")
    print("=" * 60)

    benchmark("Small file (5 functions)", generate_test_file(5))
    benchmark("Medium file (25 functions)", generate_test_file(25))
    benchmark("Large file (100 functions)", generate_test_file(100))
    benchmark("Very large file (500 functions)", generate_test_file(500))

    print()
    print("Target: comfortably under 200ms for realistic file sizes (5-100 functions).")