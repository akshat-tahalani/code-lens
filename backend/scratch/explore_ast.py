"""
scratch/explore_ast.py

Throwaway exploration script — NOT part of the final CodeLens engine.
Goal: parse a hardcoded snippet of Python and print its AST so we can
SEE what Tree-sitter actually gives us before we write real logic on top of it.
"""

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# Step A: build the parser (same pattern as our Step 11 verification)
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# Step B: a deliberately nested piece of code — this is the kind of pattern
# CodeLens needs to eventually flag as O(n^2)
source_code = b"""
def find_duplicates(arr):
    for i in range(len(arr)):
        for j in range(len(arr)):
            if i != j and arr[i] == arr[j]:
                return True
    return False
"""
# NOTE: Tree-sitter requires bytes, not a normal str — hence the b"""..."""
# This is because Tree-sitter is a C library under the hood and operates
# on raw byte offsets, not Python's internal string representation.

# Step C: actually parse it
tree = parser.parse(source_code)
root_node = tree.root_node

# Step D: walk the tree recursively and print every node's type + position
def print_tree(node, depth=0):
    indent = "  " * depth
    # node.type          -> what kind of syntax construct this is
    # node.start_point    -> (row, column) where this node begins
    # node.end_point      -> (row, column) where this node ends
    print(f"{indent}{node.type}  [{node.start_point} -> {node.end_point}]")
    for child in node.children:
        print_tree(child, depth + 1)

print_tree(root_node)