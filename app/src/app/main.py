from fastapi import FastAPI

app = FastAPI()


@app.get("/") # decorator function
async def root(): # async here is for coroutine
    return {"message": "Hello World"}