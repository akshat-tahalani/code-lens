"""
main.py — FastAPI application entrypoint.

Owns: app initialization, route registration, CORS setup.
"""
from app.db import init_db, save_analysis
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalyzeRequest, AnalyzeResponse
from app.parser import analyze_file
from app.db import init_db, save_analysis, get_history

app = FastAPI(title="CodeLens API")
init_db()  # ensure the analysis_history table exists before the server starts handling requests

# CORS: allows the React dashboard (running in a real browser, on a
# different origin like localhost:3000) to make requests to this API.
# The VS Code extension itself isn't browser-sandboxed, so it doesn't
# strictly NEED this — but the Phase 6 dashboard will.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev-only wildcard — tighten this before any real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """
    Minimal sanity-check route.
    """
    return {"status": "CodeLens backend is running"}


@app.get("/health")
def health():
    """
    Health check endpoint — used by monitoring tools or the extension
    itself to verify the backend is reachable before sending real
    analysis requests.
    """
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """
    The core endpoint: accepts source code, runs it through the
    Phase 2/3 analysis pipeline, returns structured complexity +
    pattern findings per function.

    Wraps analyze_file in a try/except so any unexpected internal
    error returns a CONSISTENT, structured error response instead of
    a raw unstructured 500 — the extension can then reliably check
    for a 'detail' field on failure, every time.
    """
    try:
        results = analyze_file(request.source_code)
        save_analysis(results)
        return AnalyzeResponse(functions=results)
    except Exception as e:
        logger.error(f"analyze_file failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )
    

@app.get("/analyze/history")
def analyze_history(function_name: str = None):
    """
    Returns past analysis records, optionally filtered by function
    name via a query param (?function_name=foo). Powers the Phase 6
    dashboard's trend charts.
    """
    return {"history": get_history(function_name)}