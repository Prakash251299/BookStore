from fastapi import FastAPI
from .database import Base, engine
from . import models as models
from .routes import router as books_router

app = FastAPI(title="BookHub Books Service", version="0.1.0")

# create tables
Base.metadata.create_all(bind=engine)

app.include_router(books_router)


@app.get("/")
def root():
    return {"status": "Books service running"}