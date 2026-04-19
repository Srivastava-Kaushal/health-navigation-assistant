from fastapi import FastAPI
from app.db.init_db import init_db
from app.api.routes.document import router as document_router

app = FastAPI(title="Health Navigation Assistant")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(document_router, prefix="/documents", tags=["documents"])

@app.get("/")
def root():
    return {"message": "Backend is running"}