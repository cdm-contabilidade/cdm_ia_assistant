from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def request_id(request: Request) -> str:
    return getattr(request.state, 'request_id', str(uuid4()))


def error_body(request: Request, code: str, message: str, details: list[dict] | None = None) -> dict:
    error = {'code': code, 'message': message, 'request_id': request_id(request)}
    if details:
        error['details'] = details
    return {'error': error}


def register_error_handlers(app) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {'code': 'request_error', 'message': str(exc.detail)}
        body = error_body(request, detail.get('code', 'request_error'), detail.get('message', 'Erro na requisição.'), detail.get('details'))
        return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers or {})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = [{'field': '.'.join(str(part) for part in error['loc']), 'message': error['msg']} for error in exc.errors()]
        return JSONResponse(status_code=422, content=error_body(request, 'validation_error', 'Dados inválidos.', details))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content=error_body(request, 'internal_error', 'Erro interno do servidor.'))
