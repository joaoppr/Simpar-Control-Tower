from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import ROOT, settings
from .routers import (company, connections, copilot, executive, governance, inventory, meta, opportunities,
                      showback)

app = FastAPI(title="Simpar FinOps Control Tower", version="1.0.0",
              description="API de FinOps multi-cloud do Grupo Simpar (modo demonstração com dados fictícios).")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_methods=["*"], allow_headers=["*"])

for r in (meta, executive, company, showback, opportunities, governance, inventory, copilot, connections):
    app.include_router(r.router)

# Em producao local (um unico processo) o FastAPI serve o frontend compilado.
DIST = ROOT / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = DIST / path
        return FileResponse(f if f.is_file() else DIST / "index.html")
