"""
patterns.py — Anti-pattern detection engine.

Owns: the Pattern data structure, all individual rule detectors, and
the rule runner that checks a function against every registered rule.
"""

from dataclasses import dataclass
from typing import Callable

from app.parser import walk, LOOP_TYPES


@dataclass
class Pattern:
    """
    One named, detectable anti-pattern.

    detector is a function with signature:
        (func_node, source_code: str) -> list[dict]
    It returns a list of MATCHES (empty list = pattern not found).
    Each match dict should at minimum include a 'line' key so we can
    later point VS Code at the exact offending line.
    """
    name: str                  # e.g. "nested_loop_same_array"
    category: str              # e.g. "nesting"
    description: str           # human-readable explanation
    complexity_impact: str     # e.g. "O(n) -> O(n^2)"
    detector: Callable


# All registered rules live here. We append to this list as we build
# each rule (Rule 1 in Step 4, Rule 2 in Step 6, etc.)
PATTERNS: list[Pattern] = []



def _get_iterable_name(for_node, source_bytes):
    """
    For a for_statement node, extract the text of what's being iterated
    over (the 'right' field) — e.g. for "for i in arr:", returns "arr".
    """
    iterable_node = for_node.child_by_field_name("right")
    if iterable_node is None:
        return None
    return source_bytes[iterable_node.start_byte:iterable_node.end_byte].decode("utf-8")


def detect_nested_loop_same_array(func_node, source_code: str) -> list[dict]:
    """
    Rule 1: flags an outer for-loop containing a nested for-loop that
    iterates over the SAME variable/expression.

    Classic pattern: for i in arr: for j in arr: ... (compare all pairs)
    """
    source_bytes = source_code.encode("utf-8")
    matches = []

    for node in walk(func_node):
        if node.type != "for_statement":
            continue
        outer_iterable = _get_iterable_name(node, source_bytes)
        if outer_iterable is None:
            continue

        # look for a NESTED for_statement inside this one's body
        body = node.child_by_field_name("body")
        if body is None:
            continue

        for inner in walk(body):
            if inner.type == "for_statement" and inner is not node:
                inner_iterable = _get_iterable_name(inner, source_bytes)
                if inner_iterable == outer_iterable:
                    matches.append({
                        "line": node.start_point[0] + 1,
                        "detail": f"Nested loop both iterate over '{outer_iterable}'",
                    })
    return matches


PATTERNS.append(Pattern(
    name="nested_loop_same_array",
    category="nesting",
    description="Two nested loops iterate over the same collection — often a sign of an O(n^2) all-pairs comparison that could potentially use a set/dict for O(n).",
    complexity_impact="O(n) -> O(n^2)",
    detector=detect_nested_loop_same_array,
))