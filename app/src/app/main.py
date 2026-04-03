from fastapi import FastAPI
from .routers import routes

app = FastAPI()
app.include_router(routes.router)

@app.get("/") # decorator function
async def root(): # async here is for coroutine
    return {"message": "Hello World"}