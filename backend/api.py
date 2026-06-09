import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TABLES = {"demo_requests", "signups"}

db = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/leads")
def get_leads(table: str = "demo_requests"):
    if table not in TABLES:
        raise HTTPException(400, f"Unknown table: {table}")
    result = db.table(table).select("*").order("created_at", desc=True).execute()
    return result.data


@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: str, table: str = "demo_requests"):
    if table not in TABLES:
        raise HTTPException(400, f"Unknown table: {table}")
    result = db.table(table).select("*").eq("id", lead_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(404, "Lead not found")
    return result.data


# Serve built React frontend (production mode)
_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        f = _dist / full_path
        if f.exists() and f.is_file():
            return FileResponse(f)
        return FileResponse(_dist / "index.html")
