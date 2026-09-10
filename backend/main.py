import sys
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, chat, chats
from app.core.config import get_settings
from app.core.errors import error_body, register_error_handlers
from fastapi.responses import JSONResponse


def production_dist() -> Path | None:
    roots = [Path(getattr(sys, '_MEIPASS', Path.cwd())), Path(__file__).resolve().parent.parent]
    for root in roots:
        candidate = root / 'dist'
        if candidate.is_dir():
            return candidate
    return None


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title='CDM AI Assistant', version='1.0.0')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origin_list,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.middleware('http')
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        content_length = request.headers.get('content-length')
        try:
            oversized = int(content_length or 0) > settings.max_request_bytes
        except ValueError:
            oversized = False
        if oversized:
            return JSONResponse(status_code=413, content=error_body(request, 'request_too_large', 'O corpo da requisição excede o limite permitido.'))
        return await call_next(request)

    @app.get('/health', tags=['system'])
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

    app.include_router(admin.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(chats.router)
    register_error_handlers(app)

    dist = production_dist()
    if dist:
        app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
    return app


app = create_app()
