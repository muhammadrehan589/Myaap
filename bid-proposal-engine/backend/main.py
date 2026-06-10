import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes import upload, extract, retrieve, compliance, scoring, proposal

load_dotenv()

app = FastAPI(
    title="Bid & Proposal Response Engine",
    description="AI-powered RFP analysis, compliance checking, and proposal generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)

# Register routes
app.include_router(upload.router, tags=["Upload"])
app.include_router(extract.router, tags=["Extraction"])
app.include_router(retrieve.router, tags=["RAG"])
app.include_router(compliance.router, tags=["Compliance"])
app.include_router(scoring.router, tags=["Scoring"])
app.include_router(proposal.router, tags=["Proposal"])


@app.get("/")
async def root():
    return {"status": "ok", "service": "Bid & Proposal Response Engine"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
