from fastapi import FastAPI
from .database import Base, engine
from . import models
from .routes import router as orders_router

app = FastAPI(title="BookHub Orders Service", version="0.1.0")

Base.metadata.create_all(bind=engine)

app.include_router(orders_router)


@app.get("/")
def root():
    return {"status": "Orders service running"}