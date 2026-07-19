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


def _find_known_set_vars(func_node, source_bytes) -> set:
    """
    Heuristic: scan the function for assignments like `x = set(...)` or
    `x = {...}` (set literal), and return the names of variables assigned
    that way. Used to suppress false-positive 'in' checks on real sets.

    NOT exhaustive — misses sets passed in as parameters, sets built via
    other means (e.g. set comprehension assigned through a helper), or
    variables later reassigned to a different type. This is a heuristic,
    not a type-checker.
    """
    known_sets = set()
    for node in walk(func_node):
        if node.type != "assignment":
            continue
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")
        if left is None or right is None:
            continue

        is_set_call = (
            right.type == "call"
            and right.child_by_field_name("function") is not None
            and source_bytes[
                right.child_by_field_name("function").start_byte:
                right.child_by_field_name("function").end_byte
            ].decode("utf-8") == "set"
        )
        is_set_literal = right.type == "set"  # e.g. {1, 2, 3}

        if is_set_call or is_set_literal:
            var_name = source_bytes[left.start_byte:left.end_byte].decode("utf-8")
            known_sets.add(var_name)

    return known_sets


def detect_linear_scan_in_loop(func_node, source_code: str) -> list[dict]:
    """
    Rule 2: flags 'x in some_list' or 'some_list.index(x)' used INSIDE
    a loop body. Suppresses the check when the right-hand side of 'in'
    is a variable we heuristically know was assigned via set(...) or a
    set literal (see _find_known_set_vars) — those checks are already
    O(1) and not a bug.
    """
    source_bytes = source_code.encode("utf-8")
    matches = []
    known_sets = _find_known_set_vars(func_node, source_bytes)

    for loop_node in walk(func_node):
        if loop_node.type not in LOOP_TYPES:
            continue
        body = loop_node.child_by_field_name("body")
        if body is None:
            continue

        for node in walk(body):
            if node.type == "comparison_operator":
                op_tokens = [c.type for c in node.children]
                if "in" in op_tokens:
                    # the operand AFTER the 'in' token is what's being
                    # scanned — find it by position, not by field name,
                    # since comparison_operator doesn't expose named fields
                    in_index = op_tokens.index("in")
                    if in_index + 1 < len(node.children):
                        rhs_node = node.children[in_index + 1]
                        rhs_text = source_bytes[rhs_node.start_byte:rhs_node.end_byte].decode("utf-8")
                        if rhs_text in known_sets:
                            continue  # heuristically confirmed O(1), skip
                    matches.append({
                        "line": node.start_point[0] + 1,
                        "detail": "'in' membership check inside a loop — O(n) per check on a list",
                    })

            if node.type == "call":
                func_part = node.child_by_field_name("function")
                if func_part is not None and func_part.type == "attribute":
                    attr_text = source_bytes[func_part.start_byte:func_part.end_byte].decode("utf-8")
                    if attr_text.endswith(".index"):
                        matches.append({
                            "line": node.start_point[0] + 1,
                            "detail": f"'{attr_text}()' call inside a loop — O(n) per call on a list",
                        })
    return matches

PATTERNS.append(Pattern(
    name="linear_scan_in_loop",
    category="data_structure_misuse",
    description="A membership check ('in') or .index() call on a list happens inside a loop. Each check is O(n), so the whole loop becomes O(n^2). Consider converting the list to a set/dict for O(1) lookups.",
    complexity_impact="O(n) -> O(n^2)",
    detector=detect_linear_scan_in_loop,
))


def detect_repeated_call_in_while_condition(func_node, source_code: str) -> list[dict]:
    """
    Rule 3: flags a function CALL inside a while-loop's condition.

    The condition is re-evaluated every iteration, so any call inside it
    is re-executed every time too. If that call is expensive (not a cheap
    O(1) builtin like len()), hoisting it out before the loop and storing
    the result in a variable saves real work.

    NOTE: this deliberately flags len() too, even though len() is O(1) on
    lists — we can't distinguish "cheap call" from "expensive call" by
    syntax alone, so we flag all calls and let the human judge, same as
    Phase 2's honest-uncertainty approach.
    """
    matches = []

    for node in walk(func_node):
        if node.type != "while_statement":
            continue
        condition = node.child_by_field_name("condition")
        if condition is None:
            continue

        for inner in walk(condition):
            if inner.type == "call":
                matches.append({
                    "line": node.start_point[0] + 1,
                    "detail": "Function call inside while-condition — re-evaluated every iteration; hoist out if expensive",
                })

    return matches


