from datetime import date
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


class RetroItem(BaseModel):
    what_went_well: str = Field(description="Что прошло хорошо")
    to_improve: str = Field(description="Что можно улучшить")
    actions: str = Field(description="Конкретные действия на следующий спринт")


class Retro(BaseModel):
    id: int
    session_date: date
    items: List[RetroItem]


class CreateRetroRequest(BaseModel):
    session_date: date
    items: List[RetroItem]


app = FastAPI(title="SecDev Course App", version="0.1.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["http://localhost"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_RETROS_DB: List[Retro] = []
_RETRO_ID_COUNTER = 0


class ProblemDetailException(Exception):
    """Кастомное исключение для генерации ошибок в формате RFC 7807."""

    def __init__(
        self, status: int, title: str, detail: str, type_: str = "about:blank"
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type_ = type_


@app.exception_handler(ProblemDetailException)
async def problem_detail_exception_handler(
    request: Request, exc: ProblemDetailException
):
    correlation_id = str(uuid4())
    return JSONResponse(
        status_code=exc.status,
        content={
            "type": exc.type_,
            "title": exc.title,
            "status": exc.status,
            "detail": exc.detail,
            "correlation_id": correlation_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler_rfc7807(request: Request, exc: HTTPException):
    correlation_id = str(uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": "HTTP Exception",
            "status": exc.status_code,
            "detail": exc.detail,
            "correlation_id": correlation_id,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ProblemDetailException(
            title="validation_error", detail="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ProblemDetailException(title="not_found", detail="item not found", status=404)


@limiter.limit("20/minute")
@app.post("/retros", response_model=Retro, status_code=201)
def create_retro(request_body: CreateRetroRequest, request: Request):
    # global _RETROS_ID_COUNTER
    # _RETROS_ID_COUNTER += 1

    if request_body.session_date > date.today():
        raise ProblemDetailException(
            status=422,
            title="Validation Error",
            detail="Session date cannot be in the future",
        )

    new_retro = Retro(
        id=len(_RETROS_DB) + 1,
        session_date=request_body.session_date,
        items=request_body.items,
    )
    _RETROS_DB.append(new_retro)
    return new_retro


@app.get("/retros", response_model=List[Retro])
def get_all_retros(from_date: Optional[date] = None, to_date: Optional[date] = None):
    filtered_retros = _RETROS_DB

    if from_date:
        filtered_retros = [r for r in filtered_retros if r.session_date >= from_date]

    if to_date:
        filtered_retros = [r for r in filtered_retros if r.session_date <= to_date]

    return filtered_retros


@app.get("/retros/{retro_id}", response_model=Retro)
def get_retro_by_id(retro_id: int):
    for retro in _RETROS_DB:
        if retro.id == retro_id:
            return retro
    raise ProblemDetailException(
        title="not_found", detail=f"Retro with id={retro_id} not found", status=404
    )


@limiter.limit("20/minute")
@app.put("/retros/{retro_id}", response_model=Retro)
def update_retro(retro_id: int, request_body: CreateRetroRequest, request: Request):
    global _RETROS_DB
    for i, retro in enumerate(_RETROS_DB):
        if retro.id == retro_id:
            if request_body.session_date > date.today():
                raise ProblemDetailException(
                    title="validation_error",
                    detail="Session date cannot be in the future",
                    status=422,
                )

            updated_retro = Retro(
                id=retro_id,
                session_date=request_body.session_date,
                items=request_body.items,
            )
            _RETROS_DB[i] = updated_retro
            return updated_retro

    raise ProblemDetailException(
        title="not_found", detail=f"Retro with id={retro_id} not found", status=404
    )


@limiter.limit("20/minute")
@app.delete("/retros/{retro_id}", status_code=204)
def delete_retro(retro_id: int, request: Request):
    global _RETROS_DB

    retro_to_delete = None
    for retro in _RETROS_DB:
        if retro.id == retro_id:
            retro_to_delete = retro
            break

    if retro_to_delete:
        _RETROS_DB.remove(retro_to_delete)
        return
    else:
        raise ProblemDetailException(
            title="not_found", detail=f"Retro with id={retro_id} not found", status=404
        )
