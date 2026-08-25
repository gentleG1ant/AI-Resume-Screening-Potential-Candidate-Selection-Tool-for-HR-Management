from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import jobs, resumes, candidates, ml_governance, internal_ai

app = FastAPI(title="AI Resume Screening API", description="API for HR AI/ML Resume Screener")

# Enable CORS for React frontend (Port 5173 / 3000) and Java Gateway (Port 8080)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(candidates.router)
app.include_router(ml_governance.router)
app.include_router(internal_ai.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

