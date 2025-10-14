from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


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


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


@app.post("/retros", response_model=Retro, status_code=201)
def create_retro(request: CreateRetroRequest):
    global _RETRO_ID_COUNTER
    _RETRO_ID_COUNTER += 1

    # Валидация: дата не может быть из будущего
    if request.session_date > date.today():
        raise ApiError(
            code="validation_error",
            message="Session date cannot be in the future",
            status=422,
        )

    new_retro = Retro(
        id=_RETRO_ID_COUNTER,
        session_date=request.session_date,
        items=request.items,
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
    raise ApiError(
        code="not_found", message=f"Retro with id={retro_id} not found", status=404
    )


@app.put("/retros/{retro_id}", response_model=Retro)
def update_retro(retro_id: int, request: CreateRetroRequest):
    for i, retro in enumerate(_RETROS_DB):
        if retro.id == retro_id:
            if request.session_date > date.today():
                raise ApiError(
                    code="validation_error",
                    message="Session date cannot be in the future",
                    status=422,
                )

            updated_retro = Retro(
                id=retro_id,
                session_date=request.session_date,
                items=request.items,
            )
            _RETROS_DB[i] = updated_retro
            return updated_retro

    raise ApiError(
        code="not_found", message=f"Retro with id={retro_id} not found", status=404
    )


@app.delete("/retros/{retro_id}", status_code=204)
def delete_retro(retro_id: int):
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
        raise ApiError(
            code="not_found", message=f"Retro with id={retro_id} not found", status=404
        )
