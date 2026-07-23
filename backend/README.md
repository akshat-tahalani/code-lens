# CodeLens Backend

FastAPI service that parses Python source code via Tree-sitter, detects
algorithmic complexity and anti-patterns, and persists analysis history.

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

## Running

```bash
python -m uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`. Interactive API docs at
`http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /` — sanity check
- `GET /health` — health check
- `POST /analyze` — accepts `{"source_code": "..."}`, returns per-function
  complexity + anti-pattern findings
- `GET /analyze/history` — past analysis records (optional `?function_name=`
  filter)

## Performance

Benchmarked via `scratch/benchmark.py`: sub-200ms response time confirmed
for files up to ~100 functions (95ms average). Very large files (500+
functions) exceed this threshold (~535ms) — a known, deliberate scope
boundary, since a single file with 500 functions already indicates a
codebase organization issue beyond what a complexity analyzer should
need to optimize around.

## Known Limitations

- Complexity heuristics are structural, not a full type-checker — e.g.
  `x in some_set` cannot always be distinguished from `x in some_list`
  when the set is passed as a function parameter rather than assigned
  locally.
- Malformed/mid-typing code is handled gracefully via Tree-sitter's
  error recovery, but may under-report complexity on the broken portion
  of the code rather than guessing.