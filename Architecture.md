# CodeLens — Architecture
 
## Overview
CodeLens is a real-time code complexity analyzer. It parses source code into
an Abstract Syntax Tree (AST) using Tree-sitter, detects algorithmic
anti-patterns (nested loops, repeated linear scans, etc.), and surfaces
Big-O complexity annotations directly in the editor, with historical trends
viewable in a dashboard.
 
## Components
 
### `backend/` (Python, FastAPI)
The analysis engine. Owns all parsing and pattern-detection logic.
- `app/parser.py` — wraps Tree-sitter: source code in, AST out.
- `app/patterns.py` — walks the AST, detects anti-patterns, maps them to
  complexity classes (O(n), O(n²), etc.).
- `app/main.py` — FastAPI routes. Accepts source code, returns JSON
  annotations.
- `app/models.py` — Pydantic schemas defining request/response shapes.
Runs as a standalone HTTP service — reusable by the extension, the
dashboard, or (in principle) a CI pipeline.
 
### `extension/` (TypeScript, VS Code Extension API)
Thin client. Watches file save events, sends source code to the backend
over HTTP, and renders returned annotations as inline decorations in the
editor margin. Contains no analysis logic itself.
 
### `dashboard/` (React)
Visualizes complexity trends over time per function/file, fetched from the
backend's history endpoints. Independent of the live-editing flow — used
for retrospective analysis.
 
## Data Flow
```
VS Code Extension --(HTTP POST: source code)--> FastAPI Backend
                                                      |
                                                      v
                                            Tree-sitter parses to AST
                                                      |
                                                      v
                                          patterns.py walks tree,
                                          detects issues + complexity
                                                      |
                                                      v
VS Code Extension <--(JSON: annotations)-------------+
                                                      |
                                                      v
                                          (also persisted for)
                                                      |
                                                      v
                                          React Dashboard (trends)
```
 
## Why this split?
Analysis logic lives in one place (`backend/`) so it can serve multiple
clients without duplication. The extension and dashboard are both "dumb"
in the sense that neither understands Python syntax or complexity theory —
they just display what the backend tells them.