from fastapi import FastAPI
from app.routes import router as auth_router
from .database import Base, engine
from . import models as models

app = FastAPI(title="BookHub Auth Service", version="0.1.0")

# create tables
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)