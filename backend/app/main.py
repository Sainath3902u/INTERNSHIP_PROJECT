from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.evaluate import router as evaluate_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://ffe-indol.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(evaluate_router)


@app.get("/")
def home():
    return {
        "message": "Synthetic Data Benchmark Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }