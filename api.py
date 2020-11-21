from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ItemQuery(BaseModel):
    user: str
    operation:str
    item: str

@app.get("/api")
async def root(query: ItemQuery):
    
    return {"message": "Hello World"}