PATTERNS.append(Pattern(
    name="repeated_call_in_while_condition",
    category="redundant_computation",
    description="A function call appears inside a while-loop's condition, meaning it re-executes every iteration. If the call is expensive, computing it once before the loop saves repeated work.",
    complexity_impact="context-dependent — flags redundant work, not necessarily a complexity CLASS change",
    detector=detect_repeated_call_in_while_condition,
))


def detect_constant_bound_loops(func_node, source_code: str) -> list[dict]:
    """
    Rule 4: flags for-loops of the form `for x in range(<int literal>):`
    — these are CONSTANT time, not O(n), since the bound never depends
    on input size. This corrects Phase 2's blind spot where depth-
    counting couldn't distinguish range(10) from range(len(arr)).
    """
    source_bytes = source_code.encode("utf-8")
    matches = []

    for node in walk(func_node):
        if node.type != "for_statement":
            continue
        iterable = node.child_by_field_name("right")
        if iterable is None or iterable.type != "call":
            continue

        callee = iterable.child_by_field_name("function")
        if callee is None:
            continue
        callee_name = source_bytes[callee.start_byte:callee.end_byte].decode("utf-8")
        if callee_name != "range":
            continue

        # inspect range()'s arguments — flag ONLY if every argument
        # is a plain integer literal (no variables, no expressions)
        args_node = iterable.child_by_field_name("arguments")
        if args_node is None:
            continue

        arg_nodes = [c for c in args_node.children if c.type not in ("(", ")", ",")]
        if arg_nodes and all(a.type == "integer" for a in arg_nodes):
            matches.append({
                "line": node.start_point[0] + 1,
                "detail": "Loop bound is a fixed integer literal — this is O(1), not O(n), regardless of input size",
            })

    return matches


PATTERNS.append(Pattern(
    name="constant_bound_loop",
    category="complexity_correction",
    description="A for-loop's range() bound is a literal integer, meaning the loop always runs a fixed number of times — it does not scale with input and should be treated as O(1), not counted toward O(n).",
    complexity_impact="corrects loop_depth contribution to O(1) for this specific loop",
    detector=detect_constant_bound_loops,
))


def detect_exponential_recursion(func_node, source_code: str) -> list[dict]:
    """
    Rule 5: flags recursive functions that call themselves 2+ times
    per invocation (like naive fib(n-1)+fib(n-2)) with no visible
    memoization — classic exponential blowup pattern.
    """
    from app.parser import get_function_signature

    source_bytes = source_code.encode("utf-8")
    func_name, _ = get_function_signature(func_node, source_code)

    self_call_count = 0
    for n in walk(func_node):
        if n.type == "call":
            callee = n.child_by_field_name("function")
            if callee is None:
                continue
            callee_name = source_bytes[callee.start_byte:callee.end_byte].decode("utf-8")
            if callee_name == func_name:
                self_call_count += 1

    matches = []
    if self_call_count >= 2:
        matches.append({
            "line": func_node.start_point[0] + 1,
            "detail": f"Function calls itself {self_call_count} times per invocation — likely exponential O(2^n) without memoization",
        })
    return matches


PATTERNS.append(Pattern(
    name="exponential_recursion",
    category="recursion",
    description="Function makes 2+ recursive self-calls per invocation with no visible memoization — classic exponential blowup (e.g. naive Fibonacci).",
    complexity_impact="O(n) assumption -> O(2^n) likely",
    detector=detect_exponential_recursion,
))

def detect_string_concat_in_loop(func_node, source_code: str) -> list[dict]:
    """
    Rule 6: flags `s += x` (augmented assignment) inside a loop where
    the target was initialized as a string literal — each += creates
    a new string copy, making repeated concatenation O(n^2).
    """
    source_bytes = source_code.encode("utf-8")

    # heuristic: find vars initialized as string literals (e.g. s = "")
    string_vars = set()
    for n in walk(func_node):
        if n.type == "assignment":
            left = n.child_by_field_name("left")
            right = n.child_by_field_name("right")
            if left and right and right.type == "string":
                var_name = source_bytes[left.start_byte:left.end_byte].decode("utf-8")
                string_vars.add(var_name)

    matches = []
    for loop_node in walk(func_node):
        if loop_node.type not in LOOP_TYPES:
            continue
        body = loop_node.child_by_field_name("body")
        if body is None:
            continue
        for n in walk(body):
            if n.type == "augmented_assignment":
                left = n.child_by_field_name("left")
                if left is None:
                    continue
                var_name = source_bytes[left.start_byte:left.end_byte].decode("utf-8")
                if var_name in string_vars:
                    matches.append({
                        "line": n.start_point[0] + 1,
                        "detail": f"'{var_name} += ...' inside a loop — string concatenation is O(n) per call, O(n^2) total. Consider list.append() + ''.join() instead.",
                    })
    return matches


