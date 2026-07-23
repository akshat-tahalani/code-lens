"""
models.py — Pydantic schemas for request/response validation.

Owns: the shape of data going in/out of the FastAPI routes. No logic
lives here — just data contracts that main.py validates against.
"""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """
    What the extension sends us: just the raw source code as a string.
    """
    source_code: str

class PatternFinding(BaseModel):
    """
    One anti-pattern match from Phase 3's rule engine, mirroring the
    dict shape returned by run_all_patterns().
    """
    pattern_name: str
    category: str
    description: str
    complexity_impact: str
    line: int
    detail: str


class FunctionReport(BaseModel):
    """
    Complexity report for ONE top-level function, mirroring the dict
    shape returned by analyze_file() for each function.
    """
    name: str
    params: str
    start_line: int
    end_line: int
    loop_depth: int
    is_recursive: bool
    complexity: str
    pattern_findings: list[PatternFinding]


class AnalyzeResponse(BaseModel):
    """
    What we send back to the extension: a list of per-function reports.
    """
    functions: list[FunctionReport]