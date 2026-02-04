from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import companies, filings, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Stock Analysis API",
    description="SEC 10-K analyzer for S&P 100 companies",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router)
app.include_router(filings.router)
app.include_router(jobs.router)


@app.get("/")
async def root():
    return {"message": "Stock Analysis API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