PATTERNS.append(Pattern(
    name="string_concat_in_loop",
    category="data_structure_misuse",
    description="Repeated string concatenation (+=) inside a loop creates a new string copy each time due to string immutability — O(n) per iteration, O(n^2) total. Use list.append() + ''.join() instead.",
    complexity_impact="O(n) -> O(n^2)",
    detector=detect_string_concat_in_loop,
))


COMPREHENSION_TYPES = {"list_comprehension", "set_comprehension", "dictionary_comprehension"}


def detect_nested_comprehension(func_node, source_code: str) -> list[dict]:
    """
    Rule 7: flags a comprehension with 2+ 'for' clauses — e.g.
    [x for row in matrix for x in row] — this is nested iteration
    compressed into one line, easy to miss visually.
    """
    matches = []
    for node in walk(func_node):
        if node.type in COMPREHENSION_TYPES:
            for_clauses = [c for c in node.children if c.type == "for_in_clause"]
            if len(for_clauses) >= 2:
                matches.append({
                    "line": node.start_point[0] + 1,
                    "detail": f"Comprehension has {len(for_clauses)} 'for' clauses — equivalent to nested loops, O(n^{len(for_clauses)})",
                })
    return matches


PATTERNS.append(Pattern(
    name="nested_comprehension",
    category="nesting",
    description="A comprehension contains multiple 'for' clauses, which is equivalent to nested loops but easy to miss visually since it's a single line.",
    complexity_impact="O(n) -> O(n^k) where k = number of for-clauses",
    detector=detect_nested_comprehension,
))

COMPREHENSION_TYPES = {"list_comprehension", "set_comprehension", "dictionary_comprehension"}


def detect_nested_comprehension(func_node, source_code: str) -> list[dict]:
    """
    Rule 7: flags a comprehension with 2+ 'for' clauses — e.g.
    [x for row in matrix for x in row] — this is nested iteration
    compressed into one line, easy to miss visually.
    """
    matches = []
    for node in walk(func_node):
        if node.type in COMPREHENSION_TYPES:
            for_clauses = [c for c in node.children if c.type == "for_in_clause"]
            if len(for_clauses) >= 2:
                matches.append({
                    "line": node.start_point[0] + 1,
                    "detail": f"Comprehension has {len(for_clauses)} 'for' clauses — equivalent to nested loops, O(n^{len(for_clauses)})",
                })
    return matches


PATTERNS.append(Pattern(
    name="nested_comprehension",
    category="nesting",
    description="A comprehension contains multiple 'for' clauses, which is equivalent to nested loops but easy to miss visually since it's a single line.",
    complexity_impact="O(n) -> O(n^k) where k = number of for-clauses",
    detector=detect_nested_comprehension,
))

def detect_sort_in_loop(func_node, source_code: str) -> list[dict]:
    """
    Rule 8: flags sorted()/.sort() calls inside a loop body — sorting
    is O(n log n) each call, so repeating it every iteration turns an
    otherwise-linear loop into O(n^2 log n).
    """
    source_bytes = source_code.encode("utf-8")
    matches = []

    for loop_node in walk(func_node):
        if loop_node.type not in LOOP_TYPES:
            continue
        body = loop_node.child_by_field_name("body")
        if body is None:
            continue
        for n in walk(body):
            if n.type != "call":
                continue
            callee = n.child_by_field_name("function")
            if callee is None:
                continue
            callee_text = source_bytes[callee.start_byte:callee.end_byte].decode("utf-8")
            if callee_text == "sorted" or callee_text.endswith(".sort"):
                matches.append({
                    "line": n.start_point[0] + 1,
                    "detail": f"'{callee_text}()' called inside a loop — O(n log n) per call, consider sorting once before the loop or using a heap",
                })
    return matches


PATTERNS.append(Pattern(
    name="sort_in_loop",
    category="redundant_computation",
    description="sorted()/.sort() is called inside a loop, repeating O(n log n) work every iteration. Sort once beforehand, or use a heap (heapq) if you need repeated min/max extraction.",
    complexity_impact="O(n log n) -> O(n^2 log n)",
    detector=detect_sort_in_loop,
))

