from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional
from dal.mock_repository import OracleCandidateRepository

router = APIRouter(prefix="/candidates", tags=["candidates"])

class StatusUpdateRequest(BaseModel):
    status: str  # 'New', 'Shortlisted', 'Interview', 'Rejected', 'Hired'
    recruiter_decision: Optional[str] = None

@router.patch("/{candidate_id}/status", status_code=200)
async def update_candidate_status(
    candidate_id: int = Path(...),
    payload: StatusUpdateRequest = None
):
    """
    Updates the screening status and recruiter notes for a candidate.
    """
    if not payload or not payload.status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    valid_statuses = {"New", "Shortlisted", "Interview", "Rejected", "Hired"}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
        
    candidate_repo = OracleCandidateRepository()
    updated = candidate_repo.update_status(
        candidate_id=candidate_id,
        status=payload.status,
        recruiter_decision=payload.recruiter_decision
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        
    # Phase 8: Log recruiter decision as training feedback
    try:
        from dal.mock_repository import OracleMLRepository, OracleResumeRepository, OracleScoreRepository
        ml_repo = OracleMLRepository()
        resume_repo = OracleResumeRepository()
        score_repo = OracleScoreRepository()
        
        # Find candidate's resume and match score
        resumes = [r for r in resume_repo.list() if r.get("candidate_id") == candidate_id]
        if resumes:
            rid = resumes[0]["resume_id"]
            # Look up score
            scores = score_repo.list(job_id=1) # or find by resume_id
            target_label = 1 if payload.status in {"Shortlisted", "Interview", "Hired"} else 0
            
            ml_repo.log_feedback({
                "candidate_id": candidate_id,
                "job_id": 1,
                "match_id": scores[0]["match_id"] if scores else 1,
                "skills_required_score": scores[0].get("skills_required_score", 0.7) if scores else 0.7,
                "skills_preferred_score": scores[0].get("skills_preferred_score", 0.6) if scores else 0.6,
                "experience_score": scores[0].get("experience_score", 0.8) if scores else 0.8,
                "education_score": scores[0].get("education_score", 0.8) if scores else 0.8,
                "projects_certs_score": scores[0].get("projects_certs_score", 0.75) if scores else 0.75,
                "global_context_score": scores[0].get("global_context_score", 0.65) if scores else 0.65,
                "baseline_score": scores[0].get("final_rank_score", 0.72) if scores else 0.72,
                "final_hr_decision": payload.status,
                "target_label": target_label,
                "recruiter_notes": payload.recruiter_decision or "",
                "is_synthetic": 0
            })
    except Exception as e:
        print(f"Feedback logging exception: {e}")
        
    return {
        "candidate_id": candidate_id,
        "status": payload.status,
        "recruiter_decision": payload.recruiter_decision,
        "message": "Candidate status updated successfully"
    }

@router.get("/{candidate_id}", status_code=200)
async def get_candidate(candidate_id: int = Path(...)):
    """
    Fetches candidate profile and screening history.
    """
    candidate_repo = OracleCandidateRepository()
    candidate = candidate_repo.get(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return candidate
