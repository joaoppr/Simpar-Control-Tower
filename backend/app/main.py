import base64
import binascii
import hmac
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from .config import ROOT, settings
from .routers import (company, connections, copilot, executive, governance, inventory, meta, opportunities,
                      showback)

app = FastAPI(title="Simpar FinOps Control Tower", version="1.0.0",
              description="API de FinOps multi-cloud do Grupo Simpar (modo demonstração com dados fictícios).")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def require_basic_auth(request: Request, call_next):
    if not settings.require_auth:
        return await call_next(request)
    if not settings.app_username or not settings.app_password:
        return PlainTextResponse("Application authentication is not configured.", status_code=503)

    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    try:
        userpass = base64.b64decode(token, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        userpass = ""
    username, separator, password = userpass.partition(":")
    valid = (
        scheme.lower() == "basic"
        and bool(separator)
        and hmac.compare_digest(username.encode("utf-8"), settings.app_username.encode("utf-8"))
        and hmac.compare_digest(password.encode("utf-8"), settings.app_password.encode("utf-8"))
    )
    if not valid:
        return PlainTextResponse(
            "Authentication required.",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Simpar Control Tower"', "Cache-Control": "no-store"},
        )
    return await call_next(request)


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