def detect_front_list_ops_in_loop(func_node, source_code: str) -> list[dict]:
    """
    Rule 9: flags list.insert(0, x) or list.pop(0) inside a loop —
    both are O(n) per call (everything after index 0 must shift),
    turning an otherwise-linear loop into O(n^2). Fix: use
    collections.deque, which does front ops in O(1).
    """
    source_bytes = source_code.encode("utf-8")
    matches = []

    for loop_node in walk(func_node):
        if loop_node.type not in LOOP_TYPES:
            continue
        body = loop_node.child_by_field_name("body")
        if body is None:
            continue
        for n in walk(body):
            if n.type != "call":
                continue
            callee = n.child_by_field_name("function")
            if callee is None or callee.type != "attribute":
                continue
            callee_text = source_bytes[callee.start_byte:callee.end_byte].decode("utf-8")

            if callee_text.endswith(".insert"):
                args_node = n.child_by_field_name("arguments")
                arg_nodes = [c for c in args_node.children if c.type not in ("(", ")", ",")] if args_node else []
                if arg_nodes and arg_nodes[0].type == "integer":
                    first_arg_text = source_bytes[arg_nodes[0].start_byte:arg_nodes[0].end_byte].decode("utf-8")
                    if first_arg_text == "0":
                        matches.append({
                            "line": n.start_point[0] + 1,
                            "detail": f"'{callee_text}(0, ...)' inside a loop — O(n) per call due to shifting. Use collections.deque for O(1) front insertion.",
                        })

            if callee_text.endswith(".pop"):
                args_node = n.child_by_field_name("arguments")
                arg_nodes = [c for c in args_node.children if c.type not in ("(", ")", ",")] if args_node else []
                if arg_nodes and arg_nodes[0].type == "integer":
                    first_arg_text = source_bytes[arg_nodes[0].start_byte:arg_nodes[0].end_byte].decode("utf-8")
                    if first_arg_text == "0":
                        matches.append({
                            "line": n.start_point[0] + 1,
                            "detail": f"'{callee_text}(0)' inside a loop — O(n) per call due to shifting. Use collections.deque for O(1) front removal.",
                        })
    return matches


PATTERNS.append(Pattern(
    name="front_list_ops_in_loop",
    category="data_structure_misuse",
    description="list.insert(0, x) or list.pop(0) called inside a loop — both are O(n) due to shifting all other elements. Use collections.deque for O(1) front operations.",
    complexity_impact="O(n) -> O(n^2)",
    detector=detect_front_list_ops_in_loop,
))

def detect_loop_invariant_construction(func_node, source_code: str) -> list[dict]:
    """
    Rule 10: flags dict(...)/set(...) construction inside a loop where
    the argument is a plain identifier (not the loop variable itself) —
    a strong signal the same structure is being rebuilt every iteration
    instead of once beforehand.
    """
    source_bytes = source_code.encode("utf-8")
    matches = []

    for loop_node in walk(func_node):
        if loop_node.type not in LOOP_TYPES:
            continue

        # collect the loop variable's name (for-loops only) so we can
        # exclude the legitimate case of building something FROM it
        loop_var = None
        if loop_node.type == "for_statement":
            left = loop_node.child_by_field_name("left")
            if left is not None:
                loop_var = source_bytes[left.start_byte:left.end_byte].decode("utf-8")

        body = loop_node.child_by_field_name("body")
        if body is None:
            continue

        for n in walk(body):
            if n.type != "call":
                continue
            callee = n.child_by_field_name("function")
            if callee is None:
                continue
            callee_text = source_bytes[callee.start_byte:callee.end_byte].decode("utf-8")
            if callee_text not in ("dict", "set"):
                continue

            args_node = n.child_by_field_name("arguments")
            arg_nodes = [c for c in args_node.children if c.type not in ("(", ")", ",")] if args_node else []
            if len(arg_nodes) == 1 and arg_nodes[0].type == "identifier":
                arg_text = source_bytes[arg_nodes[0].start_byte:arg_nodes[0].end_byte].decode("utf-8")
                if arg_text != loop_var:
                    matches.append({
                        "line": n.start_point[0] + 1,
                        "detail": f"'{callee_text}({arg_text})' built inside a loop from a variable unrelated to the loop var — likely rebuildable once BEFORE the loop",
                    })
    return matches


PATTERNS.append(Pattern(
    name="loop_invariant_construction",
    category="redundant_computation",
    description="A dict()/set() is constructed inside a loop from data that doesn't depend on the loop variable — it's likely identical every iteration and can be built once before the loop instead.",
    complexity_impact="context-dependent — flags redundant work, not necessarily a complexity CLASS change",
    detector=detect_loop_invariant_construction,
))


def run_all_patterns(func_node, source_code: str) -> list[dict]:
    """
    The rule runner: checks a function against EVERY registered pattern
    in PATTERNS, and returns a flat list of findings.

    This is what analyze_file (Phase 2) will call, merging structural
    heuristics with named pattern findings into one report.
    """
    findings = []
    for pattern in PATTERNS:
        matches = pattern.detector(func_node, source_code)
        for match in matches:
            findings.append({
                "pattern_name": pattern.name,
                "category": pattern.category,
                "description": pattern.description,
                "complexity_impact": pattern.complexity_impact,
                "line": match["line"],
                "detail": match["detail"],
            })
    return findings