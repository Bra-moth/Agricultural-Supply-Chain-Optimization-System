from fastapi import FastAPI
from .routers import clothes, outfits

app = FastAPI()
app.include_router(clothes.router)
app.include_router(outfits.router)

@app.get("/")
def read_root():
    return {"status": "Closet-to-Climate Backend"}