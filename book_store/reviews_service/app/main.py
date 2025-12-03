from fastapi import FastAPI
from .database import Base, engine
from .routes import router

app = FastAPI(title="BookHub Reviews Service", version="1.0")

Base.metadata.create_all(bind=engine)

app.include_router(router)


@app.get("/")
def root():
    return {"status": "Reviews service running"}