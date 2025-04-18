from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..core.verifier import check_scientific_name

app = FastAPI(title="Species Verifier API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/verify/{scientific_name}")
async def verify_species(scientific_name: str):
    result = check_scientific_name(scientific_name)
    return {"result": result}

@app.post("/verify-batch")
async def verify_batch(file_path: str):
    return {"status": "Under Development"}