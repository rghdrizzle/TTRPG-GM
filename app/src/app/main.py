from fastapi import FastAPI
from app.routers import routes
from fastapi.middleware.cors import CORSMiddleware
from llama_index.retrievers.bm25 import BM25Retriever



app = FastAPI()
app.include_router(routes.router)
app.include_router(routes.protected_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/") # decorator function
async def root(): # async here is for coroutine
    return {"message": "TTPRG-GM SYSTEM ONLINE"}