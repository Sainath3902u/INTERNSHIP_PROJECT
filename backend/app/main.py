from fastapi import FastAPI
from app.database.db import db
from app.api.upload import router as upload_router
from app.api.evaluate import router as evaluate_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://ffe-indol.vercel.app/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    db.connect()

@app.on_event("shutdown")
async def shutdown():
    db.close()

app.include_router(upload_router)
app.include_router(evaluate_router)

@app.get("/")
def home():
    return {
        "message": "Synthetic Data Benchmark Backend Running"
    }

@app.get("/tables")
def get_tables():
    tables = db.execute_query("SHOW TABLES")

    return {
        "tables": tables.to_dict(orient="records")
    }

@app.get("/preview/{table_name}")
def preview(table_name: str):
    df = db.execute_query(f"SELECT * FROM {table_name} LIMIT 10")

    return {
        "data": df.to_dict(orient="records")
    }