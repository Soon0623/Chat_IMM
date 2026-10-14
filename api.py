"""Local retrieval API. Set BRIDGE_API_KEY before exposing beyond localhost."""
import os
import sqlite3
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, Query

app = FastAPI(title="Student presentation retrieval")

@app.get("/search")
def search(q: str = Query(min_length=1, max_length=500), limit: int = Query(default=5, ge=1, le=20), x_api_key: str | None = Header(default=None)):
    key = os.getenv("BRIDGE_API_KEY")
    if key and x_api_key != key:
        raise HTTPException(401, "Invalid API key")
    db = Path(os.getenv("BRIDGE_DB", "data/search.db")).resolve()
    if not db.is_file():
        raise HTTPException(503, "Run the sync program first")
    terms = list(dict.fromkeys(q.strip().split()))[:20]
    if not terms:
        return {"results": []}
    # Escape wildcards; SQL arguments are always bound parameters.
    patterns = ["%" + t.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%" for t in terms]
    clauses = ["text LIKE ? ESCAPE '\\'" for _ in terms]
    score = " + ".join(f"CASE WHEN {c} THEN 1 ELSE 0 END" for c in clauses)
    sql = f"SELECT source, slide, url, text, ({score}) AS score FROM chunks WHERE {' OR '.join(clauses)} ORDER BY score DESC, id LIMIT ?"
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, patterns + patterns + [limit]).fetchall()
    return {"results": [dict(r) for r in rows]}
