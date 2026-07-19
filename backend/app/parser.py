"""
parser.py — Tree-sitter wrapper.

Owns: building the Parser once, and exposing a clean parse_source()
function that the rest of the app (patterns.py, main.py) calls without
ever touching Tree-sitter's raw API directly.
"""

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Tree


# Built ONCE at import time, not per-call — Language/Parser construction
# has overhead we don't want to pay on every single analysis request.
PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


def parse_source(source_code: str) -> Tree:
    """
    Parse a string of Python source code into a Tree-sitter AST.
    """
    source_bytes = source_code.encode("utf-8")
    tree = _parser.parse(source_bytes)
    return tree


def walk(node):
    """
    Generator that yields every node in the tree, depth-first,
    starting from `node` itself.
    """
    yield node
    for child in node.children:
        yield from walk(child)


def find_functions(root_node):
    """
    Return every function_definition node in the tree.
    """
    return [n for n in walk(root_node) if n.type == "function_definition"]


def get_function_signature(func_node, source_code: str):
    """
    Extract (name, params) from a function_definition node.
    """
    name_node = func_node.child_by_field_name("name")
    params_node = func_node.child_by_field_name("parameters")

    source_bytes = source_code.encode("utf-8")
    name = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
    params = source_bytes[params_node.start_byte:params_node.end_byte].decode("utf-8")

    return name, params


LOOP_TYPES = {"for_statement", "while_statement"}


def find_loops(node):
    """
    Return every loop node (for OR while) within the given subtree.
    """
    return [n for n in walk(node) if n.type in LOOP_TYPES]


def max_loop_depth(node, current_depth=0):
    """
    Compute the deepest loop-within-loop nesting in this subtree.
    """
    deepest = current_depth
    for child in node.children:
        if child.type in LOOP_TYPES:
            deepest = max(deepest, max_loop_depth(child, current_depth + 1))
        else:
            deepest = max(deepest, max_loop_depth(child, current_depth))
    return deepest


def is_recursive(func_node, source_code: str) -> bool:
    """
    Return True if func_node calls itself by name anywhere in its body.
    """
    func_name, _ = get_function_signature(func_node, source_code)
    source_bytes = source_code.encode("utf-8")

    for n in walk(func_node):
        if n.type == "call":
            callee_node = n.child_by_field_name("function")
            if callee_node is None:
                continue
            callee_name = source_bytes[callee_node.start_byte:callee_node.end_byte].decode("utf-8")
            if callee_name == func_name:
                return True
    return False


def estimate_complexity(func_node, source_code: str) -> str:
    """
    First-pass complexity heuristic combining loop nesting depth and
    recursion.
    """
    depth = max_loop_depth(func_node)
    recursive = is_recursive(func_node, source_code)

    if recursive and depth >= 1:
        return f"O(n^{depth} * log n) [recursive + nested loop — needs manual review]"
    if recursive:
        return "O(n) [recursive, assumed linear shrink — verify branching factor]"
    if depth == 0:
        return "O(1)"
    return f"O(n^{depth})"


def _is_top_level(func_node):
    """
    Return True if func_node is NOT nested inside another function.
    """
    parent = func_node.parent
    while parent is not None:
        if parent.type == "function_definition":
            return False
        parent = parent.parent
    return True


def analyze_file(source_code: str) -> list[dict]:
    
    """
    The orchestrator: parse source code and return a structured
    complexity report, one entry per TOP-LEVEL function.
    """
    from app.patterns import run_all_patterns
    tree = parse_source(source_code)
    all_functions = find_functions(tree.root_node)

    report = []
    for func_node in all_functions:
        if not _is_top_level(func_node):
            continue

        name, params = get_function_signature(func_node, source_code)
        report.append({
          "name": name,
            "params": params,
            "start_line": func_node.start_point[0] + 1,
            "end_line": func_node.end_point[0] + 1,
            "loop_depth": max_loop_depth(func_node),
            "is_recursive": is_recursive(func_node, source_code),
            "complexity": estimate_complexity(func_node, source_code),
            "pattern_findings": run_all_patterns(func_node, source_code),
        })
    return report