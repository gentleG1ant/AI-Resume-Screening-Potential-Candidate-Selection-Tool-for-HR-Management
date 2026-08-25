from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dal.mock_repository import OracleJobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobCreateRequest(BaseModel):
    title: str
    description: str
    required_skills: str

@router.post("/", status_code=201)
async def create_job(job: JobCreateRequest):
    """
    Creates a new job posting in the database.
    """
    repo = OracleJobRepository()
    try:
        job_id = repo.save({
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills
        })
        return {"job_id": job_id, "message": "Job created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", status_code=200)
async def list_jobs():
    """
    Lists all job postings.
    """
    repo = OracleJobRepository()
    try:
        jobs = repo.list()
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